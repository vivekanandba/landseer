"""Step definitions for broker_management.feature."""

from datetime import date

from behave import given, then, when

from app.services import broker_service as brokers
from app.services import property_service as props

NUMERIC_FIELDS = {"commission_rate", "asking_price"}


def _parse_date(value):
    return date.fromisoformat(value)


def _coerce(field, value):
    if field in NUMERIC_FIELDS:
        return float(value)
    if field == "shown_date":
        return _parse_date(value)
    return value


def _vertical_table_to_dict(table):
    return {row["field"]: _coerce(row["field"], row["value"]) for row in table}


# ---------------------------------------------------------------------------
# Given
# ---------------------------------------------------------------------------
@given('a broker "{name}" exists')
def step_broker_exists(context, name):
    context.current_broker = brokers.get_broker_by_name(context.session, name) or (
        brokers.create_broker(context.session, name=name)
    )


@given("the following brokers exist")
def step_following_brokers_exist(context):
    context.brokers = {}
    for row in context.table:
        fields = {h: _coerce(h, row[h]) for h in row.headings}
        broker = brokers.create_broker(context.session, **fields)
        context.brokers[broker.name] = broker


@given('a broker "{name}" with commission rate {rate:g}%')
def step_broker_with_rate(context, name, rate):
    context.current_broker = brokers.create_broker(context.session, name=name, commission_rate=rate)


@given('a property "{name}" with negotiated price {price:d}')
def step_property_with_negotiated_price(context, name, price):
    context.current_property = props.get_or_create_property(context.session, name=name)
    context.negotiated_price = float(price)


@given("the broker has shown {count:d} properties")
def step_broker_has_shown(context, count):
    context.shown_properties = []
    for i in range(count):
        prop = props.create_property(context.session, name=f"Shown Property {i + 1}")
        brokers.link_to_property(context.session, context.current_broker, prop)
        context.shown_properties.append(prop)


@given('{count:d} properties are marked as "{status}"')
@given('{count:d} property is marked as "{status}"')
def step_mark_properties(context, count, status):
    already = context._marked if "_marked" in context else 0
    for prop in context.shown_properties[already : already + count]:
        props.update_status(context.session, prop, status)
    context._marked = already + count


# ---------------------------------------------------------------------------
# When
# ---------------------------------------------------------------------------
@when("I create a broker with the following details")
def step_create_broker(context):
    fields = _vertical_table_to_dict(context.table)
    context.current_broker = brokers.create_broker(context.session, **fields)


@when("I link the broker to the property with")
def step_link_broker_with(context):
    fields = _vertical_table_to_dict(context.table)
    context.current_link = brokers.link_to_property(
        context.session, context.current_broker, context.current_property, **fields
    )


@when('I link "{name}" to the property on "{shown_date}"')
def step_link_named_broker(context, name, shown_date):
    broker = context.brokers[name]
    brokers.link_to_property(
        context.session, broker, context.current_property, shown_date=_parse_date(shown_date)
    )


@when("I calculate the broker commission")
def step_calculate_commission(context):
    context.commission = context.current_broker.commission_on(context.negotiated_price)


@when("I view the broker performance")
def step_view_performance(context):
    context.performance = brokers.performance(context.session, context.current_broker)


@when('I search for brokers covering "{area}"')
def step_search_brokers_by_area(context, area):
    context.broker_results = brokers.search_by_area(context.session, area)


# ---------------------------------------------------------------------------
# Then
# ---------------------------------------------------------------------------
@then('the broker "{name}" should exist')
def step_broker_should_exist(context, name):
    broker = brokers.get_broker_by_name(context.session, name)
    assert broker is not None, f"broker {name!r} not found"
    context.current_broker = broker


@then('the broker should cover "{first}" and "{second}"')
def step_broker_covers(context, first, second):
    areas = context.current_broker.areas
    assert first in areas, f"{first!r} not in {areas}"
    assert second in areas, f"{second!r} not in {areas}"


@then("the broker should be linked to the property")
def step_broker_linked(context):
    links = brokers.brokers_for_property(context.session, context.current_property)
    ids = {link.broker_id for link in links}
    assert context.current_broker.id in ids, "broker not linked to property"


@then("the asking price should be recorded as {price:d}")
def step_asking_price_recorded(context, price):
    assert context.current_link.asking_price == price, (
        f"expected {price}, got {context.current_link.asking_price}"
    )


@then("the property should have {count:d} brokers")
def step_property_broker_count(context, count):
    links = brokers.brokers_for_property(context.session, context.current_property)
    assert len(links) == count, f"expected {count} brokers, got {len(links)}"


@then('"{name}" should be the first broker to show it')
def step_first_broker(context, name):
    links = brokers.brokers_for_property(context.session, context.current_property)
    first = context.session.get(type(context.brokers[name]), links[0].broker_id)
    assert first.name == name, f"first broker is {first.name!r}, expected {name!r}"


@then("the commission should be {amount:d}")
def step_commission_should_be(context, amount):
    assert context.commission == amount, f"expected {amount}, got {context.commission}"


@then("the conversion rate should be {pct:d}%")
def step_conversion_rate(context, pct):
    actual = context.performance["conversion_rate"]
    assert actual == pct, f"expected {pct}%, got {actual}%"


@then("the shortlist rate should be {pct:d}%")
def step_shortlist_rate(context, pct):
    actual = context.performance["shortlist_rate"]
    assert actual == pct, f"expected {pct}%, got {actual}%"


@then("I should see {count:d} brokers")
def step_should_see_brokers(context, count):
    assert len(context.broker_results) == count, (
        f"expected {count} brokers, got {len(context.broker_results)}"
    )


@then('the brokers should be "{first}" and "{second}"')
def step_brokers_should_be(context, first, second):
    names = {b.name for b in context.broker_results}
    assert names == {first, second}, f"expected {{{first!r}, {second!r}}}, got {names}"
