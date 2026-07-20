"""Pydantic schemas for comparisons."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class ComparisonCreate(BaseModel):
    name: str
    property_ids: List[int] = []
    notes: str = ""


class ComparisonNotes(BaseModel):
    notes: str


class ComparisonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    notes: str


# ---------------------------------------------------------------------------
# Response models for the derived comparison views (previously untyped dicts).
# ---------------------------------------------------------------------------
class ComparisonTable(BaseModel):
    columns: List[str]
    # Row keys are human-facing column labels (with spaces) plus nested
    # documents/neighbors sub-objects, so rows stay loosely typed.
    rows: List[Dict[str, Any]]
    neighbor_highlight: Optional[str] = None


class FeatureCell(BaseModel):
    value: Any = None
    color: str


class InvestmentEntry(BaseModel):
    appreciation_pct: float
    projected_value_3y: int
    roi_pct: float
    rental_yield: Optional[str] = None
    registration_cost: int
    total_investment: int
