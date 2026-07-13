"""Step definitions for property_management.feature."""

from behave import given, then, when

from app.models.property import ActivityLog
from app.services import property_service as svc

# Fields that must be stored as numbers rather than strings.
NUMERIC_FIELDS = {"total_area_sqft", "asking_price", "price_per_sqft"}


def _coerce(field, value):
    if field in NUMERIC_FIELDS:
        return float(value)
    return value


def _row_table_to_dict(table):
    """Convert a vertical |field|value| table into a dict."""
    return {row["field"]: _coerce(row["field"], row["value"]) for row in table}


# ---------------------------------------------------------------------------
# Given
# ---------------------------------------------------------------------------
@given('a property "{name}" exists')
def step_property_exists(context, name):
    context.current_property = svc.get_or_create_property(context.session, name=name)


@given('a property "{name}" exists with status "{status}"')
def step_property_exists_with_status(context, name, status):
    context.current_property = svc.get_or_create_property(context.session, name=name, status=status)


@given("the following properties exist")
def step_following_properties_exist(context):
    for row in context.table:
        fields = {h: _coerce(h, row[h]) for h in row.headings}
        svc.create_property(context.session, **fields)


# ---------------------------------------------------------------------------
# When
# ---------------------------------------------------------------------------
@when("I create a property with the following details")
def step_create_property(context):
    fields = _row_table_to_dict(context.table)
    context.current_property = svc.create_property(context.session, **fields)


@when("I add the following subdivisions")
def step_add_subdivisions(context):
    prop = context.current_property
    for row in context.table:
        svc.add_subdivision(
            context.session,
            prop,
            name=row["name"],
            survey_number_full=row["survey_number_full"],
            area_sqft=float(row["area_sqft"]),
        )


@when("I add the following neighbors")
def step_add_neighbors(context):
    prop = context.current_property
    for row in context.table:
        svc.add_neighbor(
            context.session,
            prop,
            survey_number=row["survey_number"],
            direction=row["direction"],
            notes=row["notes"],
        )


@when('I update the property status to "{status}"')
def step_update_status(context, status):
    svc.update_status(context.session, context.current_property, status)


@when('I search for properties in "{location}"')
def step_search_location(context, location):
    context.last_result = svc.search_by_location(context.session, location)


@when("I filter properties with price between {low:d} and {high:d}")
def step_filter_price(context, low, high):
    context.last_result = svc.filter_by_price(context.session, low, high)


# ---------------------------------------------------------------------------
# Then
# ---------------------------------------------------------------------------
@then('the property "{name}" should exist')
def step_property_should_exist(context, name):
    prop = svc.get_property_by_name(context.session, name)
    assert prop is not None, f"Property {name!r} was not found"
    context.current_property = prop


@then('the property should have survey number "{survey_number}"')
def step_property_survey_number(context, survey_number):
    assert context.current_property.survey_number == survey_number


@then('the property should be in status "{status}"')
@then('the property status should be "{status}"')
def step_property_status(context, status):
    context.session.refresh(context.current_property)
    assert context.current_property.status.value == status, (
        f"expected {status!r}, got {context.current_property.status.value!r}"
    )


@then("the property should have {count:d} subdivisions")
def step_property_subdivision_count(context, count):
    context.session.refresh(context.current_property)
    actual = len(context.current_property.subdivisions)
    assert actual == count, f"expected {count} subdivisions, got {actual}"


@then("the total subdivision area should be {area:d} sqft")
def step_total_subdivision_area(context, area):
    actual = context.current_property.subdivision_area_sqft
    assert actual == area, f"expected {area} sqft, got {actual}"


@then("the property should have {count:d} neighbors tracked")
def step_property_neighbor_count(context, count):
    context.session.refresh(context.current_property)
    actual = len(context.current_property.neighbors)
    assert actual == count, f"expected {count} neighbors, got {actual}"


@then('neighbor "{survey_number}" should be to the "{direction}"')
def step_neighbor_direction(context, survey_number, direction):
    match = next(
        (n for n in context.current_property.neighbors if n.survey_number == survey_number),
        None,
    )
    assert match is not None, f"neighbor {survey_number!r} not found"
    assert match.direction.value == direction


@then("the update should be logged in the activity timeline")
def step_update_logged(context):
    logs = (
        context.session.query(ActivityLog)
        .filter(ActivityLog.property_id == context.current_property.id)
        .all()
    )
    assert any(log.action == "status_changed" for log in logs), "no status change logged"


@then("I should see {count:d} property")
@then("I should see {count:d} properties")
def step_should_see_count(context, count):
    actual = len(context.last_result)
    assert actual == count, f"expected {count} results, got {actual}"


@then('the property should be "{name}"')
def step_single_result_is(context, name):
    names = [p.name for p in context.last_result]
    assert names == [name], f"expected [{name!r}], got {names}"


@then('the properties should include "{first}" and "{second}"')
def step_results_include(context, first, second):
    names = {p.name for p in context.last_result}
    assert first in names, f"{first!r} not in {names}"
    assert second in names, f"{second!r} not in {names}"
