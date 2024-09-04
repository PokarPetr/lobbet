from __future__ import annotations

import logging
import random
from aiohttp import ClientSession
from asyncio import gather
from typing import List, Dict
from config import MAIN_URL

from config import PROXIES

async def fetch(url: str, session: ClientSession, proxy: str = None) -> Dict | List:
    try:
        async with session.get(url, proxy=proxy, timeout=10) as response:
            return await response.json()
    except Exception as e:
        logging.error(f"Error fetching {url} with proxy {proxy}: {e}")
        return []

async def fetch_with_retry(url: str, session: ClientSession, max_retries: int = 3) -> Dict | List:
    for attempt in range(max_retries):
        proxy = random.choice(PROXIES)
        result = await fetch(url, session, proxy)
        if result is not None:
            return result
        logging.warning(f"Attempt {attempt + 1}/{max_retries} failed for URL {url}")
    logging.error(f"All {max_retries} attempts failed for URL {url}")
    return []


async def get_all_leagues(session: ClientSession) -> List[str]:
    # Замените URL на соответствующий эндпоинт AdmirabBet для получения лиг
    url = f"{MAIN_URL}/api/sports/leagues"
    all_sports = await fetch_with_retry(url, session)
    leagues_list = []
    if not all_sports:
        return leagues_list
    for sport in all_sports:
        if sport['name'] != 'Soccer':
            continue
        for league in sport.get('leagues', []):
            if league.get('active') and not league.get('blocked') and league.get('numOfMatches', 0) > 1:
                league_url = f"{MAIN_URL}/api/leagues/{league.get('id')}/matches"
                leagues_list.append(league_url)
    return leagues_list


async def get_events(session: ClientSession) -> List[Dict]:
    leagues_urls = await get_all_leagues(session)
    tasks = [get_matches(league_url, session) for league_url in leagues_urls]
    responses = await gather(*tasks)
    matches = [match for response in responses if response for match in response]
    return matches