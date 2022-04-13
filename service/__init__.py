"""
Package: service

Package for the application models and service routes
This module creates and configures the Flask app and sets up the logging
and SQL database
"""
import logging
from flask import Flask
from .utils import log_handlers

# NOTE: Do not change the order of this code
# The Flask app must be created
# BEFORE you import modules that depend on it !!!

# Create the Flask aoo
app = Flask(__name__, template_folder='static')  # pylint: disable=invalid-name

# Load Configurations
app.config.from_object("config")

# Import the routes After the Flask app is created
from service import routes, models
from .utils import error_handlers

# Set up logging for production
log_handlers.init_logging(app, "gunicorn.error")

app.logger.info(70 * "*")
app.logger.info("  P E T   S E R V I C E   R U N N I N G  ".center(70, "*"))
app.logger.info(70 * "*")

app.logger.info("Service inititalized!")
