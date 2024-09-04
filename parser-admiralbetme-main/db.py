import asyncio
import random
import time
import logging
from typing import Union, List, Dict
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from models import Event
# from client.models import CommandResponse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S'
)


class DB:

    def __init__(self):
        # insert db-path and port to settings yaml in future
        self.client = AsyncIOMotorClient('mongodb://localhost:27017/')
        self.db = self.client.sports
        self.teams = self.client.team2

    async def save_events(self, events: List[Event], bookmaker: str) -> None:
        """
        !!!!!!!!!!!!!!!!!
        Temporary decision to use insert_one for dave some time for start Value project
        In future need to learn how to use insert_many or upsert_many

        @return:
        """
        for event in events:
            try:
                await self.db[f"{bookmaker}_events"].delete_many({'start_at': {'$lte': int(time.time())}})
                await self.db[f"{bookmaker}_events"].update_one(
                    {'id': event.id}, {'$setOnInsert': event.model_dump()}, upsert=True
                )
                # logging.debug(result)
                # await self.check_exist_pairs(event['id'], bookmaker)
                # await self.get_rid_of_passed_events(bookmaker)
            except DuplicateKeyError:
                pass

    async def get_all_events_by_bookmakers(self, bookmaker: str) -> List:
        cursor = self.db[f"{bookmaker}_events"].find({'start_at': {'$gte': int(time.time())}})
        return await cursor.to_list(length=2000)

    # async def check_pair_if_exists(self, pin_id: int, bookmaker: str) -> Dict:
    #     pair = await self.db[f"pin_{bookmaker}_pairs"].find_one({'pin_id': pin_id})
    #     return pair

    async def check_exist_pairs(self, pin_id: int) -> List[Dict]:
        workers = self.db.workers.find({'status': 'wait', 'job': 'automation'})
        bookmakers_pairs = []
        for worker in await workers.to_list(length=100):
            # print('worker ================', worker)
            bookie = worker['bookmaker']
            result = await self.db[f"pin_{bookie}_pairs"].find_one({'pin_id': pin_id})
            if result:
                bookmakers_pairs.append(result)
        if bookmakers_pairs:
            # print(f"bookmakers pair: {bookmakers_pairs}")
            in_work_workers = [{x['donor_data']['bookmaker']: -1} for x in bookmakers_pairs]
            await self.db.events.update_one({'pin_id': pin_id}, {'$set': {'workers': in_work_workers}})
        return bookmakers_pairs

    async def save_pair(self, event: Event, donor_event: Event, bookmaker: str) -> None:
        data = {
                'pin_id': event['id'],
                'pin_data': event,
                'donor_id': donor_event['id'],
                'donor_data': donor_event
        }
        try:
            result = await self.db[f"pin_{bookmaker}_pairs"]\
                .update_one(
                {'pin_id': event['id']},
                {'$setOnInsert': data},
                upsert=True
            )
            logging.debug(result)
            await self.db[f"pin_{bookmaker}_pairs"].delete_many(
                {'pin_data': {'start': {'$lte': int(time.time())}}}
            )
        except DuplicateKeyError:
            pass

    # async def get_rid_of_passed_events(self):
    #     await self.db[f"{bookmaker}_events"].update_one(
    #         {'id': event['id']}, {'$setOnInsert': event}, upsert=True
    #     )
    #     client_matches.delete_many({'lastdate': {'$lte': int(time.time()) - 20}})
    #     requests = [InsertOne({'y': 1}), DeleteOne({'x': 1}),
    #                 ReplaceOne({'w': 1}, {'z': 1}, upsert=True)]
    #     result = await db.test.bulk_write(requests)
    #     print("inserted %d, deleted %d, modified %d" % (
    #         result.inserted_count, result.deleted_count, result.modified_count))
    #
    #         print("upserted_ids: %s" % result.upserted_ids)

    async def add_event_to_work(self, events):
        for event in events:
            try:
                await self.db.events.update_one(
                    {'pin_id': event['pin_id']}, {'$setOnInsert': event}, upsert=True
                )
                # logging.debug(result)
                # await self.check_exist_pairs(event['id'], bookmaker)
                # await self.get_rid_of_passed_events(bookmaker)
            except DuplicateKeyError:
                pass

    async def get_event_to_work(self):
        try:
            event = await self.db.events.find_one({'status': 'wait'})
            # event['status'] = 'in_work'
            if event is None:
                return False
            await self.db.events.update_one(
                {'pin_id': event['pin_id']}, {'$set': {'status': 'in_work'}})
            return event
        except DuplicateKeyError:
            pass

    async def find_event_by_id(self, donor_id: Union[int, str], bookmaker: str) -> Dict:
        event = await self.db[f"{bookmaker}_events"].find_one({'id': donor_id})
        return event

    async def check_donor_status(self, pin_id: int, bookmaker: str, status=0) -> None:
        await self.db.events.update_one(
            {'pin_id': pin_id}, {'$set': {'bookmakers': {bookmaker: status}}})

    async def get_num_of_staker(self, pin_id: int) -> int:
        event = await self.db.events.find_one({'pin_id': pin_id})
        return event.get('num_of_bookies', 1)

    async def add_staker_to_bet(self, pin_id: int) -> None:
        r = await self.db.events.find_one_and_update(
            {'pin_id': pin_id}, {'$inc': {'num_of_bookies': 1}}, return_document=ReturnDocument.AFTER)
        return r.get('num_of_bookies', 0)

    async def set_start_wait(self, pin_id: int) -> int:
        wait_start = int(time.time())
        await self.db.events.update_one(
            {'pin_id': pin_id}, {'$set': {'start_wait': wait_start}})
        return wait_start

    async def update_worker_status(self, worker: str, bookmaker: str, status='wait') -> None:
        await self.db.workers.update_one(
            {'pc_name': worker, 'bookmaker': bookmaker, 'job': 'automation'},
            {'$set': {'status': status}}
        )
        logging.debug(f"Updated {worker} with {bookmaker} status to {status}")

    async def check_status_of_job(self, job_id: int) -> Dict:
        job = await self.db.jobs.find_one({'job_id': job_id})
        return job

    async def set_status_of_job(self, job_id: int, status='wait') -> Dict:
        job = await self.db.jobs.update_one({'job_id': job_id}, {'$set': {'status': status}})
        return job

    async def get_job(self, job_type: str, bookie: str):
        job = await self.db.jobs.find_one({'status': 'wait', 'job': job_type, 'bookmaker': bookie})
        if job:
            await self.db.jobs.update_one(
                {'job_id': job['job_id']},
                {'$set': {'status': 'in_work'}}
            )
        return job

    """ Engine commands """
    async def get_match_details(self, pair: Dict) -> int:
        job_id = random.randint(100000000, 99999999999)
        bookie = pair['donor_data']['bookmaker']
        await self.db.jobs.insert_one({
            'job_id': job_id,
            'bookmaker': bookie,
            'job': 'parser',
            'type': 'get_match_details',
            'event_id': pair['donor_id'],
            'status': 'wait',
            'time': int(time.time())
        })
        logging.debug(f"Placed job(id: {job_id}) to work.")
        return job_id
        # {'$set': {'status': 'wait', }}

    async def place_coef_to_cart(self, pair: Dict, bet_details: Dict, drop: Dict, bet_size: int) -> int:
        job_id = random.randint(100000000, 99999999999)
        bookie = pair['donor_data']['bookmaker']
        donor = Event(**pair['donor_data'])
        bet_json = {
            # 'id': job_id,
            'url': donor.url,
            'home': donor.home,
            'away': donor.away,
            'start_at': donor.kickoff,
            'sport': donor.sport,
            'outcome': drop['market'],
            'bet_size': bet_size,
            'min_bet_value': bet_details.min_bet_value,
            # 'roi': bet_details.roi,
            'bookmaker': bookie
        }
        await self.db.jobs.insert_one({
            'job_id': job_id,
            'type': 'place_to_cart',
            'data': bet_json,
            'bookmaker': bookie,
            'job': 'automation',
            'status': 'wait'
        })
        return job_id

    async def get_team(self, team: str):
        team_from_db = await self.teams.teams.find_one({'names': team})
        return team_from_db

    async def test(self):
        pinnacle = await self.get_all_events_by_bookmakers('pin')
        donor = await self.get_all_events_by_bookmakers('admiralbet_me')
        m = 0
        for pin in pinnacle:
            home_team = await self.get_team(pin.get('home'))
            away_team = await self.get_team(pin.get('away'))
            if home_team and away_team:

                # if home_team:
                for d_teams in donor:
                    if d_teams.get('home') in home_team.get('names'):
                        print(pin)
                        print(d_teams)
                        print(home_team.get('names'))
                        print(away_team.get('names'))
                        m += 1
        # print(donor)
        print(m)

    async def get_teams(self, team: str):
        teams = await self.teams.teams.find_one({'names': team})
        return teams

    async def insert_teams(self, new_team):
        await self.teams.teams.insert_one(new_team)

    async def update_teams(self, team):
        await self.teams.teams.update_one(
            {'_id': team.get('_id')},
            {'$set': {'bookmakers': team['bookmakers'], 'names': team.get('names')}}
        )


if __name__ == "__main__":
    db = DB()
    asyncio.run(db.test())
