"""Smart Matching: score and rank properties against a buyer's requirements.

Scoring reuses the deterministic per-criterion scores from ``comparison_service``
so the "match score" shown in comparisons and the recommendation ranking never
disagree. Deal-breakers are hard filters (budget, size, location, must-have
features) that disqualify a property regardless of its score.
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.preference import Preference
from app.models.property import Property
from app.services import comparison_service as cmp
from app.services import property_service as props

# Feature attributes a preference may require, and how "present" is judged.
_BOOLEAN_FEATURES = {"corner_plot"}
ALLOWED_FEATURES = {"water_source", "electricity", "road_access", "corner_plot"}


class PreferenceNotFound(Exception):
    pass


class DuplicatePreference(Exception):
    pass


class InvalidPreference(Exception):
    pass


def create_preference(session: Session, **fields) -> Preference:
    name = fields.get("name")
    if name and get_preference(session, name) is not None:
        raise DuplicatePreference(f"Preference {name!r} already exists")
    unknown = set(fields.get("required_features") or []) - ALLOWED_FEATURES
    if unknown:
        raise InvalidPreference(
            f"Unknown required features {sorted(unknown)}; allowed: {sorted(ALLOWED_FEATURES)}"
        )
    pref = Preference(**fields)
    session.add(pref)
    session.flush()
    return pref


def get_preference(session: Session, name: str) -> Optional[Preference]:
    return session.scalar(select(Preference).where(Preference.name == name))


def _has_feature(prop: Property, feature: str) -> bool:
    value = getattr(prop, feature, None)
    if feature in _BOOLEAN_FEATURES:
        return bool(value)
    return str(value or "").lower() == "yes"


def score_property(session: Session, pref: Preference, prop: Property) -> dict:
    """Headline score (0-100) + per-criterion breakdown for one property."""
    weights = pref.weights or cmp.DEFAULT_WEIGHTS
    scores = cmp.criterion_scores(session, prop)
    return {
        "score": round(cmp.weighted_average(scores, weights)),
        "breakdown": cmp.match_breakdown(session, prop, weights, scores=scores),
    }


def deal_breakers(session: Session, pref: Preference, prop: Property) -> List[str]:
    """Human-readable reasons a property fails the preference's hard filters."""
    reasons: List[str] = []
    area = prop.total_area_sqft or 0

    if pref.budget_max and prop.asking_price and prop.asking_price > pref.budget_max:
        reasons.append(f"Over budget: asking {prop.asking_price:.0f} > max {pref.budget_max:.0f}")
    if pref.size_min_sqft and area < pref.size_min_sqft:
        reasons.append(f"Too small: {area:.0f} < min {pref.size_min_sqft:.0f} sqft")
    if pref.size_max_sqft and area > pref.size_max_sqft:
        reasons.append(f"Too large: {area:.0f} > max {pref.size_max_sqft:.0f} sqft")
    if pref.locations and prop.location not in pref.locations:
        reasons.append(f"Location {prop.location!r} not in preferred {pref.locations}")
    for feature in pref.required_features or []:
        if not _has_feature(prop, feature):
            reasons.append(f"Missing required feature: {feature}")
    return reasons


def recommend(
    session: Session,
    pref: Preference,
    properties: Optional[List[Property]] = None,
    include_disqualified: bool = True,
) -> List[dict]:
    """Rank properties for a preference. Qualified come first (score-desc), then
    disqualified (also score-desc) unless excluded."""
    if properties is None:
        properties = props.list_properties(session)

    results = []
    for prop in properties:
        scored = score_property(session, pref, prop)
        reasons = deal_breakers(session, pref, prop)
        results.append(
            {
                "name": prop.name,
                "score": scored["score"],
                "disqualified": bool(reasons),
                "reasons": reasons,
                "breakdown": scored["breakdown"],
            }
        )

    if not include_disqualified:
        results = [r for r in results if not r["disqualified"]]
    results.sort(key=lambda r: (r["disqualified"], -r["score"]))
    return results


def apply_scores(
    session: Session, pref: Preference, properties: Optional[List[Property]] = None
) -> List[Property]:
    """Persist each property's headline match score against this preference."""
    if properties is None:
        properties = props.list_properties(session)
    for prop in properties:
        prop.match_score = score_property(session, pref, prop)["score"]
    session.flush()
    return properties
