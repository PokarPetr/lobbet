import os
import json
from imports import ClientSession, Semaphore
from typing import Dict
from config import PARSED_MATCHES_DIR

ALL_MATCHES = {}

async def process_event(event: Dict, session: ClientSession, semaphore: Semaphore):
    """
        Processes a match by fetching detailed information, saving it locally, and updating the global match dictionary.

        :param match: A dictionary containing match information.
        :param session: The aiohttp session object.
        :param semaphore: The asyncio semaphore to limit concurrent requests.
    """
    async with semaphore:
        event_id = event.get('id')
        ALL_MATCHES[event_id] = event
        log_dir = PARSED_MATCHES_DIR
        os.makedirs(log_dir, exist_ok=True)
        if 'home_team' in event and 'away_team' in event:
            name = f"{event['home_team']} vs {event['away_team']}"
        else:
            name = event.get('name', '')
        name = name.replace('/', '_').replace('\\', '_')
        file_name = os.path.join(log_dir, f"{name}.json")
        with open(file_name, 'w', encoding='utf-8') as f:
            json.dump(event, f, ensure_ascii=False, indent=4)
            f.write('\n')
