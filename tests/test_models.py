"""
Test cases for Product Model

Test cases can be run with:
    nosetests

"""
from itertools import product
import os
import logging
from sqlite3 import InternalError
from unicodedata import category, name
import unittest
from unittest import TestCase
from unittest.mock import MagicMock, patch
from requests import HTTPError, ConnectionError
from sqlalchemy import null
from werkzeug.exceptions import NotFound
from service.models import Product, DataValidationError, db, DatabaseConnectionError
from service import app
from .factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/testdb"
)

######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.drop_all()  # clean up the last tests
        db.create_all()  # make our sqlalchemy tables

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()
        db.drop_all()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """Create a product and assert that it exists"""
        product = Product(name="iPhone", category="Phone", description="this is test product", price=1099, stock=5)
        self.assertTrue(product != None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "iPhone")
        self.assertEqual(product.category, "Phone")
        self.assertEqual(product.description, "this is test product")
        self.assertEqual(product.price, 1099)
        self.assertEqual(product.stock, 5)
        self.assertEqual(product.__repr__(), "<Product %r id=[%s]>" % (product.name, product.id))

    def test_add_a_product(self):
        """Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = Product(name="iPhone", category="Phone", description="this is test product", price=1099, stock=5)
        self.assertTrue(product != None)
        self.assertEqual(product.id, None)
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertEqual(product.id, 1)
        products = Product.all()
        self.assertEqual(len(products), 1)

    def test_update_a_product(self):
        """Update a Product"""
        product = ProductFactory()
        logging.debug(product)
        product.create()
        logging.debug(product)
        self.assertEqual(product.id, 1)
        # Change the price to 500, test whether we can save it
        product.price = 500
        original_id = product.id
        product.update()
        self.assertEqual(product.id, original_id)
        self.assertEqual(product.price, 500)
        # Fetch it back and make sure the id hasn't changed
        # but the data did change
        products = Product.all()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].id, 1)
        self.assertEqual(products[0].price, 500)

    #def test_update_empty_id_product(self):
    #    """Update a empty id product"""
    #    Product(id = null, name="iPhone8 Plus", description="test1", price=100).create()
    #    self.assertRaises(DataValidationError, Product.update, Product)

    def test_delete_a_product(self):
        """Delete a Product"""
        product = ProductFactory()
        product.create()
        self.assertEqual(len(Product.all()), 1)
        # delete the product and make sure it isn't in the database
        product.delete()
        self.assertEqual(len(Product.all()), 0)

    def test_serialize_a_product(self):
        """Test serialization of a Product"""
        product = ProductFactory()
        data = product.serialize()
        self.assertNotEqual(data, None)
        self.assertIn("id", data)
        self.assertEqual(data["id"], product.id)
        self.assertIn("name", data)
        self.assertEqual(data["name"], product.name)
        self.assertIn("category", data)
        self.assertEqual(data["category"], product.category)
        self.assertIn("description", data)
        self.assertEqual(data["description"], product.description)
        self.assertIn("price", data)
        self.assertEqual(data["price"], product.price)
        self.assertIn("stock", data)
        self.assertEqual(data["stock"], product.stock)

    def test_deserialize_a_product(self):
        """Test deserialization of a Product"""
        data = {
            "id": "1",
            "name": "Macbook Air",
            "category": "Laptop",
            "price": "666",
            "stock": "3",
            "description": "This product is used for test"
        }
        product = Product()
        product.deserialize(data)
        self.assertNotEqual(product, None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Macbook Air")
        self.assertEqual(product.category, "Laptop")
        self.assertEqual(product.description, "This product is used for test")
        self.assertEqual(product.price, 666)
        self.assertEqual(product.stock, 3)

    def test_deserialize_missing_data(self):
        """Test deserialization of a Product with missing data"""
        data = {"id": 1, "name": "Macbook Air", "category":"Laptop", "description": "This product is used for test"}
        product = Product()
        self.assertRaises(DataValidationError, product.deserialize, data)

    def test_deserialize_bad_data(self):
        """Test deserialization of bad data"""
        data = "this is not a bad data"
        product = Product()
        self.assertRaises(DataValidationError, product.deserialize, data)

    def test_deserialize_bad_price(self):
        """ Test deserialization of bad price attribute """
        product = Product()
        data = product.serialize()
        data["price"] = "wrong" # wrong case
        self.assertRaises(DataValidationError, product.deserialize, data)

    def test_find_product(self):
        """Find a Product by ID"""
        products = ProductFactory.create_batch(3)
        for product in products:
            product.create()
        logging.debug(products)
        # make sure they got saved
        self.assertEqual(len(Product.all()), 3)
        # find the 2nd product in the list
        product = Product.find(products[1].id)
        self.assertIsNot(product, None)
        self.assertEqual(product.id, products[1].id)
        self.assertEqual(product.name, products[1].name)
        self.assertEqual(product.category, products[1].category)
        self.assertEqual(product.description, products[1].description)
        self.assertEqual(product.price, products[1].price)
        self.assertEqual(product.stock, products[1].stock)

    def test_find_by_name(self):
        """Find a Product by Name"""
        Product(name="iPhone8 Plus", category="Phone", description="test1", price=100, stock=1).create()
        Product(name="iPad Pro", category="Pad", description="test2", price=200, stock=2).create()
        products = Product.find_by_name("iPhone8 Plus")
        self.assertEqual(products[0].name, "iPhone8 Plus")
        self.assertEqual(products[0].category, "Phone")
        self.assertEqual(products[0].description, "test1")
        self.assertEqual(products[0].price, 100)
        self.assertEqual(products[0].stock, 1)

    def test_find_or_404_found(self):
        """Find or return 404 found"""
        products = ProductFactory.create_batch(3)
        for product in products:
            product.create()

        product = Product.find_or_404(products[1].id)
        self.assertIsNot(product, None)
        self.assertEqual(product.id, products[1].id)
        self.assertEqual(product.name, products[1].name)
        self.assertEqual(product.category, products[1].category)
        self.assertEqual(product.description, products[1].description)
        self.assertEqual(product.price, products[1].price)
        self.assertEqual(product.stock, products[1].stock)

    def test_find_or_404_not_found(self):
        """Find or return 404 NOT found"""
        self.assertRaises(NotFound, Product.find_or_404, 0)

    def test_show_function(self):
        """Test show function"""
        product = ProductFactory()
        product.show()

    @patch('service.models.Product.init_db')
    def test_connection_error(self, bad_mock):
        """Test Connection error handler"""
        bad_mock.side_effect = DatabaseConnectionError()
        print(bad_mock.get_json())
        self.assertRaises(DatabaseConnectionError, Product.init_db)
