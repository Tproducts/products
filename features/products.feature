Feature: The product store service back-end
    As a Product Store Owner
    I need a RESTful catalog service
    So that I can keep track of all my products

Background:
    Given the following products
        |   name       |  category  | price | stock  |   description  |
        | iPhone       |   Phone    | 1099  |   3    |     test 1     |
        | Macbook Air  |   Laptop   | 1299  |   5    |     test 2     |
        | AirPods      |  Earphone  |  99   |   10   |     test 3     |

Scenario: The server is running
    When I visit the "Home Page"
    Then I should see "Product RESTful Service" in the title
    And I should not see "404 Not Found"

Scenario: Create a Product
    When I visit the "Home Page"
    And I set the "Name" to "iPad Pro"
    And I set the "Category" to "Pad"
    And I set the "Price" to "999"
    And I set the "Stock" to "10"
    And I set the "Description" to "iPad test"
    And I press the "Create" button
    Then I should see the message "Success"
    When I copy the "Id" field
    And I press the "Clear" button
    Then the "Id" field should be empty
    And the "Name" field should be empty
    And the "Category" field should be empty
    When I paste the "Id" field
    And I press the "Retrieve" button
    Then I should see "iPad Pro" in the "Name" field
    And I should see "Pad" in the "Category" field
    And I should see "999" in the "Price" field
    And I should see "10" in the "Stock" field
    And I should see "iPad test" in the "Description" field

Scenario: List all products
    When I visit the "Home Page"
    And I press the "Search" button
    Then I should see "iPhone" in the results
    And I should see "Macbook Air" in the results
    And I should not see "Apple TV" in the results

Scenario: Search for phones
    When I visit the "Home Page"
    And I set the "Category" to "Phone"
    And I press the "Search" button
    Then I should see "iPhone" in the results
    And I should not see "Macbook Air" in the results
    And I should not see "Apple TV" in the results

Scenario: Update a Product
    When I visit the "Home Page"
    And I set the "Name" to "Macbook Air"
    And I press the "Search" button
    Then I should see "Macbook Air" in the "Name" field
    And I should see "Laptop" in the "Category" field
    When I change "Name" to "Macbook Pro"
    And I press the "Update" button
    Then I should see the message "Success"
    When I copy the "Id" field
    And I press the "Clear" button
    And I paste the "Id" field
    And I press the "Retrieve" button
    Then I should see "Macbook Pro" in the "Name" field
    When I press the "Clear" button
    And I press the "Search" button
    Then I should see "Macbook Pro" in the results
    Then I should not see "Macbook Air" in the results

Scenario: Delete a Product
    When I visit the "Home Page"
    And I press the "Search" button
    Then I should see "iPhone" in the results
    When I copy the "Id" field
    And I press the "Clear" button
    And I paste the "Id" field
    And I press the "Delete" button
    Then I should see the message "Product has been Deleted!"
    When I press the "Clear" button
    And I press the "Search" button
    Then I should not see "iPhone" in the results