"""Step definitions for survey_visualization.feature."""

import os
import tempfile
from xml.etree.ElementTree import fromstring

from behave import given, then, when

from app.services import kml_service, survey_service
from app.services import property_service as props

SQUARE = [(12.9001, 79.1001), (12.9005, 79.1001), (12.9005, 79.1010), (12.9001, 79.1010)]
KML_NS = "{http://www.opengis.net/kml/2.2}"


# ---------------------------------------------------------------------------
# Given
# ---------------------------------------------------------------------------
@given('a property "{name}" exists with a survey boundary')
def step_property_with_boundary(context, name):
    context.current_property = props.get_or_create_property(context.session, name=name)
    survey_service.add_boundary(context.session, context.current_property, SQUARE, label=name)


@given('a neighbor "{survey_number}" has a survey boundary')
def step_neighbor_with_boundary(context, survey_number):
    neighbor = props.add_neighbor(
        context.session, context.current_property, survey_number=survey_number
    )
    survey_service.add_boundary(
        context.session, context.current_property, SQUARE, label=survey_number, neighbor=neighbor
    )


# ---------------------------------------------------------------------------
# When
# ---------------------------------------------------------------------------
@when("I import a survey boundary with vertices")
def step_import_boundary(context):
    vertices = [(float(row["lat"]), float(row["lng"])) for row in context.table]
    context.current_boundary = survey_service.add_boundary(
        context.session, context.current_property, vertices
    )


@when("I generate the KML for the property")
def step_generate_kml(context):
    boundaries = survey_service.boundaries_for_map(context.session, context.current_property)
    fd, path = tempfile.mkstemp(suffix=".kml", prefix="landseer-")
    os.close(fd)
    context.kml_path = kml_service.generate_kml(boundaries, path)


@when("I build the map data for the property")
def step_build_map(context):
    boundaries = survey_service.boundaries_for_map(context.session, context.current_property)
    context.geojson = kml_service.geojson(boundaries)


# ---------------------------------------------------------------------------
# Then
# ---------------------------------------------------------------------------
@then("the property should have a survey boundary")
def step_has_boundary(context):
    assert survey_service.boundary_for(context.session, context.current_property) is not None


@then("the boundary should have {count:d} vertices")
def step_vertex_count(context, count):
    assert len(context.current_boundary.vertices) == count


@then("a KML file should be generated")
def step_kml_generated(context):
    assert os.path.exists(context.kml_path)
    with open(context.kml_path) as fh:
        context.kml_text = fh.read()
    assert context.kml_text.startswith("<?xml")


@then("the KML coordinates should be in lng,lat order")
def step_kml_order(context):
    root = fromstring(context.kml_text)
    first = next(root.iter(f"{KML_NS}coordinates")).text.split()[0]
    lng, lat, _alt = first.split(",")
    assert float(lng) > 79 and float(lat) < 13, f"unexpected coord order: {first}"


@then("the map should include {count:d} boundaries")
def step_map_boundary_count(context, count):
    assert len(context.geojson["features"]) == count


@then("the neighbor boundary should be styled differently from the subject")
def step_neighbor_styled(context):
    roles = {f["properties"]["role"] for f in context.geojson["features"]}
    assert {"subject", "neighbor"} <= roles, f"roles were {roles}"
