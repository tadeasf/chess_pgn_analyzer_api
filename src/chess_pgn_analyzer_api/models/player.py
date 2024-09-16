from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class Player(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True)
    player_id: int
    title: Optional[str] = None
    status: str
    name: Optional[str] = None
    avatar: Optional[str] = None
    location: Optional[str] = None
    country: str
    joined: datetime
    last_online: datetime
    followers: int
    is_streamer: bool
    twitch_url: Optional[str] = None
    fide: Optional[int] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)
