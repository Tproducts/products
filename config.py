"""
Global Configuration for Application
"""
import os
import json
import logging

# Get configuration from environment
DATABASE_URI = os.getenv(
    "DATABASE_URI",
    "postgres://postgres:postgres@localhost:5432/postgres"
    # "postgresql://erctqdwo:QaIf8yiJCysBBNG633pjtU7fJL5267A1@salt.db.elephantsql.com/erctqdwo"
)

# Override if running in Cloud Foundry
if "VCAP_SERVICES" in os.environ:
    vcap = json.loads(os.environ["VCAP_SERVICES"])
    url = vcap["user-provided"][0]["credentials"]["url"]
    DATABASE_URI = {"DATABASE_URI", url}

print(DATABASE_URI)

# Configure SQLAlchemy
SQLALCHEMY_DATABASE_URI = DATABASE_URI
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Secret for session management
SECRET_KEY = os.getenv("SECRET_KEY", "sup3r-s3cr3t")
LOGGING_LEVEL = logging.INFO
