import os
import re
import json
import time
from _datetime import datetime
from imports import ClientSession, Semaphore
from typing import Dict
from config import PARSED_MATCHES_DIR, REFORMAT_DATA

ALL_MATCHES = {}


def determine_type_name(name, mode):
    winner = ''
    if mode == '1380':
        patterns = [
            {"pattern": "GGII", "type_name": "Second Time Both Teams to Goal"},
            {"pattern": "GGI", "type_name": "First Time Both Teams to Goal"},
            {"pattern": "GG", "type_name": "Both Teams to Goal"},


        ]
    else:
        winner_map = {
            '1154': 1,
            '1155': 2
        }
        winner = winner_map.get(mode, '1')
        patterns = [
            {"pattern": "Team", "type_name": f"{winner} Wins and Team Total Home"},
            {"pattern": "not", "type_name": f"Not {winner} Wins and Total Goals"},
            {"pattern": "GGII", "type_name": f"{winner} Wins, Second Time Both Teams to Goal"},
            {"pattern": "GGI", "type_name": f"{winner} Wins, First Time Both Teams to Goal"},
            {"pattern": "GG", "type_name": f"{winner} Wins, Both Teams to Goal"},
            {"pattern": "&", "type_name": f"{winner} Wins and Goals"},
        ]

    for pattern in patterns:
        if pattern['pattern'] in name:
            type_name = pattern['type_name']
            return type_name

    return f"{winner} Wins and Total Goals"


async def reformat_bets(bets):
    outcomes = []

    bet_type_mapping = {
        135: {"type_name": "1X2"},
        136: {"type_name": "Asian Handicap", "type_value": lambda name: "AH1" if name == "1" else "AH2"},
        137: {"type_name": "Total Goals", "type_value": lambda name: "O" if name == "Over" else "U"},
        138: {"type_name": lambda bet: "Team Total Home" if "home" in bet.get('name', '').lower() else "Team Total Away",
              "type_value": lambda name: "HTO" if "over" in name.lower() else "HTU" if "under" in name.lower() else "ATO" if "over" in name.lower() else "ATU"},
        139: {"type_name": lambda bet: f"1H{bet.get('type_name', '')}"},
        140: {"type_name": "Win First Time - Win Match"},
        141: {"type_name": "First Time Team Total Home",
              "type_value": lambda name: "O" if name == "Over" else "U"},
        142: {"type_name": "First Time Team Total Away",
              "type_value": lambda name: "O" if name == "Over" else "U"},
        143: {"type_name": "First Time Total Goals", "type_value": lambda name: "O" if name == "Over" else "U"},
        161: {"type_name": "Second Time Team Total Home",
              "type_value": lambda name: "O" if name == "Over" else "U"},
        162: {"type_name": "Second Time Team Total Away",
              "type_value": lambda name: "O" if name == "Over" else "U"},
        163: {"type_name": "Second Time Total Goals", "type_value": lambda name: "O" if name == "Over" else "U"},
        # 1154: {"type_name": lambda name: determine_type_name(name, '1154')},
        # 1155: {"type_name": lambda name: determine_type_name(name, '1155')},
        # 1380: {"type_name": lambda name: determine_type_name(name, '1380')},
        454: {"type_name": "1X2"},
        221: {"type_name": "Set Handicap", "type_value": lambda name: "AH1" if name == "1" else "AH2"},
        220: {"type_name": "Game Handicap", "type_value": lambda name: "AH1" if name == "1" else "AH2"},
        187: {"type_name": "Total Games", "type_value": lambda name: "O" if name == "More" else "U"},
        215: {"type_name": "1 Set Total Games", "type_value": lambda name: "O" if name == "Over" else "U"},
        218: {"type_name": "1 Set Total Games", "type_value": lambda name: "O" if name == "Over" else "U"},
        219: {"type_name": "2 Set Total Games", "type_value": lambda name: "O" if name == "Over" else "U"},
        229: {"type_name": "Set Win", "type_value": lambda name: "Yes" if name == "Yes" else "No"},
        230: {"type_name": "Set Win", "type_value": lambda name: "Yes" if name == "Yes" else "No"}
    }

    for bet in bets:
        line = 0 if bet.get('sbv') is None else float(bet.get('sbv'))
        bet_type_id = bet.get('betTypeId')

        bet_type_info = bet_type_mapping.get(bet_type_id, {})
        type_name = bet_type_info.get('type_name', '')

        for outcome in bet.get('betOutcomes', []):
            name = outcome.get('name')
            odds = outcome.get('odd', 0)
            if callable(type_name):
                type_name = type_name(name)

            if bet_type_id in [1154, 1155, 1380]:
                type_name = determine_type_name(name, str(bet_type_id))

            type_value = bet_type_info.get('type_value', name)
            if callable(type_value):
                type_value = type_value(name)

            outcomes.append({
                "type_name": type_name,
                "type": type_value,
                "line": line,
                "odds": odds
            })

    return outcomes

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
