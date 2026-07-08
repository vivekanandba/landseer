Feature: OneDrive Data Import
  As a land buyer with existing research in OneDrive
  I want to import my property data automatically
  So that I don't lose any historical information

  Background:
    Given the system is initialized
    And I am logged in as a user
    And the OneDrive folder is "/TN Lands"

  Scenario: Import simple property folder
    Given a folder exists at "/TN Lands/Moothakkal"
    And it contains the following files:
      | filename | type |
      | Patta.pdf | patta |
      | FMB.pdf   | fmb   |
      | EC.pdf    | ec    |
    When I run the import for "Moothakkal"
    Then a property "Moothakkal" should be created
    And the property should have 3 documents
    And documents should be categorized as "patta", "fmb", and "ec"

  Scenario: Import property with subdivisions
    Given a folder exists at "/TN Lands/Thuthikadu"
    And it contains:
      | path                              | type      |
      | 1392-171-4-Patta.pdf             | patta     |
      | 171-4-EC-Kaniayambadi.pdf        | ec        |
      | 171-4A/171-4A-FMB.pdf            | fmb       |
      | 171-4C/171-4C-Integrated-Land-Record.pdf | land_record |
      | 171-4D/FMB-171-4D.pdf            | fmb       |
    When I run the import for "Thuthikadu"
    Then a property "Thuthikadu" should be created
    And the property should have 3 subdivisions: "171-4A", "171-4C", "171-4D"
    And subdivision "171-4A" should have 1 document
    And subdivision "171-4C" should have 1 document
    And subdivision "171-4D" should have 1 document

  Scenario: Import neighbor properties
    Given a folder exists at "/TN Lands/Thuthikadu/Neighbors"
    And it contains subfolders:
      | neighbor_folder | document_file                              |
      | 171-3A8         | 171-3A8-Integrated-Land-Records.pdf       |
      | 171-4B1         | 171-4B1-Integrated-Land-Records.pdf       |
      | 171-5A2         | 171-5A2-Patta.pdf                         |
    When I run the import for "Thuthikadu"
    Then the property should have 3 neighbors
    And neighbor "171-3A8" should have 1 document
    And neighbor "171-5A2" should have 1 document

  Scenario: Extract survey number from filename patterns
    Given the following files exist:
      | filename                      | expected_survey_number |
      | 1392-171-4-Patta.pdf         | 171-4                  |
      | FMB-171-4D.pdf               | 171-4D                 |
      | 171-4-EC-Kaniayambadi.pdf    | 171-4                  |
      | Patta-184.pdf                 | 184                    |
      | 119-4.pdf                     | 119-4                  |
    When I run survey number extraction
    Then all survey numbers should be correctly extracted

  Scenario: Import visual documents (images)
    Given a folder "/TN Lands/Kotikal Forest" contains:
      | filename                            | type  |
      | Cultivated-Crops.png               | photo |
      | Govt-Land-Boundary-North.png       | photo |
      | GuidelineValue.png                  | photo |
      | Soil-Health-Card.pdf                | document |
    When I run the import
    Then the property should have 3 photos
    And the property should have 1 document

  Scenario: Handle OneNote exports
    Given a file "/TN Lands/Thuthikadu/Thuthikadu-OneNote.pdf" exists
    When I run the import
    Then the file should be categorized as "notes"
    And it should be linked to the property "Thuthikadu"
    And OCR should extract text for search indexing

  Scenario: Import multiple properties in batch
    Given the following folders exist under "/TN Lands":
      | folder_name    | file_count |
      | Moothakkal     | 3          |
      | Thuthikadu     | 8          |
      | Kotikal Forest | 14         |
      | Irumbli        | 4          |
    When I run batch import for all folders
    Then 4 properties should be created
    And a total of 29 documents should be imported
    And an import summary should be generated

  Scenario: Handle duplicate imports gracefully
    Given a property "Moothakkal" already exists in the system
    And it has 3 documents
    When I run the import again for "Moothakkal"
    Then the system should detect existing property
    And it should only import new documents
    And it should not create duplicate records

  Scenario: Sync folder structure to property hierarchy
    Given the folder structure:
      """
      /TN Lands/Thuthikadu/
        171-4-Patta.pdf
        171-4A/
          171-4A-FMB.pdf
        171-4C/
          FMB-171-4C.pdf
        Neighbors/
          171-3A8/
            171-3A8-Integrated-Land-Records.pdf
      """
    When I run structured import
    Then the database should mirror this hierarchy:
      | type        | name      | parent          |
      | property    | Thuthikadu | -              |
      | subdivision | 171-4A    | Thuthikadu     |
      | subdivision | 171-4C    | Thuthikadu     |
      | neighbor    | 171-3A8   | Thuthikadu     |

  Scenario: Generate import report
    When I complete an import of "Thuthikadu"
    Then an import report should be generated with:
      | metric                  | value |
      | properties_created      | 1     |
      | subdivisions_created    | 3     |
      | neighbors_tracked       | 6     |
      | documents_imported      | 8     |
      | photos_imported         | 0     |
      | ocr_jobs_queued         | 8     |
