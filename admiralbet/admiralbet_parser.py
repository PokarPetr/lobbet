import time
import logging
from asyncio import Semaphore, sleep, gather
from aiohttp import ClientSession
from config import UPDATE_INTERVAL, HEADERS, SEMAPHORE_REQUESTS
from fetchers import get_events
from processing import process_event, ALL_MATCHES


async def fetch_and_process_odds():
    """
        Fetches events from AdmiralBet, processes each match and updates the list of parsed matches.
    """
    semaphore = Semaphore(SEMAPHORE_REQUESTS)
    async with ClientSession(headers=HEADERS) as session:
        events = await get_events(session)
        tasks = [process_event(event, session, semaphore) for event in events]
        await gather(*tasks)

        logging.info(f"Total matches fetched: {len(events)}")


async def schedule_odds_updates(interval: int = None):
    """
       Periodically updates odds at a specified interval (in seconds).

       :param interval: The time interval (in seconds) between updates. If not provided, it uses the default value from config.py.
    """
    if interval is None:
        interval = UPDATE_INTERVAL
    while True:
        start_time = time.time()
        try:
            await fetch_and_process_odds()
            logging.info(f"Admiralbet odds updated. Total matches: {len(ALL_MATCHES)}")
        except Exception as e:
            logging.error(f"Error updating odds: {e}")

        execution_time = time.time() - start_time
        sleep_time = max(0, interval - execution_time)
        await sleep(sleep_time)
