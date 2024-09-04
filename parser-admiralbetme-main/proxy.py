import aiofiles
import datetime
import os.path
import logging
import json
import random

from dataclasses import dataclass


@dataclass
class Proxy:
    id: int
    host: str
    port: int
    login: str
    password: str
    created_at: str
    inactived_at: str
    active: bool

    def get_url(self) -> str:
        return f"http://{self.login}:{self.password}@{self.host}:{self.port}"


_logger = logging.getLogger(os.path.basename(__file__))


class ProxyManager:
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, file: str):
        self._file = file

    async def load_file(self) -> list:
        async with aiofiles.open(self._file, "r") as file:
            data = await file.read()

        return json.loads(data)

    async def update_file(self, new_value: list) -> None:
        async with aiofiles.open(self._file, "w") as file:
            await file.write(json.dumps(new_value))

    async def select_proxy(self) -> Proxy | None:
        proxies = await self.load_file()
        if not proxies:
            return

        active_proxies = list(filter(lambda p: p.get("active", False), proxies))
        if not active_proxies:
            _logger.error("No active proxies found")
            return

        proxy = random.choice(active_proxies)
        proxy_obj = Proxy(**proxy)
        return proxy_obj

    async def inactive_proxy(self, id: int):
        proxies = await self.load_file()
        for i in range(len(proxies)):
            if proxies[i].get("id") == id:
                proxies[i]["active"] = False
                proxies[i]["inactived_at"] = datetime.datetime.now().strftime(
                    self.DATE_FORMAT
                )

        await self.update_file(proxies)
