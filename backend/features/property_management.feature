Feature: Property Management
  As a land buyer in Vellore
  I want to manage properties I'm evaluating
  So that I can organize my land search effectively

  Background:
    Given the system is initialized
    And I am logged in as a user

  Scenario: Create a new property
    When I create a property with the following details:
      | field          | value                    |
      | name           | Thuthikadu 171-4        |
      | survey_number  | 171-4                   |
      | location       | Thuthikadu              |
      | taluk          | Vellore                 |
      | total_area_sqft| 12500                   |
      | asking_price   | 1850000                 |
    Then the property "Thuthikadu 171-4" should exist
    And the property should have survey number "171-4"
    And the property should be in status "evaluating"

  Scenario: Add subdivisions to a property
    Given a property "Thuthikadu 171-4" exists
    When I add the following subdivisions:
      | name | survey_number_full | area_sqft |
      | 4A   | 171-4A             | 4200      |
      | 4C   | 171-4C             | 4100      |
      | 4D   | 171-4D             | 4200      |
    Then the property should have 3 subdivisions
    And the total subdivision area should be 12500 sqft

  Scenario: Track neighbor properties
    Given a property "Thuthikadu 171-4" exists
    When I add the following neighbors:
      | survey_number | direction | notes                    |
      | 171-3A8       | north     | Agricultural land        |
      | 171-4B1       | east      | Residential plot         |
      | 171-5A2       | south     | Has shared boundary      |
    Then the property should have 3 neighbors tracked
    And neighbor "171-3A8" should be to the "north"

  Scenario: Update property status
    Given a property "Moothakkal" exists with status "evaluating"
    When I update the property status to "shortlisted"
    Then the property status should be "shortlisted"
    And the update should be logged in the activity timeline

  Scenario: Search properties by location
    Given the following properties exist:
      | name              | location      | status       |
      | Thuthikadu 171-4  | Thuthikadu    | shortlisted  |
      | Moothakkal Plot   | Moothakkal    | evaluating   |
      | Kotikal Forest    | Kathalampattu | rejected     |
    When I search for properties in "Thuthikadu"
    Then I should see 1 property
    And the property should be "Thuthikadu 171-4"

  Scenario: Filter properties by price range
    Given the following properties exist:
      | name              | asking_price |
      | Thuthikadu 171-4  | 1850000      |
      | Moothakkal Plot   | 1600000      |
      | Kotikal Forest    | 3500000      |
    When I filter properties with price between 1500000 and 2000000
    Then I should see 2 properties
    And the properties should include "Thuthikadu 171-4" and "Moothakkal Plot"
