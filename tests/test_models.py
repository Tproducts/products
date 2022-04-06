"""
Product Test Suite

Test cases can be run with the following:
nosetests -v --with-spec --spec-color
nosetests --stop tests/test_products.py:TestProducts
"""

import os
import logging
import json
from datetime import date
from unittest import TestCase
from unittest.mock import MagicMock, patch
from requests import HTTPError, ConnectionError
from service.models import Product, DataValidationError, DatabaseConnectionError
from tests.factories import ProductFactory

# cspell:ignore VCAP SQLDB
VCAP_SERVICES = {
    "cloudantNoSQLDB": [
        {
            "credentials": {
                "username": "admin",
                "password": "pass",
                "host": "localhost",
                "port": 5984,
                "url": "http://admin:pass@localhost:5984",
            }
        }
    ]
}

VCAP_NO_SERVICES = {"noCloudant": []}

BINDING_CLOUDANT = {
    "username": "admin",
    "password": "pass",
    "host": "localhost",
    "port": 5984,
    "url": "http://admin:pass@localhost:5984",
}

######################################################################
#  T E S T   C A S E S
######################################################################
class TestProductModel(TestCase):
    """Test Cases for Product Model"""

    def setUp(self):
        """Initialize the Cloudant database"""
        Product.init_db("test")
        Product.remove_all()

    def _create_products(self, count: int) -> list:
        """Creates a collection of products in the database"""
        product_collection = []
        for _ in range(count):
            product = ProductFactory()
            product.create()
            product_collection.append(product)
        return product_collection
    
    def test_repr(self):
        product = Product("iPhone13 Pro Max", "Phone", True, 1099, "This is a test data", 1)
        self.assertEqual(repr(product), "<Product iPhone13 Pro Max id=[None]>")

    def test_create_a_product(self):
        """Create a product and assert that it exists"""
        product = Product("iPhone13 Pro Max", "Phone", True, 1099, "This is a test data", 1)
        self.assertNotEqual(product, None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "iPhone13 Pro Max")
        self.assertEqual(product.category, "Phone")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 1099)
        self.assertEqual(product.description, "This is a test data")
        self.assertEqual(product.stock, 1)

    def test_add_a_product(self):
        """Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        logging.debug("Product: %s", product.serialize())
        self.assertNotEqual(product, None)
        self.assertEqual(product.id, None)
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertNotEqual(product.id, None)
        products = Product.all()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].name, product.name)
        self.assertEqual(products[0].category, product.category)
        self.assertEqual(products[0].available, product.available)
        self.assertEqual(products[0].price, product.price)
        self.assertEqual(products[0].description, product.description)
        self.assertEqual(products[0].stock, product.stock)

    def test_update_a_product(self):
        """Update a Product"""
        product = ProductFactory()
        logging.debug("Product: %s", product.serialize())
        product.create()
        self.assertNotEqual(product.id, None)
        # Change it an save it
        product.category = "NewCategory"
        product.update()
        # Fetch it back and make sure the id hasn't changed
        # but the data did change
        products = Product.all()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].category, "NewCategory")
        self.assertEqual(products[0].name, product.name)

    def test_delete_a_product(self):
        """Delete a Product"""
        product = ProductFactory()
        logging.debug("Product: %s", product.serialize())
        product.create()
        self.assertEqual(len(Product.all()), 1)
        # delete the product and make sure it isn't in the database
        product.delete()
        self.assertEqual(len(Product.all()), 0)

    def test_serialize_a_product(self):
        """Serialize a Product"""
        product = ProductFactory()
        data = product.serialize()
        logging.debug("Product data: %s", data)
        self.assertNotEqual(data, None)
        self.assertNotIn("_id", data)
        self.assertEqual(data["name"], product.name)
        self.assertEqual(data["category"], product.category)
        self.assertEqual(data["available"], product.available)
        self.assertEqual(data["price"], product.price)
        self.assertEqual(data["description"], product.description)
        self.assertEqual(data["stock"], product.stock)

    def test_deserialize_a_product(self):
        """Deserialize a Product"""
        data = ProductFactory().serialize()
        logging.debug("Product data: %s", data)
        product = Product()
        product.deserialize(data)
        self.assertNotEqual(product, None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, data["name"])
        self.assertEqual(product.category, data["category"])
        self.assertEqual(product.available, data["available"])
        self.assertEqual(product.price, data["price"])
        self.assertEqual(product.description, data["description"])
        self.assertEqual(product.stock, data["stock"])

    def test_deserialize_with_no_name(self):
        """Deserialize a Product that has no name"""
        data = {"id": 0, "category": "Phone"}
        product = Product()
        self.assertRaises(DataValidationError, product.deserialize, data)

    def test_deserialize_with_no_data(self):
        """Deserialize a Product that has no data"""
        product = Product()
        self.assertRaises(DataValidationError, product.deserialize, None)

    def test_deserialize_with_bad_data(self):
        """Deserialize a Product that has bad data"""
        product = Product()
        self.assertRaises(DataValidationError, product.deserialize, "string data")
    
    def test_deserialize_with_invalid_type_available(self):
        """Deserialize a Product that is not available"""
        data = Product("iPhone13 Pro Max", "Phone", "ABC", 1099, "This is a test data", 1).serialize()
        product = Product() 
        self.assertRaises(DataValidationError, product.deserialize, data)
    
    def test_save_a_product_with_no_name(self):
        """Save a Product with no name"""
        product = Product(None, "Phone")
        self.assertRaises(DataValidationError, product.create)

    def test_create_a_product_with_no_name(self):
        """Create a Product with no name"""
        product = Product(None, "Phone")
        self.assertRaises(DataValidationError, product.create)

    def test_find_product(self):
        """Find a Product by id"""
        products = self._create_products(5)
        saved_product = products[0]
        product = Product.find(saved_product.id)
        self.assertIsNot(product, None)
        self.assertEqual(product.id, saved_product.id)
        self.assertEqual(product.name, saved_product.name)
        self.assertEqual(product.category, saved_product.category)
        self.assertEqual(product.available, saved_product.available)
        self.assertEqual(product.price, saved_product.price)
        self.assertEqual(product.description, saved_product.description)
        self.assertEqual(product.stock, saved_product.stock)

    def test_find_with_no_products(self):
        """Find a Product with empty database"""
        product = Product.find("emptyTest")
        self.assertIs(product, None)

    def test_product_not_found(self):
        """Find a Product that doesn't exist"""
        ProductFactory().create()
        product = Product.find("notExist")
        self.assertIs(product, None)

    def test_find_by_name(self):
        """Find a Product by Name"""
        self._create_products(5)
        saved_product = ProductFactory()
        saved_product.name = "iPad"
        saved_product.create()
        # search by name
        products = Product.find_by_name("iPad")
        self.assertNotEqual(len(products), 0)
        product = products[0]
        self.assertEqual(product.name, "iPad")
        self.assertEqual(product.category, saved_product.category)
        self.assertEqual(product.available, saved_product.available)
        self.assertEqual(product.price, saved_product.price)
        self.assertEqual(product.description, saved_product.description)
        self.assertEqual(product.stock, saved_product.stock)

    def test_find_by_category(self):
        """Find a Product by Category"""
        products = self._create_products(5)
        category = products[0].category
        category_count =  len([product for product in products if product.category == category])
        logging.debug("Looking for %d Products in category %s", category_count, category)
        found_products = Product.find_by_category(category)
        self.assertEqual(len(found_products), category_count)
        for product in found_products:
            self.assertEqual(product.category, category)

    def test_find_by_availability(self):
        """Find a Product by Availability"""
        products = self._create_products(5)
        available = products[0].available
        available_count = len([product for product in products if product.available == available])
        logging.debug("Looking for %d Products where availabe is %s", available_count, available)
        found_products = Product.find_by_availability(available)
        self.assertEqual(len(found_products), available_count)
        for product in found_products:
            self.assertEqual(product.available, available)

    def test_create_query_index(self):
        """Test create query index"""
        self._create_products(5)
        Product.create_query_index("category")

    def test_disconnect(self):
        """Test Disconnect"""
        Product.disconnect()
        product = ProductFactory()
        self.assertRaises(AttributeError, product.create)

    def test_connect(self):
        """Test Connect"""
        Product.connect()

    @patch("cloudant.database.CloudantDatabase.create_document")
    def test_http_error(self, bad_mock):
        """Test a Bad Create with HTTP error"""
        bad_mock.side_effect = HTTPError()
        product = ProductFactory()
        product.create()
        self.assertIsNone(product.id)

    @patch("cloudant.document.Document.exists")
    def test_document_not_exist(self, bad_mock):
        """Test a Bad Document Exists"""
        bad_mock.return_value = False
        product = ProductFactory()
        product.create()
        self.assertIsNone(product.id)

    @patch("cloudant.database.CloudantDatabase.__getitem__")
    def test_key_error_on_update(self, bad_mock):
        """Test KeyError on update"""
        bad_mock.side_effect = KeyError()
        product = ProductFactory()
        product.create()
        product.name = "KeyErrorTest"
        product.update()

    @patch("cloudant.database.CloudantDatabase.__getitem__")
    def test_key_error_on_delete(self, bad_mock):
        """Test KeyError on delete"""
        bad_mock.side_effect = KeyError()
        product = ProductFactory()
        product.create()
        product.delete()

    @patch("cloudant.client.Cloudant.__init__")
    def test_connection_error(self, bad_mock):
        """Test Connection error handler"""
        bad_mock.side_effect = ConnectionError()
        self.assertRaises(DatabaseConnectionError, Product.init_db, "test")

    # @patch.dict(os.environ, {'VCAP_SERVICES': json.dumps(VCAP_SERVICES)})
    # def test_vcap_services(self):
    #     """ Test if VCAP_SERVICES works """
    #     Product.init_db("test")
    #     self.assertIsNotNone(Product.client)

    # @patch.dict(os.environ, {'VCAP_SERVICES': json.dumps(VCAP_NO_SERVICES)})
    # def test_vcap_no_services(self):
    #     """ Test VCAP_SERVICES without Cloudant """
    #     Pet.init_db("test")
    #     self.assertIsNotNone(Pet.client)
    #     self.assertIsNotNone(Pet.database)
    
    # @patch.dict(os.environ, {'VCAP_SERVICES': json.dumps(VCAP_NO_SERVICES),
    #                          'BINDING_CLOUDANT': json.dumps(BINDING_CLOUDANT)})
    # def test_vcap_with_binding(self):
    #     """ Test no VCAP_SERVICES with BINDING_CLOUDANT """
    #     Pet.init_db("test")
    #     self.assertIsNotNone(Pet.client)
    #     self.assertIsNotNone(Pet.database)
    
    # @patch.dict(os.environ, {'BINDING_CLOUDANT': json.dumps(BINDING_CLOUDANT)})
    # def test_vcap_no_services(self):
    #     """ Test BINDING_CLOUDANT """
    #     Pet.init_db("test")
    #     self.assertIsNotNone(Pet.client)
    #     self.assertIsNotNone(Pet.database)