from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_session
from ..models.game import Game
from ..models.archive import Archive
from .players import get_or_create_player
import httpx
from datetime import datetime
import json

router = APIRouter()


@router.post("/players/{username}/fetch-and-store-games")
async def fetch_and_store_games(
    username: str, session: AsyncSession = Depends(get_session)
):
    player = await get_or_create_player(username, session)
    if not player:
        raise HTTPException(status_code=404, detail="Failed to fetch player data")

    async with httpx.AsyncClient() as client:
        # Fetch archives
        archives_response = await client.get(
            f"https://api.chess.com/pub/player/{username}/games/archives"
        )
        if archives_response.status_code != 200:
            raise HTTPException(
                status_code=archives_response.status_code,
                detail="Failed to fetch archives from Chess.com",
            )

        archives_data = archives_response.json()["archives"]

    total_archives = 0
    total_games = 0
    current_year, current_month = datetime.now().year, datetime.now().month

    # Reset is_current_month for all archives
    await session.execute(update(Archive).values(is_current_month=False))

    for archive_url in archives_data:
        year, month = map(int, archive_url.split("/")[-2:])

        # Check if archive already exists
        existing_archive = await session.execute(
            select(Archive).where(
                Archive.player_id == player.id,
                Archive.year == year,
                Archive.month == month,
            )
        )
        existing_archive = existing_archive.scalar_one_or_none()

        is_current_month = year == current_year and month == current_month

        if existing_archive:
            if is_current_month or not existing_archive.downloaded:
                existing_archive.is_current_month = is_current_month
                existing_archive.downloaded = (
                    False  # Reset to force re-download for current month
                )
            else:
                continue
            archive = existing_archive
        else:
            archive = Archive(
                player_id=player.id,
                year=year,
                month=month,
                url=archive_url,
                is_current_month=is_current_month,
            )
            session.add(archive)
            total_archives += 1

        # Fetch games for this archive
        async with httpx.AsyncClient() as client:
            games_response = await client.get(archive_url)
            if games_response.status_code != 200:
                continue

            games_data = games_response.json()["games"]
            for game_data in games_data:
                game_id = game_data["url"].split("/")[-1]
                existing_game = await session.execute(
                    select(Game).where(Game.game_id == game_id)
                )
                existing_game = existing_game.scalar_one_or_none()

                if existing_game and not is_current_month:
                    continue

                if existing_game:
                    # Update existing game for current month
                    for key, value in game_data.items():
                        if hasattr(existing_game, key):
                            setattr(existing_game, key, value)
                    game = existing_game
                else:
                    # Create new game
                    game = Game(
                        player_id=player.id,
                        game_id=game_id,
                        url=game_data["url"],
                        pgn=game_data["pgn"],
                        white_username=game_data["white"]["username"],
                        black_username=game_data["black"]["username"],
                        white_rating=game_data["white"]["rating"],
                        black_rating=game_data["black"]["rating"],
                        white_result=game_data["white"]["result"],
                        black_result=game_data["black"]["result"],
                        start_time=datetime.fromtimestamp(
                            game_data.get("start_time", game_data["end_time"])
                        ),
                        end_time=datetime.fromtimestamp(game_data["end_time"]),
                        time_control=game_data["time_control"],
                        rules=game_data.get("rules"),
                        eco=game_data.get("eco"),
                        tournament=game_data.get("tournament"),
                        match=game_data.get("match"),
                        analysis_result=json.dumps(game_data.get("accuracies", {})),
                    )
                    session.add(game)

                game.set_analyzed_status()
                total_games += 1

        archive.downloaded = True
        archive.last_download = datetime.utcnow()

    await session.commit()
    return {
        "message": f"Processed {total_archives} archives and stored/updated {total_games} games for {username}",
        "total_archives": total_archives,
        "total_games": total_games,
    }


@router.get("/players/{username}/games")
async def get_player_games(username: str, session: AsyncSession = Depends(get_session)):
    player = await get_or_create_player(username, session)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    games = await session.execute(select(Game).where(Game.player_id == player.id))
    games = games.scalars().all()
    return games
