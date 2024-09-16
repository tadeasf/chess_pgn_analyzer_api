from sqlmodel import SQLModel, Field
from typing import Optional


class Game(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    player_id: int = Field(foreign_key="player.id")
    game_id: str = Field(index=True)
    pgn: str
    analyzed: bool = False
    analysis_result: Optional[str] = None
