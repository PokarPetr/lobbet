import time
import logging
from typing import List, Dict, TypedDict
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError
from pymongo import InsertOne

from models import Event
from parser import Match

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S'
)


client = AsyncIOMotorClient('mongodb://localhost:27017/')
db = client.sports


class Job(TypedDict):
    _id: Dict
    job_id: int | str
    bookmaker: str
    job: str
    type: str
    event_id: int | str
    status: str
    time: int


async def get_job(job_type: str, bookie: str):
    job = await db.jobs.find_one({'status': 'wait', 'job': job_type, 'bookmaker': bookie})
    if job:
        await set_status_of_job(job['job_id'], status='in_work')
    return job


async def set_status_of_job(job_id: int, status='wait') -> Dict:
    job = await db.jobs.update_one({'job_id': job_id}, {'$set': {'status': status}})
    return job


async def save_events(events: List[Match], bookie: str) -> None:
    """
    !!!!!!!!!!!!!!!!!
    Temporary decision to use insert_one for save some time for start Value project
    In future need to learn how to use insert_many or upsert_many

    @return:
    """
    for event in events:
        try:
            await db[f"{bookie}_events"].delete_many({'start_at': {'$lte': int(time.time())}})
            await db[f"{bookie}_events"].update_one(
                {'id': event['id']}, {'$setOnInsert': event}, upsert=True
            )
        except DuplicateKeyError:
            pass


async def save_bulk_events_for_db(events: List[Match], bookie: str) -> None:
    operations = []
    for event in events:
        if not await db[f"teams_database_{bookie}"].find_one({'name': event['home'], 'country': event['country']}):
            operations += [InsertOne({'name': event['home'], 'league': event['league'], 'country': event['country']})]
        if not await db[f"teams_database_{bookie}"].find_one({'name': event['away'], 'country': event['country']}):
            operations += [InsertOne({'name': event['away'], 'league': event['league'], 'country': event['country']})]
    if operations:
        result = await db[f"teams_database_{bookie}"].bulk_write(operations)
        logging.debug(result.bulk_api_result)


async def update_match(markets: List, job: Dict) -> None:
    logging.debug(f"Update donor market")
    await db[f"{job['bookmaker']}_events"]\
        .update_one({'id': job['event_id']},
                    {'$set': {'markets': markets}})


async def get_event(job: Dict) -> Event:
    event = await db[f"{job['bookmaker']}_events"].find_one({'id': job['event_id']})
    return event


async def reg_as_worker(bookmaker: str, job_type: str) -> None:
    worker = {
        "pc_name": "betcoders",
        "bookmaker": bookmaker,
        "balance": 0,
        "status": "wait",
        "job": job_type,
        "time": time.time()
    }
    exists = await db.workers.find_one(
        {'pc_name': "betcoders", "bookmaker": bookmaker, "job": job_type}
    )
    if exists:
        await db.workers.update_one({'_id': exists['_id']},  {'$set': {'time': time.time()}})
    else:
        await db.workers.insert_one(worker)
    logging.debug(f"Connect {worker['pc_name']} {worker['bookmaker']} {worker['job']}")
