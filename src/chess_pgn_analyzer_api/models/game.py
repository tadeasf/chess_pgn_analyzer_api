from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import json
import requests
from bs4 import BeautifulSoup


class Game(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    player_id: int = Field(foreign_key="player.id")
    game_id: str = Field(index=True)
    url: str
    pgn: str
    analyzed: bool = Field(default=False)
    analysis_result: Optional[str] = None
    moves_analyzed: bool = Field(default=False)
    is_processing: bool = Field(default=False)
    move_analysis: Optional[str] = None
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
    eco_name: Optional[str] = None
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

    @staticmethod
    def fetch_opening_name(eco_url: str) -> str:
        if not eco_url or not isinstance(eco_url, str):
            return "Unknown"
        
        try:
            response = requests.get(eco_url, timeout=5)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
            
            if twitter_title and twitter_title.get('content'):
                opening_name = twitter_title['content'].replace(' - Chess Openings', '')
                return opening_name
            
            return "Unknown"
        except Exception as e:
            print(f"Error fetching opening name: {str(e)}")
            return "Unknown"
