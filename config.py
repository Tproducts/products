"""
Global Configuration for Application
"""
import os
import json
import logging

# Get configuration from environment
DATABASE_URI = os.getenv(
    "DATABASE_URI",
    "postgresql+psycopg2://erctqdwo:QaIf8yiJCysBBNG633pjtU7fJL5267A1@salt.db.elephantsql.com/erctqdwo"
)

# override if we are running in Cloud Foundry
#if 'VCAP_SERVICES' in os.environ:
#    vcap = json.loads(os.environ['VCAP_SERVICES'])
#    DATABASE_URI = vcap['user-provided'][0]['credentials']['url']

# Configure SQLAlchemy
SQLALCHEMY_DATABASE_URI = DATABASE_URI
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Secret for session management
SECRET_KEY = os.getenv("SECRET_KEY", "sup3r-s3cr3t")
LOGGING_LEVEL = logging.INFO
