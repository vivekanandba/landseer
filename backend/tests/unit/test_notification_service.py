"""Unit tests for notification_service and property_service.record_price."""
from datetime import date

from app.models.document import DocumentType
from app.services import document_service as docs
from app.services import notification_service as notify
from app.services import property_service as props


def test_record_price_updates_property_and_history(session):
    prop = props.create_property(session, name="P", asking_price=1000000)
    props.record_price(session, prop, 1100000, source="broker")
    props.record_price(session, prop, 1200000, source="broker")
    session.refresh(prop)
    assert prop.asking_price == 1200000
    actions = [log.action for log in prop.activity_logs]
    assert actions.count("price_changed") == 2


def test_expiring_documents_uses_ec_validity(session):
    prop = props.create_property(session, name="P")
    docs.upload_document(
        session, prop, "EC.pdf", doc_type=DocumentType.EC, issue_date=date(2020, 1, 15)
    )
    # EC valid 30y -> expires 2050-01-15.
    assert notify.expiring_documents(session, within_days=30, as_of=date(2019, 1, 1)) == []
    soon = notify.expiring_documents(session, within_days=30, as_of=date(2050, 1, 1))
    assert len(soon) == 1 and "EC.pdf" in soon[0]["message"]


def test_price_change_alert_fires_over_threshold(session):
    prop = props.create_property(session, name="Plot", asking_price=1000000)
    props.record_price(session, prop, 1000000)
    props.record_price(session, prop, 1200000)  # +20%
    alerts = notify.price_change_alerts(session, threshold_pct=5.0)
    assert len(alerts) == 1 and alerts[0]["change_pct"] == 20.0
    # Below threshold -> nothing.
    assert notify.price_change_alerts(session, threshold_pct=25.0) == []


def test_follow_ups_flag_idle_evaluating_properties(session):
    prop = props.create_property(session, name="Idle Plot")  # created log ~ today
    fresh = notify.follow_ups(session, as_of=date.today(), idle_days=30)
    assert all(f["property_id"] != prop.id for f in fresh)  # not idle yet
    stale = notify.follow_ups(session, as_of=date(2027, 1, 1), idle_days=30)
    assert any(f["property_id"] == prop.id for f in stale)


def test_run_due_dispatches_via_notifier(session):
    prop = props.create_property(session, name="Plot", asking_price=1000000)
    props.record_price(session, prop, 1000000)
    props.record_price(session, prop, 2000000)
    notifier = notify.LogNotifier()
    result = notify.run_due(session, notifier, price_threshold_pct=5.0)
    assert result["price_alerts"]
    assert any("price" in m.lower() for m in notifier.messages)
