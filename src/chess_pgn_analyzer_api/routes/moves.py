from fastapi import APIRouter, Depends, BackgroundTasks
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_session
from ..models.game import Game
from stockfish import Stockfish
import chess
import chess.pgn
import io
import json
import multiprocessing
import os
import logging
import subprocess
import shutil

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

router = APIRouter()

stockfish = Stockfish(
    path=stockfish_path,
    depth=12,
    parameters={"Threads": 2, "Minimum Thinking Time": 20},
)


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


def analyze_game_moves(game_pgn: str) -> list:
    pgn = io.StringIO(game_pgn)
    chess_game = chess.pgn.read_game(pgn)
    board = chess_game.board()
    move_analysis = []

    stockfish.set_position([])
    prev_evaluation = stockfish.get_evaluation()

    for move in chess_game.mainline_moves():
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
        move_analysis.append(
            {
                "move": move.uci(),
                "eval_diff": eval_diff,
                "category": move_category,
            }
        )

        prev_evaluation = current_evaluation

    return move_analysis


async def analyze_games_batch(games: list[Game], session: AsyncSession):
    with multiprocessing.Pool() as pool:
        results = pool.map(analyze_game_moves, [game.pgn for game in games])

    for game, move_analysis in zip(games, results):
        game.move_analysis = json.dumps(move_analysis)
        game.moves_analyzed = True

    await session.commit()


async def analyze_all_games(session: AsyncSession):
    batch_size = 10
    while True:
        games = await session.execute(
            select(Game).where(Game.moves_analyzed is False).limit(batch_size)
        )
        games = games.scalars().all()
        if not games:
            break
        await analyze_games_batch(games, session)


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
