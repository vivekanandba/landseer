Feature: Property Comparison
  As a land buyer evaluating multiple properties
  I want to compare them side-by-side
  So that I can make an informed purchasing decision

  Background:
    Given the system is initialized
    And I am logged in as a user
    And the following properties exist:
      | name              | location      | area_sqft | price_total | price_per_sqft | status       |
      | Thuthikadu 171-4  | Thuthikadu    | 12500     | 1850000     | 148            | shortlisted  |
      | Moothakkal Plot   | Moothakkal    | 10800     | 1600000     | 148            | evaluating   |
      | Kotikal Forest    | Kathalampattu | 112000    | 3500000     | 31             | evaluating   |

  Scenario: Create a comparison
    When I select the following properties for comparison:
      | name              |
      | Thuthikadu 171-4  |
      | Moothakkal Plot   |
      | Kotikal Forest    |
    And I create a comparison named "Top 3 Shortlist"
    Then the comparison should include 3 properties
    And the comparison should be saved

  Scenario: View comparison table
    Given I have a comparison "Top 3 Shortlist" with:
      | name              |
      | Thuthikadu 171-4  |
      | Moothakkal Plot   |
      | Kotikal Forest    |
    When I view the comparison
    Then I should see a table with columns:
      | column          |
      | Location        |
      | Area (sqft)     |
      | Total Price     |
      | Price per sqft  |
      | Status          |
      | Match Score     |
    And each property should be a row in the table

  Scenario: Compare document completion status
    Given the following document statuses:
      | property          | patta | fmb | ec  |
      | Thuthikadu 171-4  | ✅    | ✅  | ✅  |
      | Moothakkal Plot   | ✅    | ✅  | ⏳  |
      | Kotikal Forest    | ✅    | ✅  | ✅  |
    When I view the comparison
    Then the document status columns should show verification icons
    And "Moothakkal Plot" should show "⏳" for EC

  Scenario: Apply custom criteria weights
    Given I have a comparison with 3 properties
    When I set the following criteria weights:
      | criterion       | weight |
      | Location        | 30%    |
      | Price           | 25%    |
      | Area            | 20%    |
      | Document Status | 15%    |
      | Infrastructure  | 10%    |
    And I calculate weighted scores
    Then each property should have a total weighted score
    And properties should be ranked by score

  Scenario: Export comparison to PDF
    Given I have a comparison "Top 3 Shortlist"
    When I export the comparison to PDF
    Then a PDF file should be generated
    And it should contain the comparison table
    And it should include property photos
    And it should show match scores

  Scenario: Compare specific features
    Given the following property features:
      | property          | water_source | electricity | road_access | corner_plot |
      | Thuthikadu 171-4  | No           | Yes         | Yes         | No          |
      | Moothakkal Plot   | Yes          | Yes         | Yes         | No          |
      | Kotikal Forest    | Yes          | Nearby      | Kutcha      | Yes         |
    When I view feature comparison
    Then I should see which property has each feature
    And features should be color-coded (green=yes, yellow=partial, red=no)

  Scenario: Compare investment metrics
    Given I have properties with the following details:
      | property          | price_total | estimated_appreciation_3y | rental_yield |
      | Thuthikadu 171-4  | 1850000     | 15%                       | N/A          |
      | Moothakkal Plot   | 1600000     | 12%                       | N/A          |
      | Kotikal Forest    | 3500000     | 20%                       | N/A          |
    When I view investment comparison
    Then I should see ROI projections
    And appreciation estimates
    And total investment including registration costs

  Scenario: Save comparison for later
    Given I create a comparison "Weekend Review"
    When I save the comparison
    Then I should be able to retrieve it later
    And it should show the creation date
    And I can add notes to the comparison

  Scenario: Update comparison dynamically
    Given I have a comparison with 2 properties
    When I add a third property to the comparison
    Then the comparison table should update
    And all columns should reflect the new property
    And the comparison should be re-saved

  Scenario: Compare neighbor information
    Given properties have the following neighbors:
      | property          | neighbor_count | shared_boundaries |
      | Thuthikadu 171-4  | 6              | 4                 |
      | Moothakkal Plot   | 2              | 2                 |
      | Kotikal Forest    | 4              | 1                 |
    When I view the comparison
    Then I should see neighbor statistics
    And properties with more tracked neighbors should be highlighted

  Scenario: View match score breakdown
    Given a property "Thuthikadu 171-4" has match score 85%
    When I click on the match score in comparison
    Then I should see the breakdown:
      | criterion       | score | weight |
      | Location        | 95%   | 30%    |
      | Price           | 80%   | 25%    |
      | Size            | 90%   | 20%    |
      | Features        | 75%   | 15%    |
      | Infrastructure  | 70%   | 10%    |
    And I should see which criteria are strong/weak
