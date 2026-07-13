"""Pydantic schemas for comparisons."""

from typing import List

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
