from __future__ import annotations

import random
from imports import ClientSession, ClientResponseError, ClientConnectionError, ClientError, gather, logging
from typing import List, Dict, Any
from config import MAIN_URL, PROXIES, HEADERS
from utils import convert_timestamp_to_format

async def fetch(url: str, session: ClientSession, proxy: str = None) -> Dict | List:
    """
    Sends a GET request to the specified URL using a session and an optional proxy.

    :param url: The target URL to fetch data from.
    :param session: The aiohttp session object.
    :param proxy: An optional proxy to use for the request.
    :return: A parsed JSON response or an empty list if an error occurs.
    """
    try:
        async with session.get(url, headers=HEADERS, proxy=proxy, timeout=10) as response:
            response.raise_for_status()
            return await response.json()
    except ClientResponseError as e:
        logging.error(f"HTTP error fetching {url}: {e}")
    except ClientConnectionError as e:
        logging.error(f"Connection error fetching {url}: {e}")
    except ClientError as e:
        logging.error(f"Client error fetching {url}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error fetching {url}: {e}")
    return {}

async def fetch_with_retry(url: str, session: ClientSession, max_retries: int = 3) -> Dict | List:
    """
    Tries to fetch data from the URL multiple times with retries in case of failure.

    :param url: The URL to fetch data from.
    :param session: The aiohttp session object.
    :param max_retries: Maximum number of retry attempts.
    :return: The fetched data if successful, or an empty list after all retries fail.
    """
    for attempt in range(max_retries):
        result = await fetch(url, session)
        if result:
            return result
        logging.warning(f"Attempt {attempt + 1}/{max_retries} failed for URL {url}")
    logging.error(f"All {max_retries} attempts failed for URL {url}")
    return []

async def get_all_leagues(session: ClientSession) -> List[str]:
    """
    Fetches all available Football leagues from AdmiralBet's API.

    :param session: The aiohttp session object.
    :return: A list of URLs for active, non-blocked leagues with matches.
    """
    date_in = convert_timestamp_to_format()
    date_out = convert_timestamp_to_format(24)

    url = f"{MAIN_URL}/SportBookCacheWeb/api/offer/tree/null/true/true/true" \
          f"/{date_in}" \
          f"/{date_out}" \
          "/false"
    all_sports = await fetch_with_retry(url, session)

    leagues_list = []
    if not all_sports:
        return leagues_list
    for sport in all_sports:
        if sport.get('name', '').lower() not in ['football', 'soccer', 'tennis']:
            continue
        sport_id = sport.get('id', '1')
        for league in sport.get('regions', []):
            region_id = league.get('id', '')

            league_url = f"{MAIN_URL}/SportBookCacheWeb/api/offer/getWebEventsSelections?" \
                         "pageId=3" \
                         f"&sportId={sport_id}" \
                         f"&regionId={region_id}" \
                         "&isLive=false" \
                         f"&dateFrom={date_in}" \
                         f"&dateTo={date_out}"

            leagues_list.append(league_url)

    return leagues_list

async def get_match_details(url: str, session: ClientSession) -> List[Dict]:
    """
    Fetches event details from a given URL and processes them into a structured format.

    :param url: The URL to fetch event details from.
    :param session: The aiohttp session object.
    :return: A list of event dictionaries with processed details.
    """
    data = []
    raw_events = await fetch_with_retry(url, session)
    if raw_events:
        for raw_event in raw_events:
            event = dict()
            event['id'] = raw_event.get('id', '0')
            event['name'] = raw_event.get('name', '')

            if '-' in event['name']:
                teams = event['name'].split('-')
                event['home_team'] = teams[0].strip()
                event['away_team'] = teams[1].strip()

            event['sportName'] = raw_event.get('sportName', '')
            event['competitionId'] = raw_event.get('competitionId', '0')
            event['regionName'] = raw_event.get('regionName', '')
            event['regionId'] = raw_event.get('regionId', '0')
            event['dateTime'] = raw_event.get('dateTime', '0')
            event['bets'] = raw_event.get('bets', [])

            data.append(event)
    return data

async def get_matches(session: ClientSession) -> List[Dict]:
    """
    Fetches events (matches) for all available leagues.

    :param session: The aiohttp session object.
    :return: A list of match dictionaries fetched from the API.
    """
    leagues_urls = await get_all_leagues(session)
    tasks = [get_match_details(league_url, session) for league_url in leagues_urls]
    responses = await gather(*tasks)
    matches = [match for response in responses for match in response]
    return matches
