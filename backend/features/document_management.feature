Feature: Document Management
  As a land buyer
  I want to store and verify property documents
  So that I can ensure clear title and legal compliance

  Background:
    Given the system is initialized
    And I am logged in as a user
    And a property "Thuthikadu 171-4" exists

  Scenario: Upload Patta document
    When I upload a document "171-4-Patta.pdf" for the property
    Then the document should be categorized as "patta"
    And the document should be linked to the property
    And OCR should be triggered automatically

  Scenario: Auto-categorize documents by filename
    When I upload the following documents:
      | filename                      | expected_type |
      | 171-4-Patta.pdf              | patta         |
      | FMB-171-4A.pdf               | fmb           |
      | EC.pdf                        | ec            |
      | Mother-Deed.pdf               | deed          |
      | 171-4D-Integrated-Land-Record.pdf | land_record |
    Then all documents should be correctly categorized

  Scenario: Link document to subdivision
    Given a subdivision "171-4A" exists
    When I upload "171-4A-FMB.pdf"
    Then the document should be linked to subdivision "171-4A"
    And the document should also be linked to the parent property

  Scenario: Extract data from Patta using OCR
    When I upload "Patta.pdf" which contains:
      | field          | value              |
      | survey_number  | 171-4              |
      | owner_name     | Ramesh Kumar       |
      | extent         | 12500 sqft         |
      | village        | Thuthikadu         |
    Then OCR should extract survey number as "171-4"
    And OCR should extract owner name as "Ramesh Kumar"
    And OCR should extract extent as "12500 sqft"

  Scenario: Verify document checklist
    Given a property "Thuthikadu 171-4" exists
    When I check the document verification status
    Then the checklist should show:
      | document_type | status  |
      | patta         | missing |
      | fmb           | missing |
      | ec            | missing |
    When I upload "Patta.pdf", "FMB.pdf", and "EC.pdf"
    Then the checklist should show:
      | document_type | status   |
      | patta         | verified |
      | fmb           | verified |
      | ec            | verified |

  Scenario: Detect document expiry
    When I upload an EC document with issue date "2020-01-15"
    Then the document should show as "valid"
    When the current date is "2051-01-20"
    Then the document should show as "expired"
    And I should receive an expiry alert

  Scenario: Cross-verify survey numbers across documents
    Given the following documents are uploaded:
      | filename    | extracted_survey_number |
      | Patta.pdf   | 171-4                   |
      | FMB.pdf     | 171-4                   |
      | EC.pdf      | 171-5                   |
    When I run cross-verification
    Then a mismatch alert should be raised for "EC.pdf"
    And the verification status should be "issues_found"

  Scenario: Search documents by OCR text
    Given multiple documents are uploaded with OCR completed
    When I search for "Ramesh Kumar" in documents
    Then I should find all documents containing that name
    And the results should highlight matching text

  Scenario: Track document upload history
    When I upload "Patta-v1.pdf" on "2025-11-28"
    And I upload "Patta-v2.pdf" on "2025-12-05"
    Then the property should have 2 Patta documents
    And the latest version should be "Patta-v2.pdf"
    And the version history should be tracked
