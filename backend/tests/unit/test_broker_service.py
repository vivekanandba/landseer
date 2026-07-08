"""Unit tests for broker_service: commission, performance, area search, ordering."""
from datetime import date

from app.services import broker_service as brokers
from app.services import property_service as props


def test_commission_calculation():
    broker = brokers.Broker(name="Rajesh Kumar", commission_rate=2.0)
    assert broker.commission_on(2_200_000) == 44_000


def test_area_search_is_case_insensitive(session):
    brokers.create_broker(session, name="Rajesh Kumar", areas_covered="Vellore,Katpadi")
    brokers.create_broker(session, name="Suresh Babu", areas_covered="Ranipet,Arcot")
    brokers.create_broker(session, name="Kumar Swamy", areas_covered="Vellore,Ranipet")
    found = brokers.search_by_area(session, "vellore")
    assert {b.name for b in found} == {"Rajesh Kumar", "Kumar Swamy"}


def test_first_broker_ordering(session):
    prop = props.create_property(session, name="Kotikal Forest")
    first = brokers.create_broker(session, name="Rajesh Kumar")
    second = brokers.create_broker(session, name="Suresh Babu")
    brokers.link_to_property(session, first, prop, shown_date=date(2025, 11, 20))
    brokers.link_to_property(session, second, prop, shown_date=date(2025, 11, 25))
    links = brokers.brokers_for_property(session, prop)
    assert links[0].broker_id == first.id


def test_performance_metrics(session):
    broker = brokers.create_broker(session, name="Rajesh Kumar")
    shown = [props.create_property(session, name=f"P{i}") for i in range(10)]
    for prop in shown:
        brokers.link_to_property(session, broker, prop)
    for prop in shown[:3]:
        props.update_status(session, prop, "shortlisted")
    props.update_status(session, shown[3], "purchased")
    metrics = brokers.performance(session, broker)
    assert metrics["shortlist_rate"] == 30.0
    assert metrics["conversion_rate"] == 10.0
