import time
import logging
from asyncio import Semaphore, sleep, gather
from aiohttp import ClientSession
from config import UPDATE_INTERVAL, HEADERS, SEMAPHORE_REQUESTS
from fetchers import get_events, fetch_with_retry
from processing import process_match, ALL_MATCHES, parsed_matches



async def get_odds():
    semaphore = Semaphore(SEMAPHORE_REQUESTS)
    async with ClientSession(headers=HEADERS) as session:
        matches = await get_events(session)
        tasks = [process_match(match, session, semaphore) for match in matches]
        await gather(*tasks)

        logging.info(f"Total matches fetched: {len(matches)}")
    return parsed_matches


async def update_odds_periodically(interval: int = None):
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
