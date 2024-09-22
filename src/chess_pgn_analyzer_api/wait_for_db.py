import time
import logging
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from .init_db import init_db, DATABASE_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def wait_for_db(max_retries=60, delay=2):
    retries = 0
    while retries < max_retries:
        try:
            logger.info(f"Attempting to connect to database: {DATABASE_URL}")
            engine = create_engine(DATABASE_URL)
            engine.connect()
            logger.info("Successfully connected to the database.")
            init_db()
            return
        except OperationalError as e:
            retries += 1
            logger.warning(f"Attempt {retries}/{max_retries} to connect to the database failed.")
            logger.warning(f"Error: {str(e)}")
            logger.warning(f"Retrying in {delay} seconds...")
            time.sleep(delay)
    
    logger.error("Max retries reached. Could not connect to the database.")
    raise Exception("Database connection failed after maximum retries")

if __name__ == "__main__":
    wait_for_db()