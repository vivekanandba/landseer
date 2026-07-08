"""Steps shared across features (Background setup)."""
from behave import given


@given("the system is initialized")
def step_system_initialized(context):
    # Database tables are created in environment.before_scenario; nothing to do.
    assert context.session is not None


@given("I am logged in as a user")
def step_logged_in(context):
    # Authentication is out of scope for Phase 1; treat as a no-op user context.
    context.user = {"name": "test-user"}
