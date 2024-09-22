from fastapi import APIRouter, Depends, BackgroundTasks
from sqlmodel import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.dialects.postgresql import array
from ..database import get_session
from ..models.game import Game
from stockfish import Stockfish
import chess
import chess.pgn
import io
import json
import os
import logging
import shutil
import asyncio
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Get Stockfish path from environment variable or find it in PATH
stockfish_path = os.getenv('STOCKFISH_PATH') or shutil.which('stockfish')
if not stockfish_path:
    logger.error("Stockfish executable not found")
    raise RuntimeError("Stockfish not found")

logger.info(f"Stockfish path: {stockfish_path}")

# Check if Stockfish is executable
if not os.access(stockfish_path, os.X_OK):
    logger.error(f"Stockfish at {stockfish_path} is not executable")
    raise RuntimeError("Stockfish is not executable")

# Initialize Stockfish
try:
    stockfish = Stockfish(
        path=stockfish_path,
        depth=12,
        parameters={"Threads": 2, "Minimum Thinking Time": 20},
    )
    logger.info("Stockfish initialized successfully")
except Exception as e:
    logger.error(f"Error initializing Stockfish: {str(e)}")
    raise RuntimeError(f"Failed to initialize Stockfish: {str(e)}")

# Semaphore to limit concurrent Stockfish instances
MAX_CONCURRENT_ANALYSIS = 8 # Adjust based on your server's capacity
semaphore = asyncio.Semaphore(MAX_CONCURRENT_ANALYSIS)

def categorize_move(evaluation_diff):
    if evaluation_diff <= -300:
        return "??"  # Blunder
    elif evaluation_diff <= -150:
        return "?"  # Mistake
    elif evaluation_diff <= -75:
        return "?!"  # Dubious Move
    elif evaluation_diff < -30:
        return "∓"  # Slight disadvantage
    elif evaluation_diff < 30:
        return "="  # Equal position
    elif evaluation_diff < 75:
        return "⩲"  # Slight advantage
    elif evaluation_diff < 150:
        return "±"  # Clear advantage
    elif evaluation_diff < 300:
        return "+"  # Winning advantage
    else:
        return "++"  # Decisive advantage

async def analyze_game_moves(game_pgn: str) -> list:
    logger.info(f"Starting analysis of game moves")
    start_time = time.time()
    
    async with semaphore:
        try:
            return await asyncio.to_thread(_analyze_game_moves_sync, game_pgn)
        finally:
            end_time = time.time()
            logger.info(f"Game move analysis completed in {end_time - start_time:.2f} seconds")

def _analyze_game_moves_sync(game_pgn: str) -> list:
    logger.info("Initializing Stockfish for game analysis")
    stockfish = Stockfish(path=stockfish_path, depth=12, parameters={"Threads": 2, "Minimum Thinking Time": 20})
    
    pgn = io.StringIO(game_pgn)
    chess_game = chess.pgn.read_game(pgn)
    board = chess_game.board()
    move_analysis = []

    stockfish.set_position([])
    prev_evaluation = stockfish.get_evaluation()
    logger.info(f"Initial position evaluation: {prev_evaluation}")

    for move_number, move in enumerate(chess_game.mainline_moves(), start=1):
        board.push(move)
        stockfish.make_moves_from_current_position([move.uci()])
        current_evaluation = stockfish.get_evaluation()
        
        # Handle mate scores
        if prev_evaluation["type"] == "mate" and current_evaluation["type"] == "mate":
            eval_diff = (prev_evaluation["value"] - current_evaluation["value"]) * 100
        elif prev_evaluation["type"] == "mate":
            eval_diff = 10000 if prev_evaluation["value"] > 0 else -10000
        elif current_evaluation["type"] == "mate":
            eval_diff = -10000 if current_evaluation["value"] > 0 else 10000
        else:
            eval_diff = (current_evaluation["value"] - prev_evaluation["value"]) * (
                -1 if board.turn == chess.BLACK else 1
            )

        move_category = categorize_move(eval_diff)
        move_analysis.append({
            "move": move.uci(),
            "eval_diff": eval_diff,
            "category": move_category,
        })
        
        logger.info(f"Move {move_number}: {move.uci()} - Category: {move_category}, Eval diff: {eval_diff}")

        prev_evaluation = current_evaluation

    logger.info(f"Completed analysis of {len(move_analysis)} moves")
    return move_analysis

async def analyze_game(game: Game, session: AsyncSession):
    try:
        logger.info(f"Starting analysis for game {game.game_id}")
        move_analysis = await analyze_game_moves(game.pgn)
        game.move_analysis = json.dumps(move_analysis)
        game.moves_analyzed = True
        logger.info(f"Analysis completed for game {game.game_id}")
        return game
    except Exception as e:
        logger.error(f"Error analyzing game {game.game_id}: {str(e)}")
        game.moves_analyzed = False
        game.is_processing = False
        return game

async def analyze_all_games(session: AsyncSession):
    batch_size = 10  # Reduced batch size for testing
    total_analyzed = 0
    
    while True:
        async with session.begin():
            # Select games to analyze
            subquery = (
                select(Game.id)
                .where(and_(Game.moves_analyzed == False, Game.is_processing == False))
                .limit(batch_size)
                .subquery()
            )

            # Update selected games to mark them as being processed
            update_stmt = (
                update(Game)
                .where(and_(Game.id.in_(subquery), Game.moves_analyzed == False, Game.is_processing == False))
                .values(is_processing=True)
                .returning(Game)
            )
            result = await session.execute(update_stmt)
            games = result.scalars().all()

            if not games:
                break

            analyzed_games = await asyncio.gather(*[analyze_game(game, session) for game in games])
            for game in analyzed_games:
                if game:
                    game.is_processing = False
                    session.add(game)
                    if game.moves_analyzed:
                        total_analyzed += 1

        try:
            await session.commit()
            logger.info(f"Committed analysis for {len(analyzed_games)} games. Total analyzed: {total_analyzed}")
        except Exception as e:
            logger.error(f"Error committing game analysis: {str(e)}")
            await session.rollback()

        # Add a small delay between batches
        await asyncio.sleep(1)

    logger.info(f"All games analyzed. Total: {total_analyzed}")

@router.post("/analyze-moves")
async def analyze_moves(
    background_tasks: BackgroundTasks, session: AsyncSession = Depends(get_session)
):
    background_tasks.add_task(analyze_all_games, session)
    return {"message": "Move analysis started in the background"}

@router.get("/game-move-analysis/{game_id}")
async def get_game_move_analysis(
    game_id: str, session: AsyncSession = Depends(get_session)
):
    game = await session.execute(select(Game).where(Game.game_id == game_id))
    game = game.scalar_one_or_none()

    if not game:
        return {"error": "Game not found"}

    if not game.moves_analyzed:
        return {"error": "Game moves have not been analyzed yet"}

    move_analysis = json.loads(game.move_analysis)
    return {"game_id": game_id, "move_analysis": move_analysis}
