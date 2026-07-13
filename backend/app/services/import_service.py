"""OneDrive import: turn a folder of files into the property hierarchy.

Callers describe a folder as a list of relative paths (a virtual filesystem),
which keeps this layer testable without touching a real OneDrive. Path shape
determines placement:

    "Patta.pdf"                          -> document on the property
    "171-4A/171-4A-FMB.pdf"              -> document on subdivision 171-4A
    "171-4A/"                            -> subdivision 171-4A (no document)
    "Neighbors/171-3A8/...pdf"           -> document on neighbor 171-3A8
    "Neighbors/171-3A8/"                 -> neighbor 171-3A8 (tracked, no doc)
"""
import os
from typing import List, Optional, Union

from sqlalchemy.orm import Session

from app.models.document import DocumentType
from app.models.property import Neighbor, Property, Subdivision
from app.services import document_service as docs
from app.services import property_service as props

FileEntry = Union[str, dict]


class ImportResult:
    def __init__(self, prop: Optional[Property] = None):
        self.property = prop
        self.properties_created = 0
        self.subdivisions_created = 0
        self.neighbors_tracked = 0
        self.documents_imported = 0
        self.photos_imported = 0
        self.ocr_jobs_queued = 0
        self.new_documents = 0
        self.skipped_documents = 0

    def report(self) -> dict:
        return {
            "properties_created": self.properties_created,
            "subdivisions_created": self.subdivisions_created,
            "neighbors_tracked": self.neighbors_tracked,
            "documents_imported": self.documents_imported,
            "photos_imported": self.photos_imported,
            "ocr_jobs_queued": self.ocr_jobs_queued,
        }


def _entry_parts(entry: FileEntry):
    path = entry["path"] if isinstance(entry, dict) else entry
    explicit = entry.get("type") if isinstance(entry, dict) else None
    is_folder = path.endswith("/")
    parts = [p for p in path.split("/") if p]
    return parts, is_folder, explicit


def _map_type(explicit: Optional[str]) -> Optional[DocumentType]:
    """Map a folder-supplied type hint to a DocumentType.

    Returns ``None`` for a missing or unrecognized hint so the caller falls back
    to filename-based auto-categorization rather than aborting the import.
    """
    if not explicit:
        return None
    try:
        return DocumentType(explicit)
    except ValueError:
        return None


def _get_subdivision(prop: Property, name: str) -> Optional[Subdivision]:
    return next((s for s in prop.subdivisions if s.name == name), None)


def _get_neighbor(prop: Property, survey_number: str) -> Optional[Neighbor]:
    return next((n for n in prop.neighbors if n.survey_number == survey_number), None)


def import_property(session: Session, name: str, files: List[FileEntry]) -> ImportResult:
    prop = props.get_property_by_name(session, name)
    result = ImportResult()
    if prop is None:
        prop = props.create_property(session, name=name)
        result.properties_created = 1
    result.property = prop

    seen_filenames = {d.filename for d in docs.documents_for_property(session, prop)}

    def ensure_subdivision(sub_name):
        sub = _get_subdivision(prop, sub_name)
        if sub is None:
            sub = props.add_subdivision(session, prop, name=sub_name, survey_number_full=sub_name)
            session.refresh(prop)
            result.subdivisions_created += 1
        return sub

    def ensure_neighbor(survey_number):
        neighbor = _get_neighbor(prop, survey_number)
        if neighbor is None:
            neighbor = props.add_neighbor(session, prop, survey_number=survey_number)
            session.refresh(prop)
            result.neighbors_tracked += 1
        return neighbor

    for entry in files:
        parts, is_folder, explicit = _entry_parts(entry)
        if not parts:
            continue

        subdivision = None
        neighbor = None
        filename = None

        if parts[0].lower() == "neighbors":
            if len(parts) >= 2:
                neighbor = ensure_neighbor(parts[1])
            if len(parts) >= 3 and not is_folder:
                filename = parts[-1]
        elif len(parts) >= 2 and not is_folder:
            subdivision = ensure_subdivision(parts[0])
            filename = parts[-1]
        elif is_folder:
            ensure_subdivision(parts[0])
        else:  # single path segment
            filename = parts[-1]

        if not filename:
            continue
        if filename in seen_filenames:
            result.skipped_documents += 1
            continue

        doc = docs.upload_document(
            session,
            prop,
            filename,
            subdivision=subdivision,
            neighbor=neighbor,
            doc_type=_map_type(explicit),
        )
        seen_filenames.add(filename)
        result.new_documents += 1
        if doc.doc_type == DocumentType.PHOTO:
            result.photos_imported += 1
        else:
            result.documents_imported += 1
        if docs.needs_ocr(doc):
            result.ocr_jobs_queued += 1

    return result


def batch_import(session: Session, folders: List[dict]) -> dict:
    """Import many property folders. Each folder: {"name", "files"}."""
    results = []
    for folder in folders:
        results.append(import_property(session, folder["name"], folder["files"]))

    properties_created = sum(r.properties_created for r in results)
    documents_imported = sum(r.documents_imported for r in results)
    photos_imported = sum(r.photos_imported for r in results)
    summary = (
        f"Imported {properties_created} properties, "
        f"{documents_imported} documents, {photos_imported} photos."
    )
    return {
        "properties_created": properties_created,
        "documents_imported": documents_imported,
        "photos_imported": photos_imported,
        "results": results,
        "summary": summary,
    }


# ---------------------------------------------------------------------------
# File sources — where the list of files comes from
# ---------------------------------------------------------------------------
class FileSource:
    """Yields the same list-of-path-dicts that ``import_property`` consumes."""

    def list_files(self) -> List[FileEntry]:  # pragma: no cover - interface
        raise NotImplementedError


class VirtualFileSource(FileSource):
    """In-memory source (used by tests and the BDD suite)."""

    def __init__(self, files: List[FileEntry]):
        self._files = files

    def list_files(self) -> List[FileEntry]:
        return self._files


class LocalFolderSource(FileSource):
    """A real, locally-synced OneDrive folder walked from disk.

    Emits paths relative to ``root`` with forward slashes so they parse
    identically to the virtual source (``import_property`` splits on "/").
    """

    def __init__(self, root: str):
        self.root = root

    def list_files(self) -> List[FileEntry]:
        entries: List[FileEntry] = []
        for dirpath, _dirs, filenames in os.walk(self.root):
            for filename in filenames:
                full = os.path.join(dirpath, filename)
                rel = os.path.relpath(full, self.root)
                entries.append({"path": rel.replace(os.sep, "/")})
        return entries


def import_from_source(session: Session, name: str, source: FileSource) -> ImportResult:
    """Import a property from any FileSource (virtual list, local folder, ...)."""
    return import_property(session, name, source.list_files())
