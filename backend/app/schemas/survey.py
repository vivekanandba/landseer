"""Pydantic schemas for survey boundaries."""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class VertexIn(BaseModel):
    lat: float
    lng: float


class BoundaryCreate(BaseModel):
    vertices: List[VertexIn] = Field(..., min_length=3)
    label: Optional[str] = None
    # When set, the boundary is attached to this neighbor (by survey number).
    neighbor_survey_number: Optional[str] = None


class VertexRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    seq: int
    lat: float
    lng: float


class BoundaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    property_id: int
    neighbor_id: Optional[int] = None
    label: Optional[str] = None
    vertices: List[VertexRead]


# ---------------------------------------------------------------------------
# GeoJSON response models for /map.geojson (previously an untyped dict).
# ---------------------------------------------------------------------------
class GeoGeometry(BaseModel):
    type: str
    coordinates: List[List[List[float]]]


class GeoFeatureProperties(BaseModel):
    label: Optional[str] = None
    role: str


class GeoFeature(BaseModel):
    type: str
    properties: GeoFeatureProperties
    geometry: GeoGeometry


class GeoFeatureCollection(BaseModel):
    type: str
    features: List[GeoFeature]
