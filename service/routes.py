"""
Product Service with UI

Paths:
------
GET / - Displays a UI for Selenium testing
GET /products - Returns a list all of the Products
GET /products/{id} - Returns the Product with a given id number
POST /products - creates a new Product record in the database
PUT /products/{id} - updates a Product record in the database
DELETE /products/{id} - deletes a Product record in the database
"""

import sys
import logging
from flask import jsonify, request, json, url_for, make_response, abort
from . import app
from service.models import Product
from .utils import status  # HTTP Status Codes
from .utils import error_handlers


######################################################################
# GET HEALTH CHECK
######################################################################
@app.route("/healthcheck")
def healthcheck():
    """Let them know our heart is still beating"""
    return make_response(jsonify(status=200, message="Healthy"), status.HTTP_200_OK)


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Base URL for our service"""
    return app.send_static_file("index.html")


######################################################################
# LIST ALL PRODUCTS
######################################################################
@app.route("/products", methods=["GET"])
def list_products():
    """Returns all of the Products"""
    app.logger.info("Request to list Products...")

    products = []
    category = request.args.get("category")
    name = request.args.get("name")
    available = request.args.get("available")
    gender = request.args.get("gender")

    if available:  # convert to boolean
        available = available.lower() in ["true", "yes", "1"]

    if category:
        app.logger.info("Find by category: %s", category)
        products = Product.find_by_category(category)
    elif name:
        app.logger.info("Find by name: %s", name)
        products = Product.find_by_name(name)
    elif available:
        app.logger.info("Find by available: %s", available)
        products = Product.find_by_availability(available)
    # elif gender:
    #     app.logger.info("Find by gender: %s", gender)
    #     products = Product.find_by_gender(gender)
    else:
        app.logger.info("Find all")
        products = Product.all()

    app.logger.info("[%s] Products returned", len(products))
    results = [product.serialize() for product in products]
    return make_response(jsonify(results), status.HTTP_200_OK)


######################################################################
# RETRIEVE A PRODUCT
######################################################################
@app.route("/products/<product_id>", methods=["GET"])
def get_products(product_id):
    """
    Retrieve a single Product

    This endpoint will return a Product based on it's id
    """
    app.logger.info("Request to Retrieve a product with id [%s]", product_id)

    product = Product.find(product_id)
    if not product:
        abort(status.HTTP_404_NOT_FOUND, f"Product with id '{product_id}' was not found.")

    app.logger.info("Returning product: %s", product.name)
    return make_response(jsonify(product.serialize()), status.HTTP_200_OK)


######################################################################
# CREATE A NEW PRODUCT
######################################################################
@app.route("/products", methods=["POST"])
def create_products():
    """
    Creates a Product
    This endpoint will create a Product based the data in the body that is posted
    """
    app.logger.info("Request to Create a Product...")
    data = {}
    # Check for form submission data
    if request.headers.get("Content-Type") == "application/x-www-form-urlencoded":
        app.logger.info("Getting data from FORM submit")
        data = {
            "name": request.form["name"],
            "category": request.form["category"],
            "available": request.form["available"] in ['True', 'true', '1'],
            "price": request.form["price"],
            "description": request.form["description"]
        }
    else:
        check_content_type("application/json")
        app.logger.info("Getting json data from API call")
        data = request.get_json()

    app.logger.info("Processing: %s", data)
    product = Product()
    product.deserialize(data)
    product.create()
    app.logger.info("Product with new id [%s] saved!", product.id)

    message = product.serialize()
    location_url = url_for("get_products", product_id=product.id, _external=True)
    return make_response(jsonify(message), status.HTTP_201_CREATED, {"Location": location_url})


######################################################################
# UPDATE AN EXISTING PRODUCT
######################################################################
@app.route("/products/<product_id>", methods=["PUT"])
def update_products(product_id):
    """
    Update a Product

    This endpoint will update a Product based the body that is posted
    """
    app.logger.info("Request to Update a product with id [%s]", product_id)
    check_content_type("application/json")

    product = Product.find(product_id)
    if not product:
        abort(status.HTTP_404_NOT_FOUND, f"Product with id '{product_id}' was not found.")

    data = request.get_json()
    app.logger.info(data)
    product.deserialize(data)
    product.id = product_id
    product.update()
    return make_response(jsonify(product.serialize()), status.HTTP_200_OK)


######################################################################
# DELETE A PRODUCT
######################################################################
@app.route("/products/<product_id>", methods=["DELETE"])
def delete_products(product_id):
    """
    Delete a Product

    This endpoint will delete a Product based the id specified in the path
    """
    app.logger.info("Request to Delete a product with id [%s]", product_id)

    product = Product.find(product_id)
    if product:
        product.delete()

    return make_response("", status.HTTP_204_NO_CONTENT)


######################################################################
# PURCHASE A PRODUCT
######################################################################
@app.route("/products/<product_id>/purchase", methods=["PUT"])
def purchase_products(product_id):
    """Purchasing a Product makes it unavailable"""
    product = Product.find(product_id)
    if not product:
        abort(status.HTTP_404_NOT_FOUND, f"Product with id '{product_id}' was not found.")
    if not product.available:
        abort(
            status.HTTP_409_CONFLICT,
            f"Product with id '{product_id}' is not available.",
        )
    product.available = False
    product.update()
    return make_response(jsonify(product.serialize()), status.HTTP_200_OK)


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################


@app.before_first_request
def init_db(dbname="products"):
    """Initlaize the model"""
    Product.init_db(dbname)


def data_reset():
    """Removes all Products from the database"""
    if app.testing:
        Product.remove_all()


def check_content_type(content_type):
    """Checks that the media type is correct"""
    if "Content-Type" not in request.headers:
        app.logger.error("No Content-Type specified.")
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Content-Type must be {content_type}",
        )

    if request.headers["Content-Type"] == content_type:
        return

    app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {content_type}",
    )


# @app.before_first_request
def initialize_logging(log_level=app.config["LOGGING_LEVEL"]):
    """Initialized the default logging to STDOUT"""
    if not app.debug:
        print("Setting up logging...")
        # Set up default logging for submodules to use STDOUT
        # datefmt='%m/%d/%Y %I:%M:%S %p'
        fmt = "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
        logging.basicConfig(stream=sys.stdout, level=log_level, format=fmt)
        # Make a new log handler that uses STDOUT
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(fmt))
        handler.setLevel(log_level)
        # Remove the Flask default handlers and use our own
        handler_list = list(app.logger.handlers)
        for log_handler in handler_list:
            app.logger.removeHandler(log_handler)
        app.logger.addHandler(handler)
        app.logger.setLevel(log_level)
        app.logger.info("Logging handler established")
