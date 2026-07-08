"""Pydantic schemas for the property aggregate."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.property import Direction, PropertyStatus


class SubdivisionCreate(BaseModel):
    name: str
    survey_number_full: Optional[str] = None
    area_sqft: Optional[float] = None


class SubdivisionRead(SubdivisionCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    property_id: int


class NeighborCreate(BaseModel):
    survey_number: str
    direction: Optional[Direction] = None
    notes: Optional[str] = None
    shared_boundary: bool = False


class NeighborRead(NeighborCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    property_id: int


class ActivityLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    action: str
    detail: Optional[str] = None
    created_at: datetime


class PropertyBase(BaseModel):
    name: str
    survey_number: Optional[str] = None
    location: Optional[str] = None
    taluk: Optional[str] = None
    district: str = "Vellore"
    total_area_sqft: Optional[float] = None
    asking_price: Optional[float] = None
    price_per_sqft: Optional[float] = None
    water_source: Optional[str] = None
    electricity: Optional[str] = None
    road_access: Optional[str] = None
    corner_plot: Optional[bool] = None
    notes: Optional[str] = None


class PropertyCreate(PropertyBase):
    status: PropertyStatus = PropertyStatus.EVALUATING


class PropertyUpdate(BaseModel):
    name: Optional[str] = None
    survey_number: Optional[str] = None
    location: Optional[str] = None
    taluk: Optional[str] = None
    total_area_sqft: Optional[float] = None
    asking_price: Optional[float] = None
    price_per_sqft: Optional[float] = None
    status: Optional[PropertyStatus] = None
    water_source: Optional[str] = None
    electricity: Optional[str] = None
    road_access: Optional[str] = None
    corner_plot: Optional[bool] = None
    notes: Optional[str] = None


class PropertyRead(PropertyBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: PropertyStatus
    created_at: datetime
    updated_at: datetime
    subdivisions: List[SubdivisionRead] = Field(default_factory=list)
    neighbors: List[NeighborRead] = Field(default_factory=list)
