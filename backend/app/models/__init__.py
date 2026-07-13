"""SQLAlchemy models.

Importing this package registers every model on ``Base.metadata`` so that
``create_all`` sees the full schema.
"""

from app.models.base import Base, TimestampMixin
from app.models.broker import Broker, BrokerProperty
from app.models.comparison import Comparison, ComparisonItem
from app.models.document import Document, DocumentType, VerificationStatus
from app.models.preference import Preference
from app.models.price_history import PriceHistory
from app.models.property import (
    ActivityLog,
    Direction,
    Neighbor,
    Property,
    PropertyStatus,
    Subdivision,
)
from app.models.survey import SurveyBoundary, SurveyVertex

__all__ = [
    "Base",
    "TimestampMixin",
    "Property",
    "PropertyStatus",
    "Subdivision",
    "Neighbor",
    "Direction",
    "ActivityLog",
    "Broker",
    "BrokerProperty",
    "Comparison",
    "ComparisonItem",
    "Document",
    "DocumentType",
    "VerificationStatus",
    "Preference",
    "PriceHistory",
    "SurveyBoundary",
    "SurveyVertex",
]
