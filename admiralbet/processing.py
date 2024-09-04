import os
import json
from aiohttp import ClientSession
from asyncio import Semaphore
from typing import Dict
from config import PARSED_MATCHES_DIR
from utils import convert_timestamp_to_format

ALL_MATCHES = {}
parsed_matches = {}


async def process_match(match: Dict, session: ClientSession, semaphore: Semaphore):
    async with semaphore:
        match_id = match['match_id']
        match['details'] = await get_match_details(match_id, session)
        match['fetched_at'] = convert_timestamp_to_format()
        ALL_MATCHES[match_id] = match
        parsed_matches[match_id] = match

        log_dir = PARSED_MATCHES_DIR
        os.makedirs(log_dir, exist_ok=True)
        name = f"{match['home_team']} vs {match['away_team']}"
        name = name.replace('/', '_').replace('\\', '_')
        file_name = os.path.join(log_dir, f"{name}.json")
        with open(file_name, 'a', encoding='utf-8') as f:
            json.dump(match, f, ensure_ascii=False, indent=4)
            f.write('\n')
