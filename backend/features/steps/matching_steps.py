"""Step definitions for smart_matching.feature."""

from behave import given, then, when

from app.services import matching_service as matching
from app.services import property_service as props

NUMERIC_FIELDS = {"budget_max", "size_min_sqft", "size_max_sqft"}
LIST_FIELDS = {"locations", "required_features"}


def _coerce(field, value):
    if field in NUMERIC_FIELDS:
        return float(value)
    if field in LIST_FIELDS:
        return [v.strip() for v in value.split(",") if v.strip()]
    return value


# ---------------------------------------------------------------------------
# Given / When — preferences
# ---------------------------------------------------------------------------
@when("I define my requirements")
def step_define_requirements(context):
    fields = {row["field"]: _coerce(row["field"], row["value"]) for row in context.table}
    context.current_preference = matching.create_preference(context.session, **fields)


@given('a preference "{name}" with budget {amount:d}')
def step_preference_with_budget(context, name, amount):
    context.current_preference = matching.create_preference(
        context.session, name=name, budget_max=float(amount)
    )


@when('I score the properties against "{name}"')
def step_score_properties(context, name):
    pref = matching.get_preference(context.session, name)
    matching.apply_scores(context.session, pref)


@when('I get recommendations for "{name}"')
def step_get_recommendations(context, name):
    pref = matching.get_preference(context.session, name)
    context.recommendations = matching.recommend(context.session, pref)


# ---------------------------------------------------------------------------
# Then
# ---------------------------------------------------------------------------
@then('a preference "{name}" should exist')
def step_preference_exists(context, name):
    pref = matching.get_preference(context.session, name)
    assert pref is not None, f"preference {name!r} not found"
    context.current_preference = pref


@then("the preference budget should be {amount:d}")
def step_preference_budget(context, amount):
    assert context.current_preference.budget_max == amount


@then("each property should have a match score between {low:d} and {high:d}")
def step_scores_bounded(context, low, high):
    properties = props.list_properties(context.session)
    assert properties, "no properties to score"
    for prop in properties:
        assert prop.match_score is not None, f"{prop.name} has no match score"
        assert low <= prop.match_score <= high, f"{prop.name}: {prop.match_score} out of range"


def _rec(context, name):
    return next(r for r in context.recommendations if r["name"] == name)


@then('"{name}" should be disqualified')
def step_disqualified(context, name):
    assert _rec(context, name)["disqualified"], f"{name} should be disqualified"


@then('"{name}" should not be disqualified')
def step_not_disqualified(context, name):
    assert not _rec(context, name)["disqualified"], f"{name} should not be disqualified"


@then('the disqualification reason should mention "{text}"')
def step_reason_mentions(context, text):
    all_reasons = " ".join(r for rec in context.recommendations for r in rec["reasons"])
    assert text.lower() in all_reasons.lower(), f"{text!r} not in reasons: {all_reasons!r}"


@then('"{name}" should be the top recommendation')
def step_top_recommendation(context, name):
    assert context.recommendations[0]["name"] == name, (
        f"top is {context.recommendations[0]['name']!r}, expected {name!r}"
    )


@then("the recommendations should be ranked by score")
def step_ranked_by_score(context):
    qualified = [r for r in context.recommendations if not r["disqualified"]]
    scores = [r["score"] for r in qualified]
    assert scores == sorted(scores, reverse=True), f"not ranked: {scores}"
