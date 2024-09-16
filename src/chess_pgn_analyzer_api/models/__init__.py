from .player import Player
from .game import Game
from .archive import Archive
from sqlmodel import Relationship

Player.games = Relationship(
    back_populates="player", sa_relationship_kwargs={"lazy": "selectin"}
)
Player.archives = Relationship(
    back_populates="player", sa_relationship_kwargs={"lazy": "selectin"}
)
Game.player = Relationship(back_populates="games")
Archive.player = Relationship(back_populates="archives")

__all__ = ["Player", "Game", "Archive"]
