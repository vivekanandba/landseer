"""Step definitions for automation.feature.

Reuses shared steps for "a property X exists" (property_steps), and
"a property X should be created" / "the property should have N documents"
(onedrive_steps).
"""
import os
import tempfile
from datetime import date

from behave import given, then, when

from app.models.document import DocumentType
from app.services import document_service as docs
from app.services import import_service as importer
from app.services import notification_service as notify
from app.services import property_service as props


def _parse_date(value):
    return date.fromisoformat(value)


# ---------------------------------------------------------------------------
# When — actions
# ---------------------------------------------------------------------------
@when("the asking price changes to {amount:d}")
def step_price_changes(context, amount):
    props.record_price(context.session, context.current_property, float(amount))


@when("I run the due notifications")
def step_run_notifications(context):
    context.notifier = notify.LogNotifier()
    context.notifications = notify.run_due(context.session, context.notifier)


@when('I check notifications as of "{as_of}"')
def step_check_notifications(context, as_of):
    context.notifications = notify.collect(context.session, as_of=_parse_date(as_of))


@given('an EC document issued on "{issue_date}" is uploaded')
def step_upload_ec(context, issue_date):
    docs.upload_document(
        context.session,
        context.current_property,
        "EC.pdf",
        doc_type=DocumentType.EC,
        issue_date=_parse_date(issue_date),
    )


@given("a local folder with these files")
def step_local_folder(context):
    root = tempfile.mkdtemp(prefix="landseer-onedrive-")
    for row in context.table:
        full = os.path.join(root, row["path"])
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w") as fh:
            fh.write("x")
    context.folder_root = root


@when('I import "{name}" from that folder')
def step_import_from_folder(context, name):
    source = importer.LocalFolderSource(context.folder_root)
    context.result = importer.import_from_source(context.session, name, source)
    context.current_property = context.result.property


# ---------------------------------------------------------------------------
# Then
# ---------------------------------------------------------------------------
@then('there should be a price change alert for "{name}"')
def step_price_alert(context, name):
    names = [a["name"] for a in context.notifications["price_alerts"]]
    assert name in names, f"{name!r} not in price alerts {names}"


@then("there should be an expiry reminder")
def step_expiry_reminder(context):
    assert context.notifications["expiring_documents"], "no expiry reminders"


@then('there should be a follow-up for "{name}"')
def step_follow_up(context, name):
    names = [f["name"] for f in context.notifications["follow_ups"]]
    assert name in names, f"{name!r} not in follow-ups {names}"
