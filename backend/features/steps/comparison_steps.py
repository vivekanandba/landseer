"""Step definitions for property_comparison.feature."""
import os
import tempfile

from behave import given, then, when

from app.models.document import DocumentType, VerificationStatus
from app.services import comparison_service as cmp
from app.services import document_service as docs
from app.services import property_service as props

VERIFIED_ICON = "✅"
PENDING_ICON = "⏳"


def _get(context, name):
    return props.get_property_by_name(context.session, name)


def _all_properties(context):
    return props.list_properties(context.session)


def _current_properties(context):
    if "comparison" in context and context.comparison is not None:
        return cmp.properties_in(context.session, context.comparison)
    return _all_properties(context)


# ---------------------------------------------------------------------------
# Given
# ---------------------------------------------------------------------------
@given('I have a comparison "{name}" with')
def step_have_comparison_with(context, name):
    properties = [_get(context, row["name"]) for row in context.table]
    context.comparison = cmp.create_comparison(context.session, name, properties)


@given('I have a comparison "{name}"')
def step_have_comparison(context, name):
    context.comparison = cmp.create_comparison(context.session, name, _all_properties(context))


@given("I have a comparison with {count:d} properties")
def step_have_comparison_count(context, count):
    properties = _all_properties(context)[:count]
    context.comparison = cmp.create_comparison(context.session, "Working Set", properties)


@given('I create a comparison "{name}"')
def step_create_named_comparison_given(context, name):
    context.comparison = cmp.create_comparison(context.session, name, _all_properties(context))


@given("the following document statuses")
def step_document_statuses(context):
    for row in context.table:
        prop = _get(context, row["property"])
        for col in ("patta", "fmb", "ec"):
            icon = row[col]
            doc = docs.upload_document(
                context.session, prop, f"{col.upper()}.pdf", doc_type=DocumentType(col)
            )
            doc.status = (
                VerificationStatus.VERIFIED
                if icon == VERIFIED_ICON
                else VerificationStatus.UPLOADED
            )
    context.session.flush()


@given("the following property features")
def step_property_features(context):
    for row in context.table:
        prop = _get(context, row["property"])
        prop.water_source = row["water_source"]
        prop.electricity = row["electricity"]
        prop.road_access = row["road_access"]
        prop.corner_plot = row["corner_plot"].strip().lower() == "yes"
    context.session.flush()


@given("I have properties with the following details")
def step_property_details(context):
    for row in context.table:
        prop = _get(context, row["property"])
        prop.estimated_appreciation_pct = float(row["estimated_appreciation_3y"].rstrip("%"))
        prop.rental_yield = row["rental_yield"]
    context.session.flush()


@given("properties have the following neighbors")
def step_property_neighbors(context):
    for row in context.table:
        prop = _get(context, row["property"])
        count = int(row["neighbor_count"])
        shared = int(row["shared_boundaries"])
        for i in range(count):
            props.add_neighbor(
                context.session,
                prop,
                survey_number=f"{prop.name[:3]}-{i}",
                shared_boundary=i < shared,
            )
    context.session.flush()


@given('a property "{name}" has match score {score:d}%')
def step_property_match_score(context, name, score):
    prop = _get(context, name)
    prop.match_score = float(score)
    context.session.flush()
    context.current_property = prop


# ---------------------------------------------------------------------------
# When
# ---------------------------------------------------------------------------
@when("I select the following properties for comparison")
def step_select_properties(context):
    context.selected = [_get(context, row["name"]) for row in context.table]


@when('I create a comparison named "{name}"')
def step_create_named_comparison(context, name):
    context.comparison = cmp.create_comparison(context.session, name, context.selected)


@when("I view the comparison")
def step_view_comparison(context):
    context.table_view = cmp.build_table(context.session, _current_properties(context))


@when("I set the following criteria weights")
def step_set_weights(context):
    context.weights = {
        row["criterion"]: int(row["weight"].rstrip("%")) for row in context.table
    }


@when("I calculate weighted scores")
def step_calculate_weighted(context):
    context.weighted = cmp.weighted_scores(
        context.session, _current_properties(context), context.weights
    )


@when("I export the comparison to PDF")
def step_export_pdf(context):
    fd, path = tempfile.mkstemp(suffix=".pdf", prefix="landseer-comparison-")
    os.close(fd)
    context.pdf_path = cmp.export_pdf(context.session, context.comparison, path)


@when("I view feature comparison")
def step_view_features(context):
    context.features = cmp.feature_comparison(context.session, _current_properties(context))


@when("I view investment comparison")
def step_view_investment(context):
    context.investment = cmp.investment_comparison(
        context.session, _current_properties(context)
    )


@when("I save the comparison")
def step_save_comparison(context):
    context.session.flush()


@when("I add a third property to the comparison")
def step_add_third(context):
    current = {p.id for p in cmp.properties_in(context.session, context.comparison)}
    extra = next(p for p in _all_properties(context) if p.id not in current)
    cmp.add_property(context.session, context.comparison, extra)
    context.added_property = extra


@when("I click on the match score in comparison")
def step_click_match_score(context):
    context.breakdown = cmp.match_breakdown(context.session, context.current_property)


# ---------------------------------------------------------------------------
# Then
# ---------------------------------------------------------------------------
@then("the comparison should include {count:d} properties")
def step_comparison_includes(context, count):
    actual = len(cmp.properties_in(context.session, context.comparison))
    assert actual == count, f"expected {count} properties, got {actual}"


@then("the comparison should be saved")
def step_comparison_saved(context):
    assert cmp.get_comparison(context.session, context.comparison.name) is not None


@then("I should see a table with columns")
def step_table_columns(context):
    expected = [row["column"] for row in context.table]
    assert context.table_view["columns"] == expected, (
        f"columns {context.table_view['columns']} != {expected}"
    )


@then("each property should be a row in the table")
def step_property_rows(context):
    rows = context.table_view["rows"]
    expected = len(_current_properties(context))
    assert len(rows) == expected, f"expected {expected} rows, got {len(rows)}"


@then("the document status columns should show verification icons")
def step_doc_icons(context):
    for row in context.table_view["rows"]:
        assert set(row["documents"].values()) <= {"✅", "⏳", "❌"}, row["documents"]


@then('"{name}" should show "{icon}" for EC')
def step_ec_icon(context, name, icon):
    row = next(r for r in context.table_view["rows"] if r["name"] == name)
    assert row["documents"]["ec"] == icon, f"EC icon {row['documents']['ec']!r} != {icon!r}"


@then("each property should have a total weighted score")
def step_each_weighted(context):
    assert context.weighted
    for entry in context.weighted:
        assert isinstance(entry["score"], (int, float))


@then("properties should be ranked by score")
def step_ranked(context):
    scores = [e["score"] for e in context.weighted]
    assert scores == sorted(scores, reverse=True), f"not ranked: {scores}"


@then("a PDF file should be generated")
def step_pdf_generated(context):
    assert os.path.exists(context.pdf_path)
    with open(context.pdf_path, "rb") as fh:
        context.pdf_bytes = fh.read()
    assert context.pdf_bytes.startswith(b"%PDF"), "not a PDF"
    assert len(context.pdf_bytes) > 100


@then("it should contain the comparison table")
def step_pdf_table(context):
    assert b"Location" in context.pdf_bytes and b"Total Price" in context.pdf_bytes


@then("it should include property photos")
def step_pdf_photos(context):
    assert b"Photo" in context.pdf_bytes


@then("it should show match scores")
def step_pdf_scores(context):
    assert b"Match Score" in context.pdf_bytes


@then("I should see which property has each feature")
def step_features_present(context):
    for name, features in context.features.items():
        assert {"water_source", "electricity", "road_access", "corner_plot"} <= set(features)


@then("features should be color-coded (green=yes, yellow=partial, red=no)")
def step_features_colored(context):
    for features in context.features.values():
        for entry in features.values():
            assert entry["color"] in ("green", "yellow", "red"), entry


@then("I should see ROI projections")
def step_roi(context):
    for metrics in context.investment.values():
        assert "roi_pct" in metrics


@then("appreciation estimates")
def step_appreciation(context):
    for metrics in context.investment.values():
        assert "appreciation_pct" in metrics


@then("total investment including registration costs")
def step_total_investment(context):
    for metrics in context.investment.values():
        assert metrics["total_investment"] >= metrics["registration_cost"] > 0


@then("I should be able to retrieve it later")
def step_retrieve_later(context):
    assert cmp.get_comparison(context.session, context.comparison.name) is not None


@then("it should show the creation date")
def step_creation_date(context):
    fresh = cmp.get_comparison(context.session, context.comparison.name)
    assert fresh.created_at is not None


@then("I can add notes to the comparison")
def step_add_notes(context):
    cmp.add_notes(context.session, context.comparison, "Review over the weekend")
    assert context.comparison.notes == "Review over the weekend"


@then("the comparison table should update")
def step_table_updates(context):
    context.table_view = cmp.build_table(
        context.session, cmp.properties_in(context.session, context.comparison)
    )
    assert len(context.table_view["rows"]) == 3


@then("all columns should reflect the new property")
def step_columns_reflect(context):
    names = [r["name"] for r in context.table_view["rows"]]
    assert context.added_property.name in names


@then("the comparison should be re-saved")
def step_resaved(context):
    fresh = cmp.get_comparison(context.session, context.comparison.name)
    assert len(fresh.items) == 3


@then("I should see neighbor statistics")
def step_neighbor_stats(context):
    for row in context.table_view["rows"]:
        assert "count" in row["neighbors"] and "shared" in row["neighbors"]


@then("properties with more tracked neighbors should be highlighted")
def step_neighbor_highlight(context):
    rows = context.table_view["rows"]
    top = max(rows, key=lambda r: r["neighbors"]["count"])
    assert context.table_view["neighbor_highlight"] == top["name"]


@then("I should see the breakdown")
def step_see_breakdown(context):
    by_criterion = {b["criterion"]: b for b in context.breakdown}
    for row in context.table:
        criterion = row["criterion"]
        weight = int(row["weight"].rstrip("%"))
        assert criterion in by_criterion, f"{criterion!r} missing from breakdown"
        assert by_criterion[criterion]["weight"] == weight, (
            f"{criterion}: weight {by_criterion[criterion]['weight']} != {weight}"
        )


@then("I should see which criteria are strong/weak")
def step_strong_weak(context):
    strengths = {b["strength"] for b in context.breakdown}
    assert strengths <= {"strong", "moderate", "weak"}
    for entry in context.breakdown:
        assert entry["strength"] in ("strong", "moderate", "weak")
