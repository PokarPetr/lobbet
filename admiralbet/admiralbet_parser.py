import time
import json
import ujson
import os
import logging
from asyncio import Semaphore, sleep, gather
from aiohttp import ClientSession, WSMsgType
from config import UPDATE_INTERVAL, HEADERS, SEMAPHORE_REQUESTS, PARSED_MATCHES_DIR
from fetchers import get_matches
from processing import process_match, ALL_MATCHES

async def websocket_client(session, data=''):
    async with session.ws_connect('ws://localhost:8080/') as ws:
        if data:
            await ws.send_str(ujson.dumps(data))
        else:
            await ws.send_str("Hello, Server!")

        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                print(f"Client received: {msg.data}")
                if msg.data == 'close':
                    await ws.close()
                    break
            elif msg.type == WSMsgType.ERROR:
                break


async def collect_json_files(directory):
    json_data = []

    if not os.path.exists(directory):
        return json_data

    for file_name in os.listdir(directory):
        if file_name.endswith('.json'):
            file_path = os.path.join(directory, file_name)

            with open(file_path, 'r', encoding='utf-8') as json_file:
                try:
                    data = json.load(json_file)
                    json_data.append(data)
                except json.JSONDecodeError:
                    print(f"Error decoding JSON from {file_path}")

    return json_data

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
        all_data = await collect_json_files(PARSED_MATCHES_DIR)

        if all_data:
            async with ClientSession(headers=HEADERS) as session:
                await websocket_client(session, data=all_data)
        else:
            logging.warning("No data found to send to WebSocket.")
        await sleep(sleep_time)
