from sqlmodel import SQLModel, create_engine
from .models.player import Player
from .models.game import Game
from .models.archive import Archive
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://chess_user:chess_password@db:5432/chess_pgn_analyzer")

def init_db():
    try:
        engine = create_engine(DATABASE_URL)
        logger.info("Creating database tables...")
        SQLModel.metadata.create_all(engine)
        logger.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"An error occurred while initializing the database: {e}")
        raise

if __name__ == "__main__":
    init_db()