"""Generate KML and GeoJSON from survey boundaries — pure stdlib, no deps.

KML (and GeoJSON) order coordinates **longitude, latitude** — the opposite of the
(lat, lng) tuples used elsewhere — so that ordering is applied deliberately here.
"""

import os
from typing import List
from xml.etree.ElementTree import Element, ElementTree, SubElement

from app.models.survey import SurveyBoundary

KML_NS = "http://www.opengis.net/kml/2.2"
KML_MEDIA_TYPE = "application/vnd.google-earth.kml+xml"

# KML colors are aabbggrr. Subject = solid blue outline; neighbor = green.
_STYLES = {
    "subject": "ff0000ff",
    "neighbor": "ff00aa00",
}


def _ring_coords(boundary: SurveyBoundary) -> str:
    """Space-separated ``lng,lat,0`` tuples, with the ring explicitly closed."""
    verts = list(boundary.vertices)
    if verts and (verts[0].lat, verts[0].lng) != (verts[-1].lat, verts[-1].lng):
        verts = verts + [verts[0]]
    return " ".join(f"{v.lng},{v.lat},0" for v in verts)


def _add_style(doc: Element, style_id: str, color: str) -> None:
    style = SubElement(doc, "Style", id=style_id)
    line = SubElement(style, "LineStyle")
    SubElement(line, "color").text = color
    SubElement(line, "width").text = "2"
    poly = SubElement(style, "PolyStyle")
    SubElement(poly, "color").text = "4d" + color[2:]  # ~30% opacity fill


def build_kml(boundaries: List[SurveyBoundary]) -> Element:
    kml = Element("kml", xmlns=KML_NS)
    doc = SubElement(kml, "Document")
    for style_id, color in _STYLES.items():
        _add_style(doc, style_id, color)
    for boundary in boundaries:
        placemark = SubElement(doc, "Placemark")
        SubElement(placemark, "name").text = boundary.label or "boundary"
        SubElement(placemark, "styleUrl").text = "#neighbor" if boundary.is_neighbor else "#subject"
        polygon = SubElement(placemark, "Polygon")
        outer = SubElement(polygon, "outerBoundaryIs")
        ring = SubElement(outer, "LinearRing")
        SubElement(ring, "coordinates").text = _ring_coords(boundary)
    return kml


def generate_kml(boundaries: List[SurveyBoundary], path: str) -> str:
    """Write a KML document for the given boundaries and return the path."""
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    ElementTree(build_kml(boundaries)).write(path, encoding="UTF-8", xml_declaration=True)
    return path


def geojson(boundaries: List[SurveyBoundary]) -> dict:
    """A GeoJSON FeatureCollection (lng,lat rings) for a web map. Each feature is
    tagged with ``role`` (subject/neighbor) so the UI can style layers."""
    features = []
    for boundary in boundaries:
        ring = [[v.lng, v.lat] for v in boundary.vertices]
        if ring and ring[0] != ring[-1]:
            ring.append(ring[0])
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "label": boundary.label,
                    "role": "neighbor" if boundary.is_neighbor else "subject",
                },
                "geometry": {"type": "Polygon", "coordinates": [ring]},
            }
        )
    return {"type": "FeatureCollection", "features": features}


def upload_to_mymaps(kml_path: str, credentials=None):  # pragma: no cover - gated stub
    """Upload a KML to Google My Maps. Requires OAuth credentials; wired later."""
    if not credentials:
        raise RuntimeError("Google My Maps upload requires credentials (not yet configured).")
    raise NotImplementedError("Google My Maps upload is not implemented yet.")
