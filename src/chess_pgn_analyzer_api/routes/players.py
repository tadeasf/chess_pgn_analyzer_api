from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from ..database import get_session
from ..models.player import Player
import httpx

router = APIRouter()


@router.post("/players/{username}")
async def add_player(username: str, session: AsyncSession = Depends(get_session)):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.chess.com/pub/player/{username}")
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Player not found on Chess.com")

    player = Player(username=username)
    session.add(player)
    await session.commit()
    await session.refresh(player)
    return player


@router.get("/players/{username}")
async def get_player(username: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Player).where(Player.username == username))
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player
