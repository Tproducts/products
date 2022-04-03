"""
Product API Service Test Suite

Test cases can be run with the following:
nosetests -v --with-spec --spec-color
nosetests --stop tests/test_service.py:TestProductServer
"""

from unittest import TestCase
import logging
from urllib.parse import quote_plus
from werkzeug.datastructures import MultiDict, ImmutableMultiDict
from service import routes
from service.utils import status
from tests.factories import ProductFactory

# Disable all but critical errors during normal test run
# uncomment for debugging failing tests
logging.disable(logging.CRITICAL)

BASE_URL = "/products"
CONTENT_TYPE_JSON = "application/json"

######################################################################
#  T E S T   C A S E S
######################################################################
class TestProductRoutes(TestCase):
    """Product Service tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        routes.initialize_logging(logging.INFO)
        routes.init_db("test")

    def setUp(self):
        self.app = routes.app.test_client()
        routes.app.config["TESTING"] = True
        routes.data_reset()


    ############################################################
    # Utility function to bulk create products
    ############################################################
    def _create_products(self, count: int = 1) -> list:
        """Factory method to create products in bulk"""
        products = []
        for _ in range(count):
            test_product = ProductFactory()
            resp = self.app.post(
                BASE_URL, json=test_product.serialize(), content_type=CONTENT_TYPE_JSON
            )
            self.assertEqual(
                resp.status_code, status.HTTP_201_CREATED, "Could not create test product"
            )
            new_product = resp.get_json()
            test_product.id = new_product["_id"]
            products.append(test_product)
        return products


    ############################################################
    #  T E S T   C A S E S
    ############################################################
    def test_index(self):
        """Test the index page"""
        resp = self.app.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn(b"Product Demo REST API Service", resp.data)

    def test_get_product_list(self):
        """Get a list of Products"""
        self._create_products(5)
        resp = self.app.get(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(len(resp.data) > 0)

    def test_get_product(self):
        """get a single Product"""
        test_product = self._create_products()[0]
        resp = self.app.get(
            f"{BASE_URL}/{test_product.id}", content_type=CONTENT_TYPE_JSON
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        logging.debug("Response data = %s", data)
        self.assertEqual(data["name"], test_product.name)

    def test_get_product_not_found(self):
        """Get a Product that doesn't exist"""
        resp = self.app.get(f"{BASE_URL}/foo")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        data = resp.get_json()
        logging.debug("Response data = %s", data)
        self.assertIn("was not found", data["message"])

    def test_create_product(self):
        """Create a new Product"""
        test_product = ProductFactory()
        logging.debug("Test Product: %s", test_product.serialize())
        resp = self.app.post(
            BASE_URL, json=test_product.serialize(), content_type=CONTENT_TYPE_JSON
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = resp.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_product = resp.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["category"], test_product.category)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["price"], test_product.price)
        self.assertEqual(new_product["description"], test_product.description)

        # Check that the location header was correct
        resp = self.app.get(location, content_type=CONTENT_TYPE_JSON)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        new_product = resp.get_json()
        self.assertEqual(new_product["name"], test_product.name, "Names do not match")
        self.assertEqual(new_product["category"], test_product.category)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["price"], test_product.price)
        self.assertEqual(new_product["description"], test_product.description)

    def test_create_product_from_formdata(self):
        """Test processing FORM data"""
        product = ProductFactory().serialize()
        product_data = MultiDict()
        product_data.add("name", product["name"])
        product_data.add("category", product["category"])
        product_data.add("available", product["available"])
        product_data.add("price", product["price"])
        product_data.add("description", product["description"])
        data = ImmutableMultiDict(product_data)
        logging.debug("Sending Product data: %s", data)
        resp = self.app.post(BASE_URL, data=data, content_type="application/x-www-form-urlencoded")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        # Make sure location header is set
        location = resp.headers.get("Location", None)
        self.assertNotEqual(location, None)
        # Check the data is correct
        data = resp.get_json()
        logging.debug("data = %s", data)
        self.assertEqual(data["name"], product["name"])

    def test_update_product(self):
        """Update a Product"""
        # create a product to update
        test_product = ProductFactory()
        resp = self.app.post(
            BASE_URL, json=test_product.serialize(), content_type=CONTENT_TYPE_JSON
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # update the product
        new_product = resp.get_json()
        logging.debug(new_product)
        new_product["category"] = "unknown"
        resp = self.app.put(
            f"{BASE_URL}/{new_product['_id']}",
            json=new_product,
            content_type=CONTENT_TYPE_JSON,
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        updated_product = resp.get_json()
        self.assertEqual(updated_product["category"], "unknown")

    def test_update_product_with_no_name(self):
        """Update a Product without assigning a name"""
        product = self._create_products()[0]
        product_data = product.serialize()
        del product_data["name"]
        resp = self.app.put(
            f"{BASE_URL}/{product.id}",
            json=product_data,
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_product_not_found(self):
        """Update a Product that doesn't exist"""
        resp = self.app.put(f"{BASE_URL}/foo", json={}, content_type="application/json")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_product(self):
        """Delete a Product"""
        products = self._create_products(5)
        product_count = self.get_product_count()
        test_product = products[0]
        resp = self.app.delete(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(resp.data), 0)
        # make sure they are deleted
        resp = self.app.get(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        new_count = self.get_product_count()
        self.assertEqual(new_count, product_count - 1)

    def test_create_product_with_no_name(self):
        """Create a Product without a name"""
        product = self._create_products()[0]
        new_product = product.serialize()
        del new_product["name"]
        logging.debug("Product no name: %s", new_product)
        resp = self.app.post(BASE_URL, json=new_product, content_type="application/json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_no_content_type(self):
        """Create a Product with no Content-Type"""
        resp = self.app.post(BASE_URL, data="bad data")
        self.assertEqual(resp.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_product_wrong_content_type(self):
        """Create a Product with wrong Content-Type"""
        resp = self.app.post(BASE_URL, data={}, content_type="plain/text")
        self.assertEqual(resp.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_call_create_with_an_id(self):
        """Call create passing an id"""
        resp = self.app.post(f"{BASE_URL}/foo", json={})
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_query_by_name(self):
        """Query Products by name"""
        products = self._create_products(5)
        test_name = products[0].name
        name_count = len([product for product in products if product.name == test_name])
        resp = self.app.get(
            BASE_URL, query_string=f"name={quote_plus(test_name)}"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), name_count)
        # check the data just to be sure
        for product in data:
            self.assertEqual(product["name"], test_name)


    def test_query_by_category(self):
        """Query Products by category"""
        products = self._create_products(5)
        test_category = products[0].category
        category_count = len([product for product in products if product.category == test_category])
        resp = self.app.get(
            BASE_URL, query_string=f"category={quote_plus(test_category)}"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), category_count)
        # check the data just to be sure
        for product in data:
            self.assertEqual(product["category"], test_category)


    def test_query_by_availability(self):
        """Query Products by availability"""
        products = self._create_products(10)
        available_products = [product for product in products if product.available is True]
        unavailable_products = [product for product in products if product.available is False]
        available_count = len(available_products)
        unavailable_count = len(unavailable_products)
        logging.debug("Available Products [%d] %s", available_count, available_products)
        logging.debug("Unavailable Products [%d] %s", unavailable_count, unavailable_products)

        # test for available
        resp = self.app.get(
            BASE_URL, query_string="available=true"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), available_count)
        # check the data just to be sure
        for product in data:
            self.assertEqual(product["available"], True)

    def test_purchase_a_product(self):
        """Purchase a Product"""
        products = self._create_products(10)
        available_products = [product for product in products if product.available is True]
        product = available_products[0]
        resp = self.app.put(f"{BASE_URL}/{product.id}/purchase", content_type="application/json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp = self.app.get(f"{BASE_URL}/{product.id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        logging.debug("Response data: %s", data)
        self.assertEqual(data["available"], False)

    def test_purchase_not_available(self):
        """Purchase a Product that is not available"""
        products = self._create_products(10)
        unavailable_products = [product for product in products if product.available is False]
        product = unavailable_products[0]
        resp = self.app.put(f"{BASE_URL}/{product.id}/purchase", content_type="application/json")
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)

    ######################################################################
    # Utility functions
    ######################################################################

    def get_product_count(self):
        """save the current number of products"""
        resp = self.app.get(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        # logging.debug("data = %s", data)
        return len(data)
