"""Unit tests for comparison_service: table, scoring, ranking, export."""
import os
from pathlib import Path

from app.services import comparison_service as cmp
from app.services import property_service as props


def _seed(session):
    a = props.create_property(
        session, name="Thuthikadu 171-4", location="Thuthikadu",
        area_sqft=12500, price_total=1850000, price_per_sqft=148, status="shortlisted",
    )
    b = props.create_property(
        session, name="Kotikal Forest", location="Kathalampattu",
        area_sqft=112000, price_total=3500000, price_per_sqft=31, status="evaluating",
    )
    return [a, b]


def test_alias_fields_map_to_columns(session):
    a, _ = _seed(session)
    assert a.total_area_sqft == 12500
    assert a.asking_price == 1850000


def test_build_table_columns_and_rows(session):
    properties = _seed(session)
    comparison = cmp.create_comparison(session, "Top", properties)
    table = cmp.build_table(session, cmp.properties_in(session, comparison))
    assert table["columns"] == cmp.TABLE_COLUMNS
    assert len(table["rows"]) == 2


def test_cheaper_per_sqft_scores_higher(session):
    a, b = _seed(session)  # a=148/sqft, b=31/sqft
    assert cmp.match_score(session, b) > cmp.match_score(session, a)


def test_weighted_scores_are_ranked(session):
    properties = _seed(session)
    weights = {"Location": 30, "Price": 25, "Area": 20, "Document Status": 15, "Infrastructure": 10}
    ranked = cmp.weighted_scores(session, properties, weights)
    scores = [r["score"] for r in ranked]
    assert scores == sorted(scores, reverse=True)


def test_export_pdf_is_valid_file(session, tmp_path):
    properties = _seed(session)
    comparison = cmp.create_comparison(session, "Top", properties)
    path = os.path.join(tmp_path, "out.pdf")
    cmp.export_pdf(session, comparison, path)
    data = Path(path).read_bytes()
    assert data.startswith(b"%PDF") and data.rstrip().endswith(b"%%EOF")
    assert b"Location" in data and b"Match Score" in data
