"""
Models for Product Service

All of the models are stored in this module

Models
------
Product - A Product used in eCommerce application

Attributes:
-----------
id (integer) - The id of the product
name (string) - The name of the product
category (string) - The category of the product
description (string) - A brief description which is used to describe a product
price (integer) - The price of the product
stock (integer) - Remaining stock of the product

"""
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint

logger = logging.getLogger("flask.app")

# Create the SQLAlchemy object to be initialized later in init_db()
db = SQLAlchemy()


def init_db(app):
    """Initialize the SQLAlchemy app"""
    Product.init_db(app)

class DatabaseConnectionError(Exception):
    """Custom Exception when database connection fails"""
    pass

class DataValidationError(Exception):
    """Used for an data validation errors when deserializing"""

    pass

class Product(db.Model):
    """
    Class that represents a Product

    This version uses a relational database for persistence which is hidden
    from us by SQLAlchemy's object relational mappings (ORM)
    """

    ##################################################
    # Table Schema
    ##################################################
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(63), nullable=False)
    category = db.Column(db.String(63))
    description = db.Column(db.String(63))
    price = db.Column(db.Integer, nullable=False, default=100)
    stock = db.Column(db.Integer, nullable=False)
    # __table__args = (
    #   CheckConstraint(price >= 0, name='check_price_positive'), {}
    # )
    # we should consider about the negative price in next sprint

    ##################################################
    # INSTANCE METHODS
    ##################################################

    def __repr__(self):
        return "<Product %r id=[%s]>" % (self.name, self.id)

    def create(self):
        """
        Creates a Product to the database
        """
        logger.info("Creating %s", self.name)
        # id must be none to generate next primary key
        self.id = None 
        db.session.add(self)
        db.session.commit()

    def update(self):
        """
        Updates a Product to the database
        """
        logger.info("Saving %s", self.name)
        #if not self.id:
        #    raise DataValidationError("Update called with empty ID field")
        db.session.commit()

    def delete(self):
        """Removes a Product from the database."""
        logger.info("Deleting %s", self.name)
        db.session.delete(self)
        db.session.commit()

    def show(self):
        """Show the product's information."""
        logger.info(self)

    def serialize(self) -> dict:
        """Serializes a Product into a dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "price": self.price,
            "stock": self.stock
        }

    def deserialize(self, data: dict):
        """
        Deserializes a Product from a dictionary
        Args:
            data (dict): A dictionary containing the Product data
        """
        try:
            self.name = data["name"]
            self.category = data["category"]
            self.description = data["description"]
            self.stock = data["stock"]
            # Check the validity of the price attribute
            if isinstance(data["price"], int):
                self.price = data["price"]
            else:
                raise DataValidationError(
                    "Invalid type for boolean [price]: "
                    + str(type(data["price"]))
                )
        #except AttributeError as error:
        #    raise DataValidationError("Invalid attribute: " + error.args[0])
        except KeyError as error:
            raise DataValidationError(
                "Invalid Product: missing " + error.args[0]
            )
        except TypeError as error:
            raise DataValidationError(
                "Invalid Product: body of request contained bad or no data"
            )
        return self

    ##################################################
    # CLASS METHODS
    ##################################################

    @classmethod
    def init_db(cls, app: Flask):
        """Initializes the database session

        :param app: the Flask app
        :type data: Flask

        """
        logger.info("Initializing database")
        # Initialize SQLAlchemy from the Flask app
        db.init_app(app)
        app.app_context().push()
        db.create_all()  # make sqlalchemy tables

    @classmethod
    def all(cls) -> list:
        """Returns all of the Products in the database"""
        logger.info("Processing all Products")
        return cls.query.all()

    @classmethod
    def find(cls, product_id: int):
        """Finds a Product by it's ID

        :param product_id: the id of the Product to find
        :type product_id: int

        :return: an instance with the product_id, or None if not found
        :type: Product

        """
        logger.info("Processing lookup for id %s ...", product_id)
        return cls.query.get(product_id)

    @classmethod
    def find_or_404(cls, product_id: int):
        """Find a Product by it's id

        :param product_id: the id of the Product to find
        :type product_id: int

        :return: an instance with the product_id, or 404_NOT_FOUND if not found
        :type: Product

        """
        logger.info("Processing lookup or 404 for id %s ...", product_id)
        return cls.query.get_or_404(product_id)

    @classmethod
    def find_by_name(cls, name: str) -> list:
        """Returns all Products with the given name

        :param name: the name of the Products you want to match
        :type name: str

        :return: a collection of Products with that name
        :type: list

        """
        logger.info("Processing name query for %s ...", name)
        return cls.query.filter(cls.name == name)

    @classmethod
    def find_by_category(cls, category: str) -> list:
        """Returns all Products with the given category

        :param category: the category of the Products you want to match
        :type category: str

        :return: a collection of Products with that category
        :type: list

        """
        logger.info("Processing name query for %s ...", category)
        return cls.query.filter(cls.category == category)
