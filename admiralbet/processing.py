import os
import json
import time
from _datetime import datetime
from imports import ClientSession, Semaphore
from typing import Dict
from config import PARSED_MATCHES_DIR, REFORMAT_DATA
from betting_map import reformat_bets

ALL_MATCHES = {}


async def reformat_event(event):
    formatted_event = {}
    for key, value in REFORMAT_DATA.items():
        if key == 'time':
            formatted_event[key] = time.time()
            continue
        if key == 'outcomes':
            bets = event.get('bets', [])
            formatted_event[key] = await reformat_bets(bets)
            continue
        if key == 'start_time':
            date_str = event[value.get('data_key')]
            start_time = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
            formatted_event[key] = start_time.timestamp()
            continue
        if key == 'type':
            formatted_event[key] = "PreMatch"
            continue

        raw_value = event.get(value.get('data_key'))
        try:
            formatted_value = value['format'](raw_value)
        except (ValueError, TypeError) as e:
            print(f"Error converting {key}: {e}")
            formatted_value = None
        formatted_event[key] = formatted_value
    return formatted_event


async def process_match(event: Dict, session: ClientSession, semaphore: Semaphore):
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

        event = await reformat_event(event)
        with open(file_name, 'w', encoding='utf-8') as f:
            json.dump(event, f, ensure_ascii=False, indent=4)
            f.write('\n')

