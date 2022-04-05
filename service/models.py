"""
Product Model that uses Cloudant

You must initialize this class before use by calling initialize().
This class looks for an environment variable called VCAP_SERVICES
to get it's database credentials from. If it cannot find one, it
tries to connect to Cloudant on the localhost. If that fails it looks
for a server name 'cloudant' to connect to.

To use with Docker couchdb database use:
    docker run -d --name couchdb -p 5984:5984 -e COUCHDB_USER=admin -e COUCHDB_PASSWORD=pass couchdb

Docker Note:
    CouchDB uses /opt/couchdb/data to store its data, and is exposed as a volume
    e.g., to use current folder add: -v $(pwd):/opt/couchdb/data
    You can also use Docker volumes like this: -v couchdb_data:/opt/couchdb/data

Models
------
Product - A Product used in eCommerce application

Attributes:
-----------
name (string) - The name of the product
category (string) - The category of the product
available (bool) - Whether the product is available for purchase
price (integer) - The price of the product
description (string) - A brief description which is used to describe a product
stock (integer) - Remaining stock of the product

"""

import os
import json
import logging
from enum import Enum
from signal import raise_signal
from retry import retry
from datetime import date
from cloudant.client import Cloudant
from cloudant.query import Query
from cloudant.adapters import Replay429Adapter
from cloudant.database import CloudantDatabase
from requests import HTTPError, ConnectionError

# get configuration from environment (12-factor)
ADMIN_PARTY = os.environ.get("ADMIN_PARTY", "False").lower() == "true"
CLOUDANT_HOST = os.environ.get("CLOUDANT_HOST", "localhost")
CLOUDANT_USERNAME = os.environ.get("CLOUDANT_USERNAME", "admin")
CLOUDANT_PASSWORD = os.environ.get("CLOUDANT_PASSWORD", "pass")

# global variables for retry (must be int)
RETRY_COUNT = int(os.environ.get("RETRY_COUNT", 10))
RETRY_DELAY = int(os.environ.get("RETRY_DELAY", 1))
RETRY_BACKOFF = int(os.environ.get("RETRY_BACKOFF", 2))


class DatabaseConnectionError(Exception):
    """Custom Exception when database connection fails"""


class DataValidationError(Exception):
    """Custom Exception with data validation fails"""



class Product:
    """
    Class that represents a Product

    This version uses a NoSQL database for persistence
    """

    logger = logging.getLogger(__name__)
    client: Cloudant = None
    database: CloudantDatabase = None

    def __init__(
        self,
        name: str = None,
        category: str = None,
        available: bool = True,
        price: int = 0,
        description: str = None,
        stock: int = 0
    ):
        """Constructor"""
        self.id = None  # pylint: disable=invalid-name
        self.name = name
        self.category = category
        self.available = available
        self.price = price
        self.description = description
        self.stock = stock

    def __repr__(self):
        return f"<Product {self.name} id=[{self.id}]>"

    @retry(HTTPError, delay=RETRY_DELAY, backoff=RETRY_BACKOFF, tries=RETRY_COUNT, logger=logger)
    def create(self):
        """
        Creates a new Product in the database
        """
        if self.name is None:  # name is the only required field
            raise DataValidationError("name attribute is not set")

        try:
            document = self.database.create_document(self.serialize())
        except HTTPError as err:
            Product.logger.warning("Create failed: %s", err)
            return

        if document.exists():
            self.id = document["_id"]

    @retry(HTTPError, delay=RETRY_DELAY, backoff=RETRY_BACKOFF, tries=RETRY_COUNT, logger=logger)
    def update(self):
        """Updates a Product in the database"""
        try:
            document = self.database[self.id]
        except KeyError:
            document = None
        if document:
            document.update(self.serialize())
            document.save()

    @retry(HTTPError, delay=RETRY_DELAY, backoff=RETRY_BACKOFF, tries=RETRY_COUNT, logger=logger)
    def delete(self):
        """Deletes a Product from the database"""
        try:
            document = self.database[self.id]
        except KeyError:
            document = None
        if document:
            document.delete()

    def serialize(self) -> dict:
        """serializes a Product into a dictionary"""
        product = {
            "name": self.name,
            "category": self.category,
            "available": self.available,
            "price": self.price,
            "description": self.description,
            "stock": self.stock
        }
        if self.id:
            product["_id"] = self.id
        return product

    def deserialize(self, data: dict) -> None:
        """deserializes a Product my marshalling the data.

        :param data: a Python dictionary representing a Product.
        """
        Product.logger.info("deserialize(%s)", data)
        try:
            self.name = data["name"]
            self.category = data["category"]
            if isinstance(data["available"], bool):
                self.available = data["available"]
            else:
                raise DataValidationError("Invalid type for boolean [available]: " + str(type(data["available"])))
            self.price = data["price"]
            self.description = data["description"]
            self.stock = data["stock"]
        except KeyError as error:
            raise DataValidationError("Invalid product: missing " + error.args[0])
        except TypeError as error:
            raise DataValidationError("Invalid product: body of request contained bad or no data")

        # if there is no id and the data has one, assign it
        if not self.id and "_id" in data:
            self.id = data["_id"]

        return self

    ######################################################################
    #  S T A T I C   D A T A B S E   M E T H O D S
    ######################################################################

    @classmethod
    def connect(cls):
        """Connect to the server"""
        cls.client.connect()

    @classmethod
    def disconnect(cls):
        """Disconnect from the server"""
        cls.client.disconnect()

    @classmethod
    @retry(HTTPError, delay=RETRY_DELAY, backoff=RETRY_BACKOFF, tries=RETRY_COUNT, logger=logger)
    def create_query_index(cls, field_name: str, order: str = "asc"):
        """Creates a new query index for searching"""
        cls.database.create_query_index(index_name=field_name, fields=[{field_name: order}])

    @classmethod
    @retry(HTTPError, delay=RETRY_DELAY, backoff=RETRY_BACKOFF, tries=RETRY_COUNT, logger=logger)
    def remove_all(cls):
        """Removes all documents from the database (use for testing)"""
        for document in cls.database:
            document.delete()

    @classmethod
    @retry(HTTPError, delay=RETRY_DELAY, backoff=RETRY_BACKOFF, tries=RETRY_COUNT, logger=logger)
    def all(cls):
        """Query that returns all Products"""
        results = []
        for doc in cls.database:
            product = Product().deserialize(doc)
            product.id = doc["_id"]
            results.append(product)
        return results


    ######################################################################
    #  F I N D E R   M E T H O D S
    ######################################################################

    @classmethod
    @retry(HTTPError, delay=RETRY_DELAY, backoff=RETRY_BACKOFF, tries=RETRY_COUNT, logger=logger)
    def find_by(cls, **kwargs):
        """Find records using selector"""
        query = Query(cls.database, selector=kwargs)
        results = []
        for doc in query.result:
            product = Product()
            product.deserialize(doc)
            results.append(product)
        return results

    @classmethod
    @retry(HTTPError, delay=RETRY_DELAY, backoff=RETRY_BACKOFF, tries=RETRY_COUNT, logger=logger)
    def find(cls, product_id: str):
        """Query that finds Products by their id"""
        try:
            document = cls.database[product_id]
            # Cloudant doesn't delete documents. :( It leaves the _id with no data
            # so we must validate that _id that came back has a valid _rev
            # if this next line throws a KeyError the document was deleted
            _ = document['_rev']
            return Product().deserialize(document)
        except KeyError:
            return None

    @classmethod
    @retry(HTTPError, delay=RETRY_DELAY, backoff=RETRY_BACKOFF, tries=RETRY_COUNT, logger=logger)
    def find_by_name(cls, name: str):
        """Query that finds Products by their name"""
        return cls.find_by(name=name)

    @classmethod
    @retry(HTTPError, delay=RETRY_DELAY, backoff=RETRY_BACKOFF, tries=RETRY_COUNT, logger=logger)
    def find_by_category(cls, category: str):
        """Query that finds Products by their category"""
        return cls.find_by(category=category)

    @classmethod
    @retry(HTTPError, delay=RETRY_DELAY, backoff=RETRY_BACKOFF, tries=RETRY_COUNT, logger=logger)
    def find_by_availability(cls, available: bool = True):
        """Query that finds Products by their availability"""
        return cls.find_by(available=available)
    

    ############################################################
    #  C L O U D A N T   D A T A B A S E   C O N N E C T I O N
    ############################################################

    @staticmethod
    def init_db(dbname: str = "products"):
        """
        Initialized Cloudant database connection
        """
        opts = {}
        # Try and get VCAP from the environment
        if "VCAP_SERVICES" in os.environ:
            Product.logger.info("Found Cloud Foundry VCAP_SERVICES bindings")
            vcap_services = json.loads(os.environ["VCAP_SERVICES"])
            # Look for Cloudant in VCAP_SERVICES
            for service in vcap_services:
                if service.startswith("cloudantNoSQLDB"):
                    opts = vcap_services[service][0]["credentials"]

        # if VCAP_SERVICES isn't found, maybe we are running on Kubernetes?
        if not opts and "BINDING_CLOUDANT" in os.environ:
            Product.logger.info("Found Kubernetes BINDING_CLOUDANT bindings")
            opts = json.loads(os.environ["BINDING_CLOUDANT"])

        # If Cloudant not found in VCAP_SERVICES or BINDING_CLOUDANT
        # get it from the CLOUDANT_xxx environment variables
        if not opts:
            Product.logger.info("VCAP_SERVICES and BINDING_CLOUDANT undefined.")
            opts = {
                "username": CLOUDANT_USERNAME,
                "password": CLOUDANT_PASSWORD,
                "host": CLOUDANT_HOST,
                "port": 5984,
                "url": "http://" + CLOUDANT_HOST + ":5984/",
            }

        if any(k not in opts for k in ("host", "username", "password", "port", "url")):
            raise DatabaseConnectionError(
                "Error - Failed to retrieve options. " "Check that app is bound to a Cloudant service."
            )

        Product.logger.info("Cloudant Endpoint: %s", opts["url"])
        try:
            if ADMIN_PARTY:
                Product.logger.info("Running in Admin Party Mode...")
            Product.client = Cloudant(
                opts["username"],
                opts["password"],
                url=opts["url"],
                connect=True,
                auto_renew=True,
                admin_party=ADMIN_PARTY,
                adapter=Replay429Adapter(retries=10, initialBackoff=0.01),
            )

        except ConnectionError:
            raise DatabaseConnectionError("Cloudant service could not be reached")

        # Create database if it doesn't exist
        try:
            Product.database = Product.client[dbname]
        except KeyError:
            # Create a database using an initialized client
            Product.database = Product.client.create_database(dbname)
        # check for success
        if not Product.database.exists():
            raise DatabaseConnectionError("Database [{}] could not be obtained".format(dbname))
