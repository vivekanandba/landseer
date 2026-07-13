"""Unit tests for import_service: placement, dedupe, batch, reporting."""
from app.services import import_service as importer
from app.services import property_service as props


def test_import_places_subdivisions_and_neighbors(session):
    files = [
        {"path": "1392-171-4-Patta.pdf"},
        {"path": "171-4A/171-4A-FMB.pdf"},
        {"path": "Neighbors/171-3A8/171-3A8-Integrated-Land-Records.pdf"},
    ]
    result = importer.import_property(session, "Thuthikadu", files)
    assert result.properties_created == 1
    assert result.subdivisions_created == 1
    assert result.neighbors_tracked == 1
    assert result.documents_imported == 3


def test_photos_counted_separately(session):
    files = [
        {"path": "Cultivated-Crops.png", "type": "photo"},
        {"path": "Govt-Land-Boundary-North.png", "type": "photo"},
        {"path": "Soil-Health-Card.pdf", "type": "document"},
    ]
    result = importer.import_property(session, "Kotikal Forest", files)
    assert result.photos_imported == 2
    assert result.documents_imported == 1


def test_reimport_skips_duplicates(session):
    files = [{"path": "Patta.pdf"}, {"path": "FMB.pdf"}, {"path": "EC.pdf"}]
    importer.import_property(session, "Moothakkal", files)
    again = importer.import_property(session, "Moothakkal", files)
    assert again.properties_created == 0
    assert again.new_documents == 0
    assert again.skipped_documents == 3


def test_local_folder_source_walks_disk(session, tmp_path):
    (tmp_path / "171-4A").mkdir()
    (tmp_path / "Neighbors" / "171-3A8").mkdir(parents=True)
    (tmp_path / "1392-171-4-Patta.pdf").write_text("x")
    (tmp_path / "171-4A" / "171-4A-FMB.pdf").write_text("x")
    (tmp_path / "Neighbors" / "171-3A8" / "171-3A8-Patta.pdf").write_text("x")

    source = importer.LocalFolderSource(str(tmp_path))
    result = importer.import_from_source(session, "Thuthikadu", source)
    assert result.properties_created == 1
    assert result.subdivisions_created == 1
    assert result.neighbors_tracked == 1
    assert result.documents_imported == 3


def test_batch_import_totals(session):
    folders = [
        {"name": "Moothakkal", "files": [{"path": f"m-{i}.pdf"} for i in range(3)]},
        {"name": "Irumbli", "files": [{"path": f"i-{i}.pdf"} for i in range(4)]},
    ]
    batch = importer.batch_import(session, folders)
    assert batch["properties_created"] == 2
    assert batch["documents_imported"] == 7
    assert "Imported 2 properties" in batch["summary"]
