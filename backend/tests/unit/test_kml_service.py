"""Unit tests for kml_service: KML/GeoJSON generation and coordinate ordering."""

from pathlib import Path
from xml.etree.ElementTree import fromstring

from app.services import kml_service, survey_service
from app.services import property_service as props

SQUARE = [(12.9001, 79.1001), (12.9005, 79.1001), (12.9005, 79.1010), (12.9001, 79.1010)]
KML_NS = "{http://www.opengis.net/kml/2.2}"


def _prop_with_boundaries(session):
    prop = props.create_property(session, name="Thuthikadu 171-4")
    neighbor = props.add_neighbor(session, prop, survey_number="171-3A8")
    survey_service.add_boundary(session, prop, SQUARE, label="171-4")
    survey_service.add_boundary(session, prop, SQUARE, label="171-3A8", neighbor=neighbor)
    return prop


def test_generate_kml_is_valid_and_lng_lat_ordered(session, tmp_path):
    prop = _prop_with_boundaries(session)
    boundaries = survey_service.boundaries_for_map(session, prop)
    path = kml_service.generate_kml(boundaries, str(tmp_path / "out.kml"))

    text = Path(path).read_text()
    assert text.startswith("<?xml")

    root = fromstring(text)
    coords = root.iter(f"{KML_NS}coordinates")
    first = next(coords).text.split()[0]  # "lng,lat,0"
    lng, lat, _alt = first.split(",")
    assert float(lng) > 79 and float(lat) < 13  # KML is lng,lat — order matters
    # ring is closed: first == last vertex
    tokens = root.find(f".//{KML_NS}coordinates").text.split()
    assert tokens[0] == tokens[-1]


def test_neighbor_uses_a_different_style(session, tmp_path):
    prop = _prop_with_boundaries(session)
    boundaries = survey_service.boundaries_for_map(session, prop)
    root = fromstring(
        Path(kml_service.generate_kml(boundaries, str(tmp_path / "o.kml"))).read_text()
    )
    style_urls = [e.text for e in root.iter(f"{KML_NS}styleUrl")]
    assert "#subject" in style_urls and "#neighbor" in style_urls


def test_geojson_tags_roles(session):
    prop = _prop_with_boundaries(session)
    fc = kml_service.geojson(survey_service.boundaries_for_map(session, prop))
    roles = {f["properties"]["role"] for f in fc["features"]}
    assert roles == {"subject", "neighbor"}
    # GeoJSON polygon rings are lng,lat and closed.
    ring = fc["features"][0]["geometry"]["coordinates"][0]
    assert ring[0] == ring[-1] and ring[0][0] > 79
