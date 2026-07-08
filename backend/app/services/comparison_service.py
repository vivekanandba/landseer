"""Comparison domain operations: build tables, score and rank, export.

Scoring is deterministic and derived from stored property attributes so the same
inputs always produce the same table. Presentation concerns (icons, colours) are
computed here as plain data so any UI can render them consistently.
"""
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.comparison import Comparison, ComparisonItem
from app.models.property import Property
from app.services import document_service as docs

TABLE_COLUMNS = [
    "Location",
    "Area (sqft)",
    "Total Price",
    "Price per sqft",
    "Status",
    "Match Score",
]

# Default weighting (percent) used for the headline match score.
DEFAULT_WEIGHTS = {
    "Location": 30,
    "Price": 25,
    "Size": 20,
    "Features": 15,
    "Infrastructure": 10,
}

# Tamil Nadu stamp duty + registration is ~7% of the transaction value.
REGISTRATION_RATE = 0.07


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------
def create_comparison(
    session: Session,
    name: str,
    properties: List[Property],
    notes: str = "",
) -> Comparison:
    comparison = Comparison(name=name, notes=notes)
    session.add(comparison)
    session.flush()
    for prop in properties:
        add_property(session, comparison, prop)
    return comparison


def get_comparison(session: Session, name: str) -> Optional[Comparison]:
    return session.scalar(select(Comparison).where(Comparison.name == name))


def add_property(session: Session, comparison: Comparison, prop: Property) -> None:
    existing = {item.property_id for item in comparison.items}
    if prop.id in existing:
        return
    session.add(ComparisonItem(comparison_id=comparison.id, property_id=prop.id))
    session.flush()
    session.refresh(comparison)


def add_notes(session: Session, comparison: Comparison, notes: str) -> Comparison:
    comparison.notes = notes
    session.flush()
    return comparison


def properties_in(session: Session, comparison: Comparison) -> List[Property]:
    return [session.get(Property, item.property_id) for item in comparison.items]


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------
def _price_per_sqft(prop: Property) -> float:
    if prop.price_per_sqft:
        return prop.price_per_sqft
    if prop.asking_price and prop.total_area_sqft:
        return prop.asking_price / prop.total_area_sqft
    return 150.0


def _feature_score(prop: Property) -> int:
    flags = [
        (prop.water_source or "").lower() == "yes",
        (prop.electricity or "").lower() == "yes",
        (prop.road_access or "").lower() == "yes",
        bool(prop.corner_plot),
    ]
    return round(sum(flags) / len(flags) * 100)


def _doc_score(session: Session, prop: Property) -> int:
    status = docs.checklist(session, prop)
    verified = sum(1 for s in status.values() if s == "verified")
    return round(verified / len(status) * 100) if status else 0


def criterion_scores(session: Session, prop: Property) -> Dict[str, int]:
    """Per-criterion 0-100 scores for a property."""
    location = 85 if prop.location else 40
    price = max(0, min(100, round(100 - _price_per_sqft(prop) / 3)))
    size = min(100, max(10, round((prop.total_area_sqft or 0) / 2000 * 100)))
    features = _feature_score(prop)
    doc = _doc_score(session, prop)
    return {
        "Location": location,
        "Price": price,
        "Size": size,
        "Area": size,
        "Features": features,
        "Infrastructure": features,
        "Document Status": doc,
    }


def match_score(session: Session, prop: Property, weights=DEFAULT_WEIGHTS) -> int:
    scores = criterion_scores(session, prop)
    total_weight = sum(weights.values()) or 1
    weighted = sum(scores.get(c, 0) * w for c, w in weights.items())
    return round(weighted / total_weight)


def match_breakdown(session: Session, prop: Property, weights=DEFAULT_WEIGHTS) -> List[dict]:
    scores = criterion_scores(session, prop)
    breakdown = []
    for criterion, weight in weights.items():
        score = scores.get(criterion, 0)
        strength = "strong" if score >= 80 else "weak" if score <= 60 else "moderate"
        breakdown.append(
            {"criterion": criterion, "score": score, "weight": weight, "strength": strength}
        )
    return breakdown


def weighted_scores(
    session: Session, properties: List[Property], weights: Dict[str, int]
) -> List[dict]:
    """Rank properties by a weighted blend of the supplied criteria."""
    total_weight = sum(weights.values()) or 1
    results = []
    for prop in properties:
        scores = criterion_scores(session, prop)
        weighted = sum(scores.get(c, 0) * w for c, w in weights.items())
        results.append({"name": prop.name, "score": round(weighted / total_weight, 1)})
    results.sort(key=lambda r: r["score"], reverse=True)
    return results


# ---------------------------------------------------------------------------
# Presentation helpers
# ---------------------------------------------------------------------------
def _doc_icons(session: Session, prop: Property) -> Dict[str, str]:
    icons = {}
    for doc_type in docs.REQUIRED_TYPES:
        found = docs.documents_of_type(session, prop, doc_type)
        if any(d.status.value == "verified" for d in found):
            icons[doc_type.value] = "✅"
        elif found:
            icons[doc_type.value] = "⏳"
        else:
            icons[doc_type.value] = "❌"
    return icons


def _feature_color(value: Optional[str], *, boolean=False) -> str:
    if boolean:
        return "green" if value else "red"
    v = (value or "").lower()
    if v == "yes":
        return "green"
    if v in ("no", ""):
        return "red"
    return "yellow"  # nearby / kutcha / partial


def build_table(session: Session, properties: List[Property]) -> dict:
    rows = []
    for prop in properties:
        rows.append(
            {
                "name": prop.name,
                "Location": prop.location,
                "Area (sqft)": prop.total_area_sqft,
                "Total Price": prop.asking_price,
                "Price per sqft": round(_price_per_sqft(prop)),
                "Status": prop.status.value,
                "Match Score": match_score(session, prop),
                "documents": _doc_icons(session, prop),
                "neighbors": {
                    "count": len(prop.neighbors),
                    "shared": sum(1 for n in prop.neighbors if n.shared_boundary),
                },
            }
        )
    highlight = max(rows, key=lambda r: r["neighbors"]["count"])["name"] if rows else None
    return {"columns": TABLE_COLUMNS, "rows": rows, "neighbor_highlight": highlight}


def feature_comparison(session: Session, properties: List[Property]) -> Dict[str, dict]:
    result = {}
    for prop in properties:
        result[prop.name] = {
            "water_source": {
                "value": prop.water_source,
                "color": _feature_color(prop.water_source),
            },
            "electricity": {
                "value": prop.electricity,
                "color": _feature_color(prop.electricity),
            },
            "road_access": {
                "value": prop.road_access,
                "color": _feature_color(prop.road_access),
            },
            "corner_plot": {
                "value": prop.corner_plot,
                "color": _feature_color(prop.corner_plot, boolean=True),
            },
        }
    return result


def investment_comparison(session: Session, properties: List[Property]) -> Dict[str, dict]:
    result = {}
    for prop in properties:
        price = prop.asking_price or 0.0
        appreciation = prop.estimated_appreciation_pct or 0.0
        registration = round(price * REGISTRATION_RATE)
        projected = round(price * (1 + appreciation / 100))
        result[prop.name] = {
            "appreciation_pct": appreciation,
            "projected_value_3y": projected,
            "roi_pct": appreciation,
            "rental_yield": prop.rental_yield,
            "registration_cost": registration,
            "total_investment": round(price + registration),
        }
    return result


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------
def _pdf_bytes(lines: List[str]) -> bytes:
    ops = ["BT", "/F1 10 Tf", "40 760 Td", "14 TL"]
    for i, line in enumerate(lines):
        escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        if i:
            ops.append("T*")
        ops.append(f"({escaped}) Tj")
    ops.append("ET")
    content = "\n".join(ops).encode("latin-1", "replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    out = b"%PDF-1.4\n"
    offsets = []
    for i, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
    xref_pos = len(out)
    count = len(objects) + 1
    out += b"xref\n0 %d\n" % count
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += b"%010d 00000 n \n" % off
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (count, xref_pos)
    return out


def export_pdf(session: Session, comparison: Comparison, path: str) -> str:
    """Render a comparison to a self-contained PDF file and return its path."""
    properties = properties_in(session, comparison)
    lines = [f"Landseer Property Comparison: {comparison.name}", ""]
    lines.append(" | ".join(TABLE_COLUMNS))
    for prop in properties:
        lines.append(
            " | ".join(
                str(v)
                for v in (
                    prop.location,
                    prop.total_area_sqft,
                    prop.asking_price,
                    round(_price_per_sqft(prop)),
                    prop.status.value,
                    f"{match_score(session, prop)}%",
                )
            )
        )
    lines.append("")
    lines.append("Photos:")
    for prop in properties:
        lines.append(f"Photo: {prop.name}")
    lines.append("")
    lines.append("Match Scores:")
    for prop in properties:
        lines.append(f"{prop.name}: {match_score(session, prop)}%")

    with open(path, "wb") as fh:
        fh.write(_pdf_bytes(lines))
    return path
