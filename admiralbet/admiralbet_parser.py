import time
import logging
from asyncio import Semaphore, sleep, gather
from aiohttp import ClientSession
from config import UPDATE_INTERVAL, HEADERS, SEMAPHORE_REQUESTS
from fetchers import get_matches
from processing import process_match, ALL_MATCHES


async def get_odds():
    """
        Fetches events from AdmiralBet, processes each match and updates the list of parsed matches.
    """
    semaphore = Semaphore(SEMAPHORE_REQUESTS)
    async with ClientSession(headers=HEADERS) as session:
        events = await get_matches(session)
        tasks = [process_match(event, session, semaphore) for event in events]
        await gather(*tasks)

        logging.info(f"Total matches fetched: {len(events)}")


async def update_odds_periodically(interval: int = None):
    """
       Periodically updates odds at a specified interval (in seconds).

       :param interval: The time interval (in seconds) between updates. If not provided, it uses the default value from config.py.
    """
    if interval is None:
        interval = UPDATE_INTERVAL
    while True:
        start_time = time.time()
        try:
            await get_odds()
            logging.info(f"Admiralbet odds updated. Total matches: {len(ALL_MATCHES)}")
        except Exception as e:
            logging.error(f"Error updating odds: {e}")

        execution_time = time.time() - start_time
        sleep_time = max(0, interval - execution_time)
        await sleep(sleep_time)
