"""Step definitions for ocr_processing.feature.

Reuses 'a property "X" exists' from property_steps.
"""
from behave import given, then, when

from app.services import document_service as docs
from app.services.ocr import SimulatedOcrProvider, extract_fields


@when("I parse the OCR text")
def step_parse_ocr(context):
    context.parsed = extract_fields(context.text)


@then('the parsed survey number should be "{value}"')
def step_parsed_survey(context, value):
    assert context.parsed.get("survey_number") == value


@then('the parsed owner name should be "{value}"')
def step_parsed_owner(context, value):
    assert context.parsed.get("owner_name") == value


@given('a document "{filename}" is uploaded')
def step_document_uploaded(context, filename):
    context.current_document = docs.upload_document(
        context.session, context.current_property, filename
    )


@when('I process the OCR queue with extracted survey number "{survey_number}"')
def step_process_queue(context, survey_number):
    provider = SimulatedOcrProvider(default={"survey_number": survey_number})
    context.processed = docs.process_queue(context.session, provider)


@then('the document OCR status should be "{status}"')
def step_ocr_status(context, status):
    context.session.refresh(context.current_document)
    assert context.current_document.ocr_status == status


@then('the document survey number should be "{survey_number}"')
def step_document_survey(context, survey_number):
    context.session.refresh(context.current_document)
    assert context.current_document.extracted_survey_number == survey_number
