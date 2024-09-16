from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import json


class Game(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    player_id: int = Field(foreign_key="player.id")
    game_id: str = Field(index=True)
    url: str
    pgn: str
    analyzed: bool = Field(default=False)
    analysis_result: Optional[str] = None
    moves_analyzed: bool = Field(default=False)
    move_analysis: Optional[str] = None  # Add this line
    white_username: str
    black_username: str
    white_rating: int
    black_rating: int
    white_result: str
    black_result: str
    start_time: Optional[datetime]
    end_time: datetime
    time_control: str
    rules: Optional[str]
    eco: Optional[str]
    tournament: Optional[str]
    match: Optional[str]

    def set_analyzed_status(self):
        if self.analysis_result:
            try:
                analysis_data = json.loads(self.analysis_result)
                self.analyzed = bool(analysis_data) and any(analysis_data.values())
            except json.JSONDecodeError:
                self.analyzed = False
        else:
            self.analyzed = False
