Feature: Broker Management
  As a land buyer
  I want to track brokers and their property listings
  So that I can evaluate broker performance and manage commissions

  Background:
    Given the system is initialized
    And I am logged in as a user

  Scenario: Add a new broker
    When I create a broker with the following details:
      | field             | value                  |
      | name              | Rajesh Kumar           |
      | phone             | +919876543210          |
      | email             | rajesh@example.com     |
      | areas_covered     | Vellore,Katpadi        |
      | commission_rate   | 2.0                    |
    Then the broker "Rajesh Kumar" should exist
    And the broker should cover "Vellore" and "Katpadi"

  Scenario: Link broker to a property
    Given a broker "Rajesh Kumar" exists
    And a property "Moothakkal Plot" exists
    When I link the broker to the property with:
      | field          | value      |
      | shown_date     | 2025-11-28 |
      | asking_price   | 2500000    |
      | broker_notes   | Good location, owner motivated |
    Then the broker should be linked to the property
    And the asking price should be recorded as 2500000

  Scenario: Track multiple brokers for same property
    Given a property "Kotikal Forest" exists
    And the following brokers exist:
      | name          |
      | Rajesh Kumar  |
      | Suresh Babu   |
      | Kumar Swamy   |
    When I link "Rajesh Kumar" to the property on "2025-11-20"
    And I link "Suresh Babu" to the property on "2025-11-25"
    Then the property should have 2 brokers
    And "Rajesh Kumar" should be the first broker to show it

  Scenario: Calculate broker commission
    Given a broker "Rajesh Kumar" with commission rate 2.0%
    And a property "Moothakkal" with negotiated price 2200000
    When I calculate the broker commission
    Then the commission should be 44000

  Scenario: View broker performance metrics
    Given a broker "Rajesh Kumar" exists
    And the broker has shown 10 properties
    And 3 properties are marked as "shortlisted"
    And 1 property is marked as "purchased"
    When I view the broker performance
    Then the conversion rate should be 10%
    And the shortlist rate should be 30%

  Scenario: Search brokers by area
    Given the following brokers exist:
      | name          | areas_covered        |
      | Rajesh Kumar  | Vellore,Katpadi      |
      | Suresh Babu   | Ranipet,Arcot        |
      | Kumar Swamy   | Vellore,Ranipet      |
    When I search for brokers covering "Vellore"
    Then I should see 2 brokers
    And the brokers should be "Rajesh Kumar" and "Kumar Swamy"
