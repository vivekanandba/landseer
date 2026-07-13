"""Pydantic schemas for the Smart Matching API."""

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class PreferenceCreate(BaseModel):
    name: str
    size_min_sqft: Optional[float] = None
    size_max_sqft: Optional[float] = None
    budget_max: Optional[float] = None
    locations: List[str] = []
    required_features: List[str] = []
    weights: Optional[Dict[str, int]] = None
    notes: Optional[str] = None


class PreferenceRead(PreferenceCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class BreakdownItem(BaseModel):
    criterion: str
    score: int
    weight: int
    strength: str


class Recommendation(BaseModel):
    name: str
    score: int
    disqualified: bool
    reasons: List[str]
    breakdown: List[BreakdownItem]
