import logging
from pymongo import MongoClient, ASCENDING
from config import settings

logger = logging.getLogger(__name__)

try:
    client = MongoClient(settings.MONGODB_URI)
    db = client[settings.DB_NAME]
    products_collection = db["products"]
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise e

def init_db():
    """Ensure unique index on the sku field before running the API."""
    try:
        products_collection.create_index([("sku", ASCENDING)], unique=True)
        logger.info("Successfully ensured unique index on 'sku'.")
    except Exception as e:
        logger.error(f"Error creating unique index on 'sku': {e}")