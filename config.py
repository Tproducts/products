"""
Global Configuration for Application
"""
import os
import json
import logging

# Get configuration from environment
DATABASE_URI = os.getenv(
    "DATABASE_URI",
    "postgresql://erctqdwo:QaIf8yiJCysBBNG633pjtU7fJL5267A1@salt.db.elephantsql.com/erctqdwo"
)

# Configure SQLAlchemy
SQLALCHEMY_DATABASE_URI = DATABASE_URI
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Secret for session management
SECRET_KEY = os.getenv("SECRET_KEY", "sup3r-s3cr3t")
LOGGING_LEVEL = logging.INFO
