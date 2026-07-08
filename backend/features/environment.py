"""Behave environment hooks.

Each scenario runs against a fresh in-memory SQLite database so scenarios are
fully isolated and the BDD suite needs no external PostgreSQL instance.
"""
import os
import sys

# Ensure the backend package root (this file's grandparent) is importable when
# behave is launched as a console script.
_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from app.database import create_all, drop_all, get_sessionmaker, init_engine


def before_all(context):
    # One shared in-memory engine for the whole run; tables are reset per scenario.
    init_engine("sqlite+pysqlite:///:memory:")


def before_scenario(context, scenario):
    create_all()
    context.session = get_sessionmaker()()
    # Scratch space for entities created during a scenario.
    context.current_property = None
    context.last_result = None


def after_scenario(context, scenario):
    session = getattr(context, "session", None)
    if session is not None:
        session.close()
    drop_all()
