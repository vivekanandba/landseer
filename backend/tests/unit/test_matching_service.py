"""Unit tests for matching_service: scoring, deal-breakers, ranking, persistence."""

import pytest

from app.services import matching_service as matching
from app.services import property_service as props


def _seed(session):
    cheap = props.create_property(
        session,
        name="Cheap PerSqft",
        location="Thuthikadu",
        area_sqft=100000,
        price_total=3000000,
        price_per_sqft=30,
        status="evaluating",
    )
    dear = props.create_property(
        session,
        name="Dear PerSqft",
        location="Thuthikadu",
        area_sqft=10000,
        price_total=2000000,
        price_per_sqft=200,
        status="evaluating",
    )
    return cheap, dear


def test_score_property_is_bounded(session):
    cheap, _ = _seed(session)
    pref = matching.create_preference(session, name="P", budget_max=4000000)
    result = matching.score_property(session, pref, cheap)
    assert 0 <= result["score"] <= 100
    assert {b["criterion"] for b in result["breakdown"]}  # non-empty breakdown


def test_budget_deal_breaker(session):
    _seed(session)
    pricey = props.create_property(session, name="Pricey", asking_price=5000000)
    pref = matching.create_preference(session, name="Tight", budget_max=2000000)
    reasons = matching.deal_breakers(session, pref, pricey)
    assert any("budget" in r.lower() for r in reasons)


def test_required_feature_deal_breaker(session):
    prop = props.create_property(session, name="NoWater", water_source="No")
    pref = matching.create_preference(
        session, name="NeedsWater", required_features=["water_source"]
    )
    reasons = matching.deal_breakers(session, pref, prop)
    assert any("water_source" in r for r in reasons)


def test_location_deal_breaker(session):
    prop = props.create_property(session, name="Elsewhere", location="Ranipet")
    pref = matching.create_preference(session, name="LocPref", locations=["Thuthikadu"])
    assert matching.deal_breakers(session, pref, prop)


def test_recommend_ranks_qualified_first_then_score(session):
    _seed(session)
    props.create_property(session, name="Pricey", asking_price=9000000, price_per_sqft=400)
    pref = matching.create_preference(session, name="Value", budget_max=4000000)
    recs = matching.recommend(session, pref)
    # Pricey exceeds budget -> disqualified -> ranked last.
    assert recs[-1]["name"] == "Pricey" and recs[-1]["disqualified"]
    qualified = [r for r in recs if not r["disqualified"]]
    assert qualified[0]["name"] == "Cheap PerSqft"  # best price-per-sqft wins
    assert [r["score"] for r in qualified] == sorted((r["score"] for r in qualified), reverse=True)


def test_exclude_disqualified(session):
    _seed(session)
    props.create_property(session, name="Pricey", asking_price=9000000)
    pref = matching.create_preference(session, name="Value", budget_max=4000000)
    recs = matching.recommend(session, pref, include_disqualified=False)
    assert all(not r["disqualified"] for r in recs)
    assert "Pricey" not in {r["name"] for r in recs}


def test_duplicate_preference_name_raises(session):
    matching.create_preference(session, name="Dup")
    with pytest.raises(matching.DuplicatePreference):
        matching.create_preference(session, name="Dup")


def test_unknown_required_feature_rejected(session):
    with pytest.raises(matching.InvalidPreference):
        matching.create_preference(session, name="Bad", required_features=["poool"])


def test_apply_scores_persists_match_score(session):
    cheap, _ = _seed(session)
    pref = matching.create_preference(session, name="P", budget_max=4000000)
    matching.apply_scores(session, pref)
    session.refresh(cheap)
    assert cheap.match_score is not None and 0 <= cheap.match_score <= 100
