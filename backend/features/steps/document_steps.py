"""Step definitions for document_management.feature."""
from datetime import date

from behave import given, then, when

from app.models.document import DocumentType, VerificationStatus
from app.services import document_service as docs
from app.services import property_service as props


def _parse_date(value):
    return date.fromisoformat(value)


def _find_subdivision_for(prop, filename):
    survey = docs.extract_survey_number(filename)
    for sub in prop.subdivisions:
        if survey and (sub.survey_number_full == survey or sub.name == survey):
            return sub
    return None


# ---------------------------------------------------------------------------
# Given
# ---------------------------------------------------------------------------
@given('a subdivision "{name}" exists')
def step_subdivision_exists(context, name):
    context.current_subdivision = props.add_subdivision(
        context.session, context.current_property, name=name, survey_number_full=name
    )


@given("the following documents are uploaded")
def step_following_documents_uploaded(context):
    context.uploaded = []
    for row in context.table:
        doc = docs.upload_document(
            context.session,
            context.current_property,
            row["filename"],
            extracted_survey_number=row.get("extracted_survey_number"),
        )
        context.uploaded.append(doc)


@given("multiple documents are uploaded with OCR completed")
def step_documents_with_ocr(context):
    for filename in ("Patta.pdf", "EC.pdf"):
        doc = docs.upload_document(context.session, context.current_property, filename)
        docs.simulate_ocr(
            context.session,
            doc,
            {"owner_name": "Ramesh Kumar", "village": "Thuthikadu"},
        )


# ---------------------------------------------------------------------------
# When
# ---------------------------------------------------------------------------
@when('I upload a document "{filename}" for the property')
def step_upload_document_for_property(context, filename):
    context.current_document = docs.upload_document(
        context.session, context.current_property, filename
    )


@when("I upload the following documents")
def step_upload_following_documents(context):
    context.categorized = []
    for row in context.table:
        doc = docs.upload_document(context.session, context.current_property, row["filename"])
        context.categorized.append((doc, row["expected_type"]))


@when('I upload "{filename}" which contains')
def step_upload_with_ocr(context, filename):
    doc = docs.upload_document(context.session, context.current_property, filename)
    fields = {row["field"]: row["value"] for row in context.table}
    context.current_document = docs.simulate_ocr(context.session, doc, fields)


@when('I upload an EC document with issue date "{issue_date}"')
def step_upload_ec_with_date(context, issue_date):
    context.current_document = docs.upload_document(
        context.session,
        context.current_property,
        "EC.pdf",
        doc_type=DocumentType.EC,
        issue_date=_parse_date(issue_date),
    )


@when('I upload "{first}", "{second}", and "{third}"')
def step_upload_three(context, first, second, third):
    for filename in (first, second, third):
        docs.upload_document(context.session, context.current_property, filename)


@when('I upload "{filename}" on "{uploaded_on}"')
def step_upload_on_date(context, filename, uploaded_on):
    context.current_document = docs.upload_document(
        context.session, context.current_property, filename
    )


@when('I upload "{filename}"')
def step_upload(context, filename):
    subdivision = _find_subdivision_for(context.current_property, filename)
    context.current_document = docs.upload_document(
        context.session, context.current_property, filename, subdivision=subdivision
    )


@when("I check the document verification status")
def step_check_verification(context):
    context.checklist = docs.checklist(context.session, context.current_property)


@when('the current date is "{as_of}"')
def step_set_current_date(context, as_of):
    context.as_of = _parse_date(as_of)


@when("I run cross-verification")
def step_run_cross_verify(context):
    context.crossverify = docs.cross_verify(context.session, context.current_property)


@when('I search for "{query}" in documents')
def step_search_documents(context, query):
    context.search_query = query
    context.search_results = docs.search_by_ocr(context.session, query)


# ---------------------------------------------------------------------------
# Then
# ---------------------------------------------------------------------------
@then('the document should be categorized as "{doc_type}"')
def step_document_categorized(context, doc_type):
    assert context.current_document.doc_type.value == doc_type, (
        f"expected {doc_type!r}, got {context.current_document.doc_type.value!r}"
    )


@then("the document should be linked to the property")
def step_document_linked_property(context):
    assert context.current_document.property_id == context.current_property.id


@then("OCR should be triggered automatically")
def step_ocr_triggered(context):
    assert docs.needs_ocr(context.current_document)
    assert context.current_document.ocr_status == "queued"


@then("all documents should be correctly categorized")
def step_all_categorized(context):
    for doc, expected in context.categorized:
        assert doc.doc_type.value == expected, (
            f"{doc.filename}: expected {expected!r}, got {doc.doc_type.value!r}"
        )


@then('the document should be linked to subdivision "{name}"')
def step_document_linked_subdivision(context, name):
    sub = context.current_subdivision
    assert sub.name == name
    assert context.current_document.subdivision_id == sub.id, "not linked to subdivision"


@then("the document should also be linked to the parent property")
def step_document_linked_parent(context):
    assert context.current_document.property_id == context.current_property.id


@then('OCR should extract survey number as "{value}"')
def step_ocr_survey(context, value):
    assert context.current_document.extracted_survey_number == value


@then('OCR should extract owner name as "{value}"')
def step_ocr_owner(context, value):
    assert context.current_document.extracted_owner_name == value


@then('OCR should extract extent as "{value}"')
def step_ocr_extent(context, value):
    assert context.current_document.extracted_extent == value


@then("the checklist should show")
def step_checklist_shows(context):
    checklist = docs.checklist(context.session, context.current_property)
    for row in context.table:
        doc_type, expected = row["document_type"], row["status"]
        assert checklist.get(doc_type) == expected, (
            f"{doc_type}: expected {expected!r}, got {checklist.get(doc_type)!r}"
        )


@then('the document should show as "{state}"')
def step_document_state(context, state):
    as_of = context.as_of if "as_of" in context else date.today()
    expired = docs.is_expired(context.current_document, as_of)
    actual = "expired" if expired else "valid"
    assert actual == state, f"expected {state!r}, got {actual!r}"


@then("I should receive an expiry alert")
def step_expiry_alert(context):
    as_of = context.as_of if "as_of" in context else date.today()
    assert docs.is_expired(context.current_document, as_of), "no expiry alert raised"


@then('a mismatch alert should be raised for "{filename}"')
def step_mismatch_alert(context, filename):
    assert filename in context.crossverify["mismatches"], (
        f"{filename!r} not in mismatches {context.crossverify['mismatches']}"
    )


@then('the verification status should be "{status}"')
def step_verification_status(context, status):
    all_docs = docs.documents_for_property(context.session, context.current_property)
    assert any(d.status.value == status for d in all_docs), (
        f"no document has status {status!r}"
    )


@then("I should find all documents containing that name")
def step_find_all_docs(context):
    assert context.search_results, "no documents matched"
    for doc in context.search_results:
        assert context.search_query.lower() in doc.ocr_text.lower()


@then("the results should highlight matching text")
def step_results_highlight(context):
    doc = context.search_results[0]
    highlighted = docs.highlight(doc.ocr_text, context.search_query)
    assert "[[" in highlighted and "]]" in highlighted


@then("the property should have {count:d} Patta documents")
def step_patta_count(context, count):
    patta = docs.documents_of_type(
        context.session, context.current_property, DocumentType.PATTA
    )
    assert len(patta) == count, f"expected {count} patta docs, got {len(patta)}"


@then('the latest version should be "{filename}"')
def step_latest_version(context, filename):
    latest = docs.latest_version(
        context.session, context.current_property, DocumentType.PATTA
    )
    assert latest is not None and latest.filename == filename, (
        f"latest is {latest.filename if latest else None!r}, expected {filename!r}"
    )


@then("the version history should be tracked")
def step_version_history(context):
    patta = docs.documents_of_type(
        context.session, context.current_property, DocumentType.PATTA
    )
    versions = sorted(d.version for d in patta)
    assert versions == list(range(1, len(patta) + 1)), f"unexpected versions {versions}"
