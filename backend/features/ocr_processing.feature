Feature: OCR processing
  As a land buyer with scanned documents
  I want key fields extracted and the OCR queue processed
  So that documents become searchable and verifiable

  Background:
    Given the system is initialized
    And I am logged in as a user

  Scenario: Parse fields from OCR text
    When I parse the OCR text:
      """
      Survey Number: 171-4
      Owner Name: Ramesh Kumar
      Extent: 12500 sqft
      Village: Thuthikadu
      """
    Then the parsed survey number should be "171-4"
    And the parsed owner name should be "Ramesh Kumar"

  Scenario: Process the OCR queue for uploaded documents
    Given a property "Thuthikadu 171-4" exists
    And a document "Patta.pdf" is uploaded
    When I process the OCR queue with extracted survey number "171-4"
    Then the document OCR status should be "complete"
    And the document survey number should be "171-4"
