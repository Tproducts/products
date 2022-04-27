"""
Product Service with Swagger

Paths (Based on RESTful standard):
------
GET / - Displays a UI for Selenium testing
GET /products - Returns a list all of the Products
GET /products/{id} - Returns the Product with a given id number
POST /products - creates a new Product record in the database
PUT /products/{id} - updates a Product record in the database
DELETE /products/{id} - deletes a Product record in the database
"""

import sys
import secrets
import logging
from functools import wraps
from flask import jsonify, request, url_for, make_response, render_template
from flask_restx import Api, Resource, fields, reqparse, inputs
from service.models import Product, DataValidationError, DatabaseConnectionError
from .utils import status   # HTTP Status Codes
from . import app  

######################################################################
# GET HEALTH CHECK
######################################################################
@app.route("/healthcheck")
def healthcheck():
    """Let them know our heart is still beating"""
    return make_response(jsonify(status=200, message="Healthy"), status.HTTP_200_OK)

######################################################################
# Configure the Root route before OpenAPI
######################################################################
@app.route('/')
def index():
    """ Index page """
    app.logger.info("Request for Root URL")
    return app.send_static_file('index.html')


######################################################################
# Configure Swagger before initializing it
######################################################################
api = Api(app,
          version='1.0.0',
          title='Product REST API Service',
          description='This is a Product server.',
          default='products',
          default_label='Product shop operations',
          doc='/apidocs', # default also could use doc='/apidocs/'
          prefix='' # changed from /api to /
         )


# Define the model so that the docs reflect what can be sent
create_model = api.model('Product', {
    'name': fields.String(required=True,
                          description='The name of the Product'),
    'category': fields.String(required=True,
                              description='The category of Product'),
    'price': fields.Integer(required=True,
                              description='The price of Product'),
    'stock': fields.Integer(required=True,
                              description='The stock of Product'),
    'description': fields.String(description='The gender of the Product')
})

product_model = api.inherit(
    'ProductModel', 
    create_model,
    {
        'id': fields.Integer(readOnly=True,
                            description='The unique id assigned internally by service'),
    }
)


# query string arguments
product_args = reqparse.RequestParser()
product_args.add_argument('name', type=str, required=False, help='List Products by name')
product_args.add_argument('category', type=str, required=False, help='List Products by category')

######################################################################
# Special Error Handlers
######################################################################
@api.errorhandler(DataValidationError)
def request_validation_error(error):
    """ Handles Value Errors from bad data """
    message = str(error)
    app.logger.error(message)
    return {
        'status_code': status.HTTP_400_BAD_REQUEST,
        'error': 'Bad Request',
        'message': message
    }, status.HTTP_400_BAD_REQUEST

@api.errorhandler(DatabaseConnectionError)
def database_connection_error(error):
    """ Handles Database Errors from connection attempts """
    message = str(error)
    app.logger.critical(message)
    return {
        'status_code': status.HTTP_503_SERVICE_UNAVAILABLE,
        'error': 'Service Unavailable',
        'message': message
    }, status.HTTP_503_SERVICE_UNAVAILABLE


######################################################################
#  PATH: /products/{id}
######################################################################
@api.route('/products/<product_id>')
@api.param('product_id', 'The Product identifier')
class ProductResource(Resource):
    """
    ProductResource class

    Allows the manipulation of a single Product
    GET /product{id} - Returns a Product with the id
    PUT /product{id} - Update a Product with the id
    DELETE /product{id} -  Deletes a Product with the id
    """

    #------------------------------------------------------------------
    # RETRIEVE A PRODUCT
    #------------------------------------------------------------------
    @api.doc('get_products')
    @api.response(404, 'Product not found')
    @api.marshal_with(product_model)
    def get(self, product_id):
        """
        Retrieve a single Product

        This endpoint will return a Product based on it's id
        """
        app.logger.info("Request to Retrieve a product with id [%s]", product_id)
        product = Product.find(product_id)
        if not product:
            abort(status.HTTP_404_NOT_FOUND, "Product with id '{}' was not found.".format(product_id))
        return product.serialize(), status.HTTP_200_OK

    #------------------------------------------------------------------
    # UPDATE AN EXISTING PRODUCT
    #------------------------------------------------------------------
    @api.doc('update_products')
    @api.response(404, 'Product not found')
    @api.response(400, 'The posted Product data was not valid')
    @api.expect(create_model)
    @api.marshal_with(product_model)
    def put(self, product_id):
        """
        Update a Product

        This endpoint will update a Product based the body that is posted
        """
        app.logger.info('Request to Update a product with id [%s]', product_id)
        product = Product.find(product_id)
        if not product:
            abort(status.HTTP_404_NOT_FOUND, "Product with id '{}' was not found.".format(product_id))
        app.logger.debug('Payload = %s', api.payload)
        data = api.payload # difference
        product.deserialize(data)
        product.id = product_id
        product.update()
        return product.serialize(), status.HTTP_200_OK

    #------------------------------------------------------------------
    # DELETE A PRODUCT
    #------------------------------------------------------------------
    @api.doc('delete_products')
    @api.response(204, 'Product deleted')
    @api.response(404, 'Product was not found')
    def delete(self, product_id):
        """
        Delete a Product

        This endpoint will delete a Product based the id specified in the path
        """
        app.logger.info('Request to Delete a product with id [%s]', product_id)
        product = Product.find(product_id)
        if product:
            product.delete()
            app.logger.info('Product with id [%s] was deleted', product_id)
        else:
            abort(status.HTTP_404_NOT_FOUND, "Product with id '{}' was not found.".format(product_id))

        return '', status.HTTP_204_NO_CONTENT


######################################################################
#  PATH: /products
######################################################################
@api.route('/products', strict_slashes=False)
class ProductCollection(Resource):
    """ Handles all interactions with collections of Products """
    #------------------------------------------------------------------
    # LIST ALL PRODUCTS
    #------------------------------------------------------------------
    @api.doc('list_products')
    @api.expect(product_args, validate=True)
    @api.response(200, 'Listed all products')
    @api.marshal_list_with(product_model)
    def get(self):
        """ List Products """
        app.logger.info('Request to list Products...')
        products = []
        args = product_args.parse_args()
        if args['name']:
            app.logger.info('Filtering by name: %s', args['name'])
            products = Product.find_by_name(args['name'])
        elif args['category']:
            app.logger.info('Filtering by category: %s', args['category'])
            products = Product.find_by_category(args['category'])
        else:
            app.logger.info('Returning unfiltered list.')
            products = Product.all()

        results = [product.serialize() for product in products]
        app.logger.info('[%s] Products returned', len(results))
        return results, status.HTTP_200_OK


    #------------------------------------------------------------------
    # CREATE A NEW PRODUCT
    #------------------------------------------------------------------
    @api.doc('create_products')
    @api.response(400, 'The posted data was not valid')
    @api.expect(create_model)
    @api.marshal_with(product_model, code=201)
    def post(self):
        """
        Creates a Product
        This endpoint will create a Product based the data in the body that is posted
        """
        app.logger.info('Request to Create a Product')
        check_content_type("application/json")
        product = Product()
        app.logger.debug('Payload = %s', api.payload)
        product.deserialize(api.payload) # difference
        product.create()
        app.logger.info('Product with new id [%s] created!', product.id)
        location_url = api.url_for(ProductResource, product_id=product.id, _external=True)
        return product.serialize(), status.HTTP_201_CREATED, {'Location': location_url}

    #------------------------------------------------------------------
    # DELETE ALL PRODUCTS (for testing only)
    #------------------------------------------------------------------
    # @api.doc('delete_all_products')
    # @api.response(204, 'All Products deleted')
    # def delete(self):
    #     """
    #     Delete all Product

    #     This endpoint will delete all Product only if the system is under test
    #     """
    #     app.logger.info('Request to Delete all products...')
    #     if "TESTING" in app.config and app.config["TESTING"]:
    #         Product.remove_all()
    #         app.logger.info("Removed all Products from the database")
    #     else:
    #         app.logger.warning("Request to clear database while system not under test")

    #     return '', status.HTTP_204_NO_CONTENT


######################################################################
#  PATH: /products/{id}/purchase
######################################################################
@api.route('/products/<product_id>/purchase')
@api.param('product_id', 'The Product identifier')
class PurchaseResource(Resource):
    """ Purchase actions on a Product """
    @api.doc('purchase_products')
    @api.response(200, 'Success')
    @api.response(404, 'Product not found')
    @api.response(409, 'The Product is out of stock')
    def put(self, product_id):
        """
        Purchase a Product

        This endpoint will purchase a Product and decrease its stock by 1
        """
        app.logger.info('Request to Purchase a Product')
        product = Product.find(product_id)
        if not product:
            abort(status.HTTP_404_NOT_FOUND, 'Product with id [{}] was not found.'.format(product_id))
        if product.stock <= 0:
            abort(status.HTTP_409_CONFLICT, 'Product with id [{}] is out of stock.'.format(product_id))
        stock_num = product.stock
        product.stock = stock_num - 1
        product.update()
        app.logger.info('Product with id [%s] has been purchased!', product.id)
        return product.serialize(), status.HTTP_200_OK


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################

def abort(error_code: int, message: str):
    """Logs errors before aborting"""
    app.logger.error(message)
    api.abort(error_code, message)

@app.before_first_request
def init_db():
    """ Initlaize the model """
    global app
    Product.init_db(app)

def check_content_type(media_type):
    """Checks that the media type is correct"""
    content_type = request.headers.get("Content-Type")
    if content_type and content_type == media_type:
        return
    app.logger.error("Invalid Content-Type: %s", content_type)
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        "Content-Type must be {}".format(media_type),
    )