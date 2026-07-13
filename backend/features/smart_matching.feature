Feature: Smart Matching
  As a land buyer with specific requirements
  I want properties scored and ranked against my preferences
  So that I can focus on the best-fit land and avoid deal-breakers

  Background:
    Given the system is initialized
    And I am logged in as a user

  Scenario: Define property requirements
    When I define my requirements:
      | field         | value                 |
      | name          | My Ideal Plot         |
      | budget_max    | 2000000               |
      | size_min_sqft | 10000                 |
      | locations     | Thuthikadu,Moothakkal |
    Then a preference "My Ideal Plot" should exist
    And the preference budget should be 2000000

  Scenario: Auto-score properties against preferences
    Given the following properties exist:
      | name             | location      | area_sqft | price_total | price_per_sqft |
      | Thuthikadu 171-4 | Thuthikadu    | 12500     | 1850000     | 148            |
      | Kotikal Forest   | Kathalampattu | 112000    | 3500000     | 31             |
    And a preference "Budget Buyer" with budget 4000000
    When I score the properties against "Budget Buyer"
    Then each property should have a match score between 0 and 100

  Scenario: Deal-breaker detection excludes an over-budget property
    Given the following properties exist:
      | name            | location   | area_sqft | price_total | price_per_sqft |
      | Affordable Plot | Thuthikadu | 10000     | 1500000     | 150            |
      | Pricey Estate   | Thuthikadu | 50000     | 5000000     | 100            |
    And a preference "Tight Budget" with budget 2000000
    When I get recommendations for "Tight Budget"
    Then "Pricey Estate" should be disqualified
    And the disqualification reason should mention "budget"
    And "Affordable Plot" should not be disqualified

  Scenario: Recommendations are ranked best-first
    Given the following properties exist:
      | name          | location   | area_sqft | price_total | price_per_sqft |
      | Cheap PerSqft | Thuthikadu | 100000    | 3000000     | 30             |
      | Dear PerSqft  | Thuthikadu | 10000     | 2000000     | 200            |
    And a preference "Value Seeker" with budget 4000000
    When I get recommendations for "Value Seeker"
    Then "Cheap PerSqft" should be the top recommendation
    And the recommendations should be ranked by score
