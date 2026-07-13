"""Step definitions for onedrive_import.feature."""

from behave import given, then, when

from app.models.document import DocumentType
from app.services import document_service as docs
from app.services import import_service as importer
from app.services import property_service as props


def _basename(path):
    return path.rstrip("/").split("/")[-1]


def _parent_name(path):
    return path.rstrip("/").split("/")[-2]


def _non_photo_docs(context, prop):
    return [
        d
        for d in docs.documents_for_property(context.session, prop)
        if d.doc_type != DocumentType.PHOTO
    ]


def _photo_docs(context, prop):
    return [
        d
        for d in docs.documents_for_property(context.session, prop)
        if d.doc_type == DocumentType.PHOTO
    ]


def _parse_tree(text):
    lines = [ln for ln in text.splitlines() if ln.strip()]
    property_name = lines[0].strip().rstrip("/").split("/")[-1]
    files = []
    stack = []  # (indent, folder_name)
    for line in lines[1:]:
        indent = len(line) - len(line.lstrip())
        name = line.strip()
        is_folder = name.endswith("/")
        clean = name.rstrip("/")
        while stack and stack[-1][0] >= indent:
            stack.pop()
        prefix = "/".join(n for _, n in stack)
        rel = f"{prefix}/{clean}" if prefix else clean
        if is_folder:
            stack.append((indent, clean))
            files.append(rel + "/")
        else:
            files.append(rel)
    return property_name, files


# ---------------------------------------------------------------------------
# Background
# ---------------------------------------------------------------------------
@given('the OneDrive folder is "{path}"')
def step_onedrive_folder(context, path):
    context.onedrive_root = path
    context.files = []


# ---------------------------------------------------------------------------
# Given (folder descriptions)
# ---------------------------------------------------------------------------
@given('a folder exists at "{path}"')
def step_folder_exists(context, path):
    context.folder_path = path
    context.import_name = _basename(path)
    context.files = []


@given('a folder "{path}" contains')
def step_folder_contains_inline(context, path):
    context.folder_path = path
    context.import_name = _basename(path)
    context.files = [{"path": row["filename"], "type": row["type"]} for row in context.table]


@given("it contains the following files")
@given("it contains")
def step_it_contains(context):
    entries = []
    for row in context.table:
        path = row["path"] if "path" in row.headings else row["filename"]
        entry = {"path": path}
        if "type" in row.headings:
            entry["type"] = row["type"]
        entries.append(entry)
    context.files = entries


@given("it contains subfolders")
def step_it_contains_subfolders(context):
    context.files = [
        {"path": f"Neighbors/{row['neighbor_folder']}/{row['document_file']}"}
        for row in context.table
    ]


@given("the following files exist")
def step_following_files_exist(context):
    context.survey_rows = [
        (row["filename"], row["expected_survey_number"]) for row in context.table
    ]


@given('a file "{path}" exists')
def step_file_exists(context, path):
    context.import_name = _parent_name(path)
    context.files = [{"path": _basename(path)}]


@given('the following folders exist under "{root}"')
def step_folders_exist(context, root):
    context.folders = []
    for row in context.table:
        count = int(row["file_count"])
        name = row["folder_name"]
        files = [{"path": f"{name}-{i}.pdf"} for i in range(count)]
        context.folders.append({"name": name, "files": files})


@given('a property "{name}" already exists in the system')
def step_property_already_exists(context, name):
    context.import_name = name
    context.existing_property = props.get_or_create_property(context.session, name=name)


@given("it has {count:d} documents")
def step_it_has_documents(context, count):
    names = ["Patta.pdf", "FMB.pdf", "EC.pdf"]
    context.dupe_files = [{"path": n} for n in names[:count]]
    for entry in context.dupe_files:
        docs.upload_document(context.session, context.existing_property, entry["path"])


@given("the folder structure")
def step_folder_structure(context):
    name, files = _parse_tree(context.text)
    context.import_name = name
    context.files = files


# ---------------------------------------------------------------------------
# When
# ---------------------------------------------------------------------------
@when('I run the import for "{name}"')
def step_run_import_named(context, name):
    context.result = importer.import_property(context.session, name, context.files)
    context.current_property = context.result.property


@when("I run the import")
@when("I run structured import")
def step_run_import(context):
    context.result = importer.import_property(context.session, context.import_name, context.files)
    context.current_property = context.result.property


@when('I run the import again for "{name}"')
def step_run_import_again(context, name):
    context.result = importer.import_property(context.session, name, context.dupe_files)
    context.current_property = context.result.property


@when("I run survey number extraction")
def step_run_survey_extraction(context):
    context.extracted = {
        filename: docs.extract_survey_number(filename) for filename, _ in context.survey_rows
    }


@when("I run batch import for all folders")
def step_run_batch(context):
    context.batch = importer.batch_import(context.session, context.folders)


@when('I complete an import of "{name}"')
def step_complete_import(context, name):
    files = [
        {"path": "1392-171-4-Patta.pdf"},
        {"path": "171-4-EC-Kaniayambadi.pdf"},
        {"path": "171-4A/171-4A-FMB.pdf"},
        {"path": "171-4C/171-4C-Integrated-Land-Record.pdf"},
        {"path": "171-4D/FMB-171-4D.pdf"},
        {"path": "Neighbors/171-3A8/171-3A8-Integrated-Land-Records.pdf"},
        {"path": "Neighbors/171-4B1/171-4B1-Integrated-Land-Records.pdf"},
        {"path": "Neighbors/171-5A2/171-5A2-Patta.pdf"},
        {"path": "Neighbors/171-6/"},
        {"path": "Neighbors/171-7/"},
        {"path": "Neighbors/171-8/"},
    ]
    context.result = importer.import_property(context.session, name, files)
    context.current_property = context.result.property


# ---------------------------------------------------------------------------
# Then
# ---------------------------------------------------------------------------
@then('a property "{name}" should be created')
def step_property_created(context, name):
    prop = props.get_property_by_name(context.session, name)
    assert prop is not None, f"property {name!r} not created"
    context.current_property = prop


@then("the property should have {count:d} documents")
def step_property_document_count(context, count):
    actual = len(_non_photo_docs(context, context.current_property))
    assert actual == count, f"expected {count} documents, got {actual}"


@then("the property should have {count:d} document")
def step_property_single_document(context, count):
    step_property_document_count(context, count)


@then("the property should have {count:d} photos")
def step_property_photo_count(context, count):
    actual = len(_photo_docs(context, context.current_property))
    assert actual == count, f"expected {count} photos, got {actual}"


@then('documents should be categorized as "{first}", "{second}", and "{third}"')
def step_documents_categorized_as(context, first, second, third):
    types = {
        d.doc_type.value
        for d in docs.documents_for_property(context.session, context.current_property)
    }
    assert {first, second, third} <= types, f"expected {{{first},{second},{third}}} in {types}"


@then('the property should have {count:d} subdivisions: "{a}", "{b}", "{c}"')
def step_property_subdivisions_named(context, count, a, b, c):
    names = {s.name for s in context.current_property.subdivisions}
    assert len(names) == count, f"expected {count} subdivisions, got {len(names)}"
    assert {a, b, c} <= names, f"expected {{{a},{b},{c}}}, got {names}"


@then('subdivision "{name}" should have {count:d} document')
def step_subdivision_document_count(context, name, count):
    sub = next(s for s in context.current_property.subdivisions if s.name == name)
    actual = len(docs.documents_for_subdivision(context.session, sub))
    assert actual == count, f"subdivision {name}: expected {count} docs, got {actual}"


@then("the property should have {count:d} neighbors")
def step_property_neighbor_count_import(context, count):
    actual = len(context.current_property.neighbors)
    assert actual == count, f"expected {count} neighbors, got {actual}"


@then('neighbor "{name}" should have {count:d} document')
def step_neighbor_document_count(context, name, count):
    neighbor = next(n for n in context.current_property.neighbors if n.survey_number == name)
    actual = len(docs.documents_for_neighbor(context.session, neighbor))
    assert actual == count, f"neighbor {name}: expected {count} docs, got {actual}"


@then("all survey numbers should be correctly extracted")
def step_all_surveys_extracted(context):
    for filename, expected in context.survey_rows:
        actual = context.extracted[filename]
        assert actual == expected, f"{filename}: expected {expected!r}, got {actual!r}"


@then('the file should be categorized as "{doc_type}"')
def step_file_categorized(context, doc_type):
    documents = docs.documents_for_property(context.session, context.current_property)
    context.current_document = documents[0]
    assert context.current_document.doc_type.value == doc_type, (
        f"expected {doc_type!r}, got {context.current_document.doc_type.value!r}"
    )


@then('it should be linked to the property "{name}"')
def step_file_linked_to_property(context, name):
    prop = props.get_property_by_name(context.session, name)
    assert context.current_document.property_id == prop.id


@then("OCR should extract text for search indexing")
def step_ocr_indexing(context):
    assert docs.needs_ocr(context.current_document)


@then("{count:d} properties should be created")
def step_batch_properties(context, count):
    assert context.batch["properties_created"] == count, (
        f"expected {count}, got {context.batch['properties_created']}"
    )


@then("a total of {count:d} documents should be imported")
def step_batch_documents(context, count):
    assert context.batch["documents_imported"] == count, (
        f"expected {count}, got {context.batch['documents_imported']}"
    )


@then("an import summary should be generated")
def step_batch_summary(context):
    assert context.batch["summary"]


@then("the system should detect existing property")
def step_detect_existing(context):
    assert context.result.properties_created == 0, "property was recreated"


@then("it should only import new documents")
def step_only_new(context):
    assert context.result.new_documents == 0, (
        f"expected 0 new documents, got {context.result.new_documents}"
    )


@then("it should not create duplicate records")
def step_no_duplicates(context):
    total = len(docs.documents_for_property(context.session, context.current_property))
    assert total == len(context.dupe_files), (
        f"expected {len(context.dupe_files)} documents, got {total}"
    )


@then("the database should mirror this hierarchy")
def step_mirror_hierarchy(context):
    prop = context.current_property
    for row in context.table:
        kind, name, parent = row["type"], row["name"], row["parent"]
        if kind == "property":
            assert prop.name == name, f"property {prop.name!r} != {name!r}"
        elif kind == "subdivision":
            assert any(s.name == name for s in prop.subdivisions), f"subdivision {name!r} missing"
            assert parent == prop.name
        elif kind == "neighbor":
            assert any(n.survey_number == name for n in prop.neighbors), (
                f"neighbor {name!r} missing"
            )
            assert parent == prop.name


@then("an import report should be generated with")
def step_import_report(context):
    report = context.result.report()
    for row in context.table:
        metric, value = row["metric"], int(row["value"])
        assert report[metric] == value, f"{metric}: expected {value}, got {report[metric]}"
