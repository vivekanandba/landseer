"""Pydantic schemas for the import API."""

from typing import List, Optional

from pydantic import BaseModel


class FileEntryIn(BaseModel):
    path: str
    type: Optional[str] = None


class ImportPropertyRequest(BaseModel):
    name: str
    files: List[FileEntryIn] = []


class FolderIn(BaseModel):
    name: str
    files: List[FileEntryIn] = []


class BatchImportRequest(BaseModel):
    folders: List[FolderIn] = []


class ImportReport(BaseModel):
    properties_created: int
    subdivisions_created: int
    neighbors_tracked: int
    documents_imported: int
    photos_imported: int
    ocr_jobs_queued: int


class BatchImportResponse(BaseModel):
    properties_created: int
    documents_imported: int
    photos_imported: int
    summary: str
