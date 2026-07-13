"""Unit tests for the OCR queue/processing pipeline (simulated provider)."""

from app.services import document_service as docs
from app.services import property_service as props
from app.services.ocr import SimulatedOcrProvider


def test_process_queue_drains_queued_documents(session):
    prop = props.create_property(session, name="P")
    docs.upload_document(session, prop, "Patta.pdf")
    docs.upload_document(session, prop, "FMB.pdf")
    # Photos are not queued for OCR.
    docs.upload_document(session, prop, "site.png")

    provider = SimulatedOcrProvider(
        by_filename={
            "Patta.pdf": {"survey_number": "171-4", "owner_name": "Ramesh Kumar"},
            "FMB.pdf": {"survey_number": "171-4A"},
        }
    )
    processed = docs.process_queue(session, provider)
    assert processed == 2  # only the two non-photo docs were queued

    patta = docs.documents_of_type(session, prop, docs.DocumentType.PATTA)[0]
    assert patta.ocr_status == "complete"
    assert patta.extracted_owner_name == "Ramesh Kumar"
    # Re-running finds nothing left queued.
    assert docs.process_queue(session, provider) == 0


def test_process_document_applies_provider_fields(session):
    prop = props.create_property(session, name="P")
    doc = docs.upload_document(session, prop, "Patta.pdf")
    provider = SimulatedOcrProvider(default={"survey_number": "184", "village": "Irumbli"})
    docs.process_document(session, doc, provider)
    assert doc.extracted_survey_number == "184" and doc.extracted_village == "Irumbli"
