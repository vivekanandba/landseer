Feature: Automation and notifications
  As a land buyer tracking many properties
  I want the system to surface expiries, price changes and stale leads
  So that I never miss a follow-up or a time-sensitive document

  Background:
    Given the system is initialized
    And I am logged in as a user

  Scenario: Alert on a significant price change
    Given a property "Moothakkal Plot" exists
    When the asking price changes to 1000000
    And the asking price changes to 1300000
    And I run the due notifications
    Then there should be a price change alert for "Moothakkal Plot"

  Scenario: Remind about an expiring document
    Given a property "Thuthikadu 171-4" exists
    And an EC document issued on "2020-01-15" is uploaded
    When I check notifications as of "2050-01-10"
    Then there should be an expiry reminder

  Scenario: Follow up on stale evaluations
    Given a property "Old Lead" exists
    When I check notifications as of "2027-01-01"
    Then there should be a follow-up for "Old Lead"

  Scenario: Import a property from a local folder
    Given a local folder with these files:
      | path                                  |
      | 1392-171-4-Patta.pdf                  |
      | 171-4A/171-4A-FMB.pdf                 |
      | Neighbors/171-3A8/171-3A8-Patta.pdf   |
    When I import "Thuthikadu" from that folder
    Then a property "Thuthikadu" should be created
    And the property should have 3 documents
