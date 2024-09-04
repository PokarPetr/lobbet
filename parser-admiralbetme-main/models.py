from typing import Optional, List, Union
from pydantic import BaseModel


class Market(BaseModel):
    type: str
    type_name: str
    line: str
    odds: float


class Event(BaseModel):
    id: int
    url: str
    home: str
    away: str
    kickoff: Optional[int] = 0
    league: Union[str, None]
    markets: List[Market]
    sport: str
    bookmaker: Optional[str] = ''
