import asyncio
import logging
import time
from typing import List

from parser import ParserService, Match
from aiosearch import SearchCoincidence
from compare import SearchCoincidence as SearchCoincidence2
from admiralbet_me import AdmiralBetMe
from db_client import get_event, update_match, reg_as_worker
from db_client import get_job, set_status_of_job, save_events
from db_client import save_bulk_events_for_db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S'
)

search = SearchCoincidence()
search2 = SearchCoincidence2()

bookmaker = 'admiralbet_me'
job_type = 'parser'
parser = AdmiralBetMe(service=ParserService.prematch)


async def run():
    await reg_as_worker(bookmaker, 'manual')
    await reg_as_worker(bookmaker, 'parser')
    time_ = time.time() - 500
    while True:
        job = await get_job(job_type, bookmaker)
        if job:
            if job['type'] == 'get_match_details':
                event = await get_event(job)
                markets = await parser.get_match_details(event['url'])
                await update_match(markets, job)
                await set_status_of_job(job['job_id'], status='completed')
            elif job['type'] == 'get_24hour_matches':
                matches: List[Match] = await parser.get_24_hour_matches()
                await save_events(matches, bookmaker)
                await search.launcher(bookmaker)
                await set_status_of_job(job['job_id'], status='completed')
            elif job['type'] == 'get_48hour_matches':
                matches: List[Match] = await parser.get_48_hour_matches()
                await save_events(matches, bookmaker)
                await search.launcher(bookmaker)
                await set_status_of_job(job['job_id'], status='completed')
        if time.time() - time_ > 300:
            matches: List[Match] = await parser.get_48_hour_matches()
            await save_events(matches, bookmaker)
            await search.launcher(bookmaker)
            await search2.launcher(bookmaker)
            await save_bulk_events_for_db(matches, bookmaker)
            time_ = time.time()
        await asyncio.sleep(0.0)


if __name__ == "__main__":
    while True:
        try:
            asyncio.run(run())
        except Exception as e:
            logging.error(f"{e}")
            time.sleep(5)
