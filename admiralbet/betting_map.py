import re

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
        time_map = {
            '1': 'Home',
            '2': "Away",
        }
        winner = winner_map.get(mode, '1')
        team_match = re.search(r'Team(\d)', name)
        team_number = team_match.group(1) if team_match else None
        patterns = [
                {"pattern": "Team", "type_name": f"{winner} Wins and {time_map.get(team_number, '')} Total Goals"},
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
              "type_value": lambda name: "1HHTO" if name == "Over" else "1HHTU"},
        142: {"type_name": "First Time Team Total Away",
              "type_value": lambda name: "1HATO" if name == "Over" else "1HATU"},
        143: {"type_name": "First Time Total Goals", "type_value": lambda name: "1HO" if name == "Over" else "1HU"},
        # 152: {"type_name": "1X2 Double Chance"},
        161: {"type_name": "Second Time Team Total Home",
              "type_value": lambda name: "2HHTO" if name == "Over" else "2HHTU"},
        162: {"type_name": "Second Time Team Total Away",
              "type_value": lambda name: "2HATO" if name == "Over" else "2HATU"},
        163: {"type_name": "Second Time Total Goals", "type_value": lambda name: "2HO" if name == "Over" else "2HU"},
        187: {"type_name": "Total Games", "type_value": lambda name: "O" if name == "More" else "U"},
        215: {"type_name": "1 Set Total Games", "type_value": lambda name: "1HO" if name == "Over" else "1HU"},
        218: {"type_name": "1 Set Total Games", "type_value": lambda name: "1HO" if name == "Over" else "1HU"},
        219: {"type_name": "2 Set Total Games", "type_value": lambda name: "2HO" if name == "Over" else "2HU"},
        221: {"type_name": "Set Asian Handicap", "type_value": lambda name: "AH1" if name == "1" else "AH2"},
        220: {"type_name": "Game Asian Handicap", "type_value": lambda name: "GAH1" if name == "1" else "GAH2"},
        229: {"type_name": "First Player Wins Set", "type_value": lambda name: "Yes" if name == "Yes" else "No"},
        230: {"type_name": "Second Player Wins Set", "type_value": lambda name: "Yes" if name == "Yes" else "No"},
        454: {"type_name": "1X2"},
        # 764: {"type_name": "1X2 No Draw"},
    }

    for bet in bets:
        line = 0 if bet.get('sbv') is None else float(bet.get('sbv'))
        bet_type_id = bet.get('betTypeId')

        if bet_type_id not in bet_type_mapping:
            continue

        bet_type_info = bet_type_mapping.get(bet_type_id, {})
        type_name = bet_type_info.get('type_name', '')

        for outcome in bet.get('betOutcomes', []):
            name = outcome.get('name')
            odds = outcome.get('odd', 0)
            if callable(type_name):
                type_name = type_name(name)

            # if bet_type_id in [1154, 1155, 1380]:
            #     type_name = determine_type_name(name, str(bet_type_id))

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
