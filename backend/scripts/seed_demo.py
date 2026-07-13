"""Seed a local database with demo data and print Smart Matching results.

Run from ``backend/``:

    venv/bin/python scripts/seed_demo.py

By default this uses a local SQLite file ``./landseer_demo.db`` so it works with
zero setup. Override with ``LANDSEER_DATABASE_URL`` to point at Postgres.

To then explore the API interactively against the same database, see
``docs/development/running-locally.md``.
"""
import os
import sys

# Make the backend package importable when run as a plain script.
_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

os.environ.setdefault("LANDSEER_DATABASE_URL", "sqlite+pysqlite:///./landseer_demo.db")

from app.database import create_all, get_sessionmaker, init_engine  # noqa: E402
from app.services import matching_service as matching  # noqa: E402
from app.services import property_service as props  # noqa: E402

PROPERTIES = [
    dict(name="Thuthikadu 171-4", location="Thuthikadu", area_sqft=12500,
         price_total=1850000, price_per_sqft=148, water_source="Yes",
         electricity="Yes", road_access="Yes"),
    dict(name="Moothakkal Plot", location="Moothakkal", area_sqft=10800,
         price_total=1600000, price_per_sqft=148, water_source="No",
         electricity="Yes", road_access="Yes"),
    dict(name="Kotikal Forest", location="Kathalampattu", area_sqft=112000,
         price_total=3500000, price_per_sqft=31, water_source="Yes",
         electricity="Nearby", road_access="Kutcha"),
    dict(name="Irumbli Farm", location="Irumbli", area_sqft=43560,
         price_total=2600000, price_per_sqft=60, water_source="Yes",
         electricity="Yes", road_access="Yes", corner_plot=True),
]


def _get_or_create_property(session, **fields):
    return props.get_property_by_name(session, fields["name"]) or props.create_property(
        session, **fields
    )


def main():
    init_engine(os.environ["LANDSEER_DATABASE_URL"])
    create_all()
    session = get_sessionmaker()()

    for fields in PROPERTIES:
        _get_or_create_property(session, **fields)

    pref = matching.get_preference(session, "My Ideal Plot")
    if pref is None:
        pref = matching.create_preference(
            session, name="My Ideal Plot", budget_max=3000000, size_min_sqft=10000,
            locations=["Thuthikadu", "Moothakkal", "Irumbli"],
            required_features=["water_source"],
        )
    session.commit()

    recs = matching.recommend(session, pref)
    print(
        f"\nSmart Matching — recommendations for {pref.name!r} "
        f"(budget <= {pref.budget_max:.0f}, needs {pref.required_features}):\n"
    )
    print(f"  {'#':<4}{'property':<20}{'score':>6}  status")
    print("  " + "-" * 60)
    for i, r in enumerate(recs, 1):
        status = "OK" if not r["disqualified"] else "DISQUALIFIED — " + "; ".join(r["reasons"])
        print(f"  {i:<4}{r['name']:<20}{r['score']:>6}  {status}")
    print(
        f"\nDatabase: {os.environ['LANDSEER_DATABASE_URL']}\n"
        f"Explore the full API interactively: see docs/development/running-locally.md\n"
    )


if __name__ == "__main__":
    main()
