"""Unit tests for survey_service: boundary storage and map gathering."""
import pytest

from app.services import property_service as props
from app.services import survey_service

SQUARE = [(12.9001, 79.1001), (12.9005, 79.1001), (12.9005, 79.1010), (12.9001, 79.1010)]


def test_add_boundary_stores_ordered_vertices(session):
    prop = props.create_property(session, name="Thuthikadu 171-4")
    boundary = survey_service.add_boundary(session, prop, SQUARE, label="171-4")
    assert boundary.id is not None
    assert [(v.lat, v.lng) for v in boundary.vertices] == SQUARE  # order preserved by seq


def test_boundary_requires_three_vertices(session):
    prop = props.create_property(session, name="P")
    with pytest.raises(survey_service.InvalidBoundary):
        survey_service.add_boundary(session, prop, SQUARE[:2])


def test_boundaries_for_map_includes_neighbors(session):
    prop = props.create_property(session, name="P")
    neighbor = props.add_neighbor(session, prop, survey_number="171-3A8")
    survey_service.add_boundary(session, prop, SQUARE)
    survey_service.add_boundary(session, prop, SQUARE, neighbor=neighbor)
    mapped = survey_service.boundaries_for_map(session, prop)
    assert len(mapped) == 2
    assert mapped[0].neighbor_id is None      # subject first
    assert mapped[1].neighbor_id == neighbor.id
