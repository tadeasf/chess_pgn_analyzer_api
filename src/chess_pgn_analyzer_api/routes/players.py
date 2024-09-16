from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_session
from ..models.player import Player
import httpx
from datetime import datetime

router = APIRouter()


async def fetch_player_data(username: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.chess.com/pub/player/{username}")
        if response.status_code != 200:
            return None
        return response.json()


async def get_or_create_player(username: str, session: AsyncSession):
    result = await session.execute(select(Player).where(Player.username == username))
    player = result.scalar_one_or_none()

    if not player:
        player_data = await fetch_player_data(username)
        if not player_data:
            return None

        player = Player(
            username=player_data["username"],
            player_id=player_data["player_id"],
            title=player_data.get("title"),
            status=player_data["status"],
            name=player_data.get("name"),
            avatar=player_data.get("avatar"),
            location=player_data.get("location"),
            country=player_data["country"],
            joined=datetime.fromtimestamp(player_data["joined"]),
            last_online=datetime.fromtimestamp(player_data["last_online"]),
            followers=player_data["followers"],
            is_streamer=player_data.get("is_streamer", False),
            twitch_url=player_data.get("twitch_url"),
            fide=player_data.get("fide"),
        )
        session.add(player)
        await session.commit()
        await session.refresh(player)

    return player


@router.post("/players/{username}")
async def add_player(username: str, session: AsyncSession = Depends(get_session)):
    player = await get_or_create_player(username, session)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found on Chess.com")
    return player


@router.get("/players/{username}")
async def get_player(username: str, session: AsyncSession = Depends(get_session)):
    player = await get_or_create_player(username, session)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player
