import asyncio
from typing import List
from db import DB
from fuzzywuzzy import fuzz
import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S'
)

db = DB()
RATIO = 80


class SearchCoincidence:

    async def launcher(self, donor_name):
        pinnacle = await db.get_all_events_by_bookmakers('pin')
        donor = await db.get_all_events_by_bookmakers(donor_name)
        coins_matches = await self.start_search_coincidence(pinnacle, donor)
        logging.info(f"found {len(coins_matches)} coincidence")
        for coins_ in coins_matches:
            await db.save_pair(coins_[0], coins_[1], donor_name)
            # print(f"{coins_[0]['home']} - {coins_[0]['away']} === {coins_[1]['home']} - {coins_[1]['away']}")
        print(f"{len(coins_matches)}/{len(donor)}/{len(pinnacle)}")
        return coins_matches

    async def start_search_coincidence(self, pinnacle: List, matches: List) -> List:
        nu_list = []
        empty_matches = 0
        for i, v in enumerate(pinnacle):
            if v is None:
                empty_matches += 1
                continue
            if not v:
                continue
            for ii, vv in enumerate(matches):
                if v['sport'].lower() != vv['sport'].lower():
                    if v['sport'].lower() == 'soccer' and vv['sport'].lower() != 'football':
                        continue
                # if v.get('start_at') == vv.get('start_at'):
                #     continue
                # TODO: turn on compare by time and check it
                compare_home = fuzz.partial_ratio(v['home'], vv['home'])
                compare_away = fuzz.partial_ratio(v['away'], vv['away'])
                if compare_home > RATIO and compare_away > RATIO:
                    check_by_league = await self.check_by_league(v, vv)
                    if check_by_league is True:
                        logging.debug(f"{vv.get('bookmaker')}: Skip {v['league']} * {v['home']} - {v['away']}"
                                      f" *** {vv['league']} * {vv['home']} - {vv['away']}")
                        continue
                    await self.check_in_db(v['home'], vv['home'], v, vv)
                    await self.check_in_db(v['away'], vv['away'], v, vv)
                    # print('____________')
                    # print(v['home'], vv['home'])
                    # print(v['away'], vv['away'])
                    # print(v['league'], vv['league'])
                    # print(compare_home, compare_away)
                    nu_list.append([v, vv])
                await asyncio.sleep(0)
            await asyncio.sleep(0)
        if empty_matches > 0:
            logging.warning(f"{empty_matches} pinnacle matches with None markets.")
        return nu_list

    async def check_in_db(self, pinnacle_team, bookie_team, v, vv):
        # pinnacle_team = pin.get('')
        # bookie_team
        team = await db.get_teams(pinnacle_team)
        if team:
            if bookie_team in team.get('names') and vv['bookmaker'] in team['bookmakers'].keys():
                ...
                # report['already_was'] += 1
            else:
                donor = {'bookmaker': vv['bookmaker'], 'team': bookie_team, 'league': vv['league'], 'country': vv['country']}
                team['bookmakers']['admiralbet_me'] = donor
                if bookie_team not in team.get('names'):
                    team.get('names').append(bookie_team)
                await db.update_teams(team)
                # report['updated'] += 1
        else:
            donor = {
                'bookmaker': vv['bookmaker'],
                'team': bookie_team,
                'league': vv['league'],
                'country': vv['country']
            }
            pinnacle = {'bookmaker': v['bookmaker'], 'team': pinnacle_team, 'league': v['league'],
                        'country': v['country']}
            new_team = {
                "names": [pinnacle_team, bookie_team],
                'bookmakers': {
                    'pinnacle': pinnacle,
                    vv['bookmaker']: donor
                }
            }
            await db.insert_teams(new_team)
            # report['new'] += 1

        # print(f"New:", report['new'])
        # print(f"Updated:", report['updated'])
        # print(f"No pinnacle:", report['no_pinnacle'])
        # print(f"Was:", report['already_was'])

    @staticmethod
    async def check_by_league(v: dict, vv: dict) -> bool:
        match_name_v = f"{v['home']} - {v['away']}"
        league_v = v['league']
        match_name_vv = f"{vv['home']} - {vv['away']}"
        league_vv = vv['league']
        if league_vv is None:
            return False
        if 'reserve' in league_v.lower() or 'reserve' in match_name_v.lower():
            if 'reserve' not in league_vv.lower() and 'reserve' not in match_name_vv.lower():
                return True
        if 'u19' in league_v.lower() or 'u19' in match_name_v.lower():
            if 'u19' not in league_vv.lower() and 'u19' not in match_name_vv.lower():
                return True
        if 'u20' in league_v.lower() or 'u20' in match_name_v.lower():
            if 'u20' not in league_vv.lower() and 'u20' not in match_name_vv.lower():
                return True
        if 'u21' in league_v.lower() or 'u21' in match_name_v.lower():
            if 'u21' not in league_vv.lower() and 'u21' not in match_name_vv.lower():
                return True
        if 'u23' in league_v.lower() or 'u23' in match_name_v.lower():
            if 'u23' not in league_vv.lower() and 'u23' not in match_name_vv.lower():
                return True
        if 'women' in league_v.lower()\
                or 'women' in match_name_v.lower()\
                or 'frauen' in league_v.lower() \
                or 'femminile' in league_v.lower()\
                or 'feminine' in league_v.lower()\
                or 'femenina' in league_v.lower()\
                or 'fem.' in league_v.lower()\
                or 'femm.' in league_v.lower()\
                or ' w ' in match_name_v.lower()\
                or '(wom)' in match_name_v.lower()\
                or '(w)' in match_name_v.lower():
            if 'women' not in league_vv.lower()\
                    and 'women' not in match_name_vv.lower()\
                    and 'frauen' not in league_vv.lower() \
                    and 'femminile' not in league_vv.lower()\
                    and 'feminine' not in league_vv.lower()\
                    and 'femenina' not in league_vv.lower()\
                    and 'fem.' not in league_vv.lower()\
                    and 'femm.' not in league_vv.lower()\
                    and ' w ' not in match_name_vv.lower()\
                    and '(wom)' not in match_name_vv.lower()\
                    and '(w)' not in match_name_vv.lower():
                return True
        if 'reserve' in league_vv.lower() or 'reserve' in match_name_vv.lower():
            if 'reserve' not in league_v.lower() and 'reserve' not in match_name_v.lower():
                return True
        if 'u19' in league_vv.lower() or 'u19' in match_name_vv.lower():
            if 'u19' not in league_v.lower() and 'u19' not in match_name_v.lower():
                return True
        if 'u20' in league_vv.lower() or 'u20' in match_name_vv.lower():
            if 'u20' not in league_v.lower() and 'u20' not in match_name_v.lower():
                return True
        if 'u21' in league_vv.lower() or 'u21' in match_name_vv.lower():
            if 'u21' not in league_v.lower() and 'u21' not in match_name_v.lower():
                return True
        if 'u23' in league_vv.lower() or 'u23' in match_name_vv.lower():
            if 'u23' not in league_v.lower() and 'u23' not in match_name_v.lower():
                return True
        if 'women' in league_vv.lower() or 'women' in match_name_vv.lower() or 'frauen' in league_vv.lower() \
                or 'femminile' in league_vv.lower()\
                or 'feminine' in league_vv.lower()\
                or 'fem.' in league_vv.lower()\
                or 'femm.' in league_vv.lower()\
                or 'femenina' in league_vv.lower()\
                or ' w ' in match_name_vv.lower()\
                or '(wom)' in match_name_vv.lower()\
                or '(w)' in match_name_vv.lower():
            if 'women' not in league_v.lower()\
                    and 'women' not in match_name_v.lower()\
                    and 'frauen' not in league_v.lower()\
                    and 'femminile' not in league_v.lower()\
                    and 'feminine' not in league_v.lower()\
                    and 'fem.' not in league_v.lower()\
                    and 'femm.' not in league_v.lower()\
                    and 'femenina' not in league_v.lower()\
                    and ' w ' not in match_name_v.lower()\
                    and '(wom)' not in match_name_v.lower()\
                    and '(w)' not in match_name_v.lower():
                return True
        return False


if __name__ == "__main__":
    s = SearchCoincidence()
    coins = asyncio.run(s.launcher('admiralbet_me'))
    print(len(coins))
