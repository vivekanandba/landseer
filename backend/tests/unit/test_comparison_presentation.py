"""Unit tests for comparison presentation helpers (table, features, investment)."""

from app.models.document import DocumentType
from app.services import comparison_service as cmp
from app.services import document_service as docs
from app.services import property_service as props


def _prop(session, name, **fields):
    return props.create_property(session, name=name, **fields)


def test_feature_comparison_color_mapping(session):
    prop = _prop(
        session,
        "Featured",
        water_source="yes",
        electricity="no",
        road_access="nearby",
        corner_plot=True,
    )
    fc = cmp.feature_comparison(session, [prop])["Featured"]
    assert fc["water_source"]["color"] == "green"
    assert fc["electricity"]["color"] == "red"
    assert fc["road_access"]["color"] == "yellow"
    assert fc["corner_plot"]["color"] == "green"


def test_investment_comparison_math(session):
    prop = _prop(session, "Invest", asking_price=1_000_000, estimated_appreciation_pct=10)
    inv = cmp.investment_comparison(session, [prop])["Invest"]
    assert inv["appreciation_pct"] == 10
    assert inv["projected_value_3y"] == 1_100_000
    assert inv["registration_cost"] == round(1_000_000 * cmp.REGISTRATION_RATE)
    assert inv["total_investment"] == 1_000_000 + inv["registration_cost"]


def test_build_table_structure_highlight_and_doc_icons(session):
    p1 = _prop(session, "One", location="X", total_area_sqft=1000, asking_price=500_000)
    p2 = _prop(session, "Two", location="Y", total_area_sqft=2000, asking_price=800_000)
    props.add_neighbor(session, p2, survey_number="9-1", shared_boundary=True)
    # A required-type doc that isn't verified yet -> the "in progress" icon.
    docs.upload_document(session, p1, "patta.pdf", doc_type=DocumentType.PATTA)

    table = cmp.build_table(session, [p1, p2])
    assert {r["name"] for r in table["rows"]} == {"One", "Two"}
    assert table["neighbor_highlight"] == "Two"  # more neighbors

    one = next(r for r in table["rows"] if r["name"] == "One")
    assert one["documents"]["patta"] == "⏳"  # uploaded, not verified
    assert one["documents"]["ec"] == "❌"  # missing
    assert one["neighbors"] == {"count": 0, "shared": 0}
