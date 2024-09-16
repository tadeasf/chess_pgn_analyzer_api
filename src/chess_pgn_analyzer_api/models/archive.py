from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Archive(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    player_id: int = Field(foreign_key="player.id")
    year: int
    month: int
    url: str
    downloaded: bool = False
    last_download: Optional[datetime] = None
    is_current_month: bool = Field(default=False)
