from enum import Enum
from typing import TypedDict, Optional, TypeAlias

from proxy import ProxyManager


Id: TypeAlias = str | int
Json: TypeAlias = list | dict


class ParserService(Enum):
    live = "live"
    prematch = "prematch"


class Sport(Enum):
    """
    Inherit from this class
    """

    pass


class Market(TypedDict):
    type: str
    type_name: str
    line: str
    odds: float


class SportDict(TypedDict):
    id: int
    name: str


class Match(TypedDict):
    id: Id
    name: str
    url: str
    home: str
    away: str
    start_at: int  # unix time
    sport: str
    bookmaker: str
    league: str | None
    country: str | None
    markets: list[Market]


class Parser:
    def __init__(self, service: ParserService, *, proxy_file: Optional[str] = None):
        if not isinstance(service, ParserService):
            raise ValueError("service type invalid")

        self._service = service.value
        self._proxy_manager = None
        if proxy_file:
            self._proxy_manager = ProxyManager(proxy_file)

    async def get_24hour_matches(self, sport: Sport) -> list[Match]:
        """
        Get all matches by sport during 24 hours
        """
        raise NotImplementedError

    async def get_48hour_matches(self, sport: Sport) -> list[Match]:
        """
        Get all matches by sport during 48 hours
        """
        raise NotImplementedError

    async def get_match(self, idk: Id) -> Match | None:
        """
        Get match details by id
        """
        raise NotImplementedError

    async def fetch(self, *args, **kwargs) -> Json:
        """
        Function for fethching data. Use only this method to fetch data
        """
        raise NotImplementedError

    async def select_proxy(self) -> str | None:
        if self._proxy_manager:
            proxy_obj = await self._proxy_manager.select_proxy()
            return proxy_obj.get_url() if proxy_obj else None
        return None
