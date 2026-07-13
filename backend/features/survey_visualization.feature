Feature: Survey Visualization
  As a land buyer mapping plots in Vellore
  I want to import survey boundaries and generate maps
  So that I can see a property and its neighbors on a map

  Background:
    Given the system is initialized
    And I am logged in as a user

  Scenario: Import survey vertices for a property
    Given a property "Thuthikadu 171-4" exists
    When I import a survey boundary with vertices:
      | lat     | lng     |
      | 12.9001 | 79.1001 |
      | 12.9005 | 79.1001 |
      | 12.9005 | 79.1010 |
      | 12.9001 | 79.1010 |
    Then the property should have a survey boundary
    And the boundary should have 4 vertices

  Scenario: Generate a KML file for a property
    Given a property "Thuthikadu 171-4" exists with a survey boundary
    When I generate the KML for the property
    Then a KML file should be generated
    And the KML coordinates should be in lng,lat order

  Scenario: Neighbor boundaries are layered on the map
    Given a property "Thuthikadu 171-4" exists with a survey boundary
    And a neighbor "171-3A8" has a survey boundary
    When I build the map data for the property
    Then the map should include 2 boundaries
    And the neighbor boundary should be styled differently from the subject
