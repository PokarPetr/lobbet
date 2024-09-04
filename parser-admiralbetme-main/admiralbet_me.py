import time
from abc import ABC

import fake_useragent
import logging
from typing import Dict, List
from datetime import datetime, timedelta
import asyncio
import aiohttp

from parser import Parser, ParserService, Market, Match, Json, Sport

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S'
)


headers = {
            "Language": "en-US",
            "OfficeId": "1175",
            "user-agent": fake_useragent.UserAgent().random
        }


class AdmiralBetSport(Sport):
    soccer = 1


class AdmiralBetMe(Parser, ABC):

    async def get_24_hour_matches(self) -> List[Match]:
        date_in = time.strftime('%Y-%m-%dT%H:%M:%S.000')
        date_out = (datetime.now() + timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%S.000')
        matches: List[Match] = await self.get_events(date_in, date_out)
        logging.info(f"AdmiralBet has {len(matches)} events in near 24 hours.")
        return matches

    async def get_48_hour_matches(self) -> List[Match]:
        date_in = time.strftime('%Y-%m-%dT%H:%M:%S.000')
        date_out = (datetime.now() + timedelta(hours=48)).strftime('%Y-%m-%dT%H:%M:%S.000')
        matches: List[Match] = await self.get_events(date_in, date_out)
        logging.info(f"AdmiralBet has {len(matches)} in near 48 hours.")
        return matches

    async def get_events(self, date_in: str, date_out: str):
        async with aiohttp.ClientSession() as session:
            url_ = "https://webapi.admiralbet.me/SportBookCacheWeb/api/offer/tree/null/true/true/true" \
                  f"/{date_in}" \
                  f"/{date_out}" \
                  "/false"
            try:
                async with session.get(
                    url_,
                    headers=headers,
                    timeout=120
                ) as response:
                    data = await response.json()
            except Exception as e:
                logging.error(f"AdmiralBet error: {e}")
                return []
        regions = await self.get_regions(data)
        data = await self.get_all_matches(regions)
        try:
            matches_ = await self.matches_from_json(data)
        except AttributeError:
            logging.error(f"AttributeError")
            return []
        return matches_

    async def get_all_matches(self, regions: Dict) -> List[Dict]:
        tasks = []
        sem = asyncio.Semaphore(100)
        for key, region in regions.items():
            try:
                task = asyncio.ensure_future(self.fetch_matches(region, sem))
                tasks.append(task)
            except Exception as e:
                logging.error(e)
        responses = await asyncio.gather(*tasks)
        data = []
        for response in responses:
            data += response
        return data

    @staticmethod
    async def get_regions(data: Dict) -> Dict:
        regions = {}
        for d in data:
            # if d['name'] in ['Football', 'Basketball']:
            if d['name'] in ['Football']:
                for country in d['regions']:
                    if country['eventsCount'] >= 1:
                        regions[country['id']] = {'id': country['id'], 'sport_id': country['sportId']}
        return regions

    @staticmethod
    async def fetch_matches(region, sem):
        async with sem:
            date_in = time.strftime('%Y-%m-%dT%H:%M:%S.000')
            date_out = (datetime.now() + timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%S.000')

            async with aiohttp.ClientSession() as session:
                url_ = "https://webapi.admiralbet.me/SportBookCacheWeb/api/offer/getWebEventsSelections?" \
                      "pageId=3" \
                      f"&sportId={region['sport_id']}" \
                      f"&regionId={region['id']}" \
                      "&isLive=false" \
                      f"&dateFrom={date_in}" \
                      f"&dateTo={date_out}"
                try:
                    async with session.get(
                            url_,
                            headers=headers,
                            timeout=120
                    ) as response:
                        data = await response.json()
                except Exception as e:
                    logging.info("Admiralbet ERROR")
                    logging.debug(e)
                    logging.warning(f"Could not get all live list")
                    return []
        return data

    @staticmethod
    async def matches_from_json(data: List) -> List[Match]:
        matches = []
        for i, d in enumerate(data):
            if d['mappingTypeId'] > 1:
                logging.debug(f"skip bonus matches {d['name']}")
                continue
            if ' - ' not in d['name']:
                logging.debug(f"it's no a match: {d['name']}")
                continue
            url_ = ''
            try:
                try:
                    start_time = int(datetime.fromisoformat(d['dateTime']).timestamp()) + 14400
                except Exception as e:
                    logging.error(f"time incorrect format: {e}")
                    continue
                url_ = f"https://admiralbet.me/sport-prematch?sport={d['sportName']}" \
                       f"&region={d['regionName'].replace(' ', '_')}" \
                       f"&competition={d['competitionName'].replace(' ', '_')}" \
                       f"&competitionId={d['sportId']}-{d['regionId']}-{d['competitionId']}&" \
                       f"event={d['id']}" \
                       f"&eventName={d['name'].replace(' ', '_')}"
            except TypeError:
                start_time = None
            home = d['name'].split(' - ')[0]
            away = d['name'].split(' - ')[1]
            sport_name = 'soccer' if d['sportName'] == 'Football' else d['sportName'].lower()
            match = Match(
                id=d['id'],
                url=url_,
                home=home,
                away=away,
                start_at=start_time,
                league=d['competitionName'],
                country=d['regionName'],
                markets=[],
                sport=sport_name,
                bookmaker='admiralbet_me'
            )
            matches.append(match)
        return matches

    async def fetch(self, url_: str) -> Json:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    url_,
                    headers=headers,
                    timeout=120
                ) as response:
                    data = await response.json()
                    return data
            except Exception as e:
                logging.error(f"AdmiralBet error: {e}")
                return {}

    async def get_match_details(self, url_: str) -> List[Market]:
        event_id = url_.split('&event=')[1].split('&')[0]
        competition_id = url_.split('&competitionId=')[1].split('&')[0].replace('-', '/')
        link = f"https://webapi.admiralbet.me/SportBookCacheWeb/api/offer/betsAndGroups/" \
               f"{competition_id}/{event_id}"
        bets = await self.fetch(link)
        markets = await self.convert_to_scanner_format(bets)
        logging.info(f"match {event_id} has {len(markets)} markets")
        return markets

    @staticmethod
    def scanner_format_bet(ctsf):
        scanner_format_bet = {
                        'type_name': ctsf['type_name'],
                        'type': ctsf['type'],
                        'line': ctsf['line'],
                        'odds': ctsf['odds']
                    }
        return scanner_format_bet

    async def convert_to_scanner_format(self, bets):
        converted_list = []
        for bet in bets['bets']:
            for i, outcome in enumerate(bet['betOutcomes']):
                ctsf = await self.convert_to_scanner_format_(outcome)
                if ctsf is False:
                    continue
                converted_list.append(ctsf)
        return converted_list

    @staticmethod
    async def convert_to_scanner_format_(bet):
        if bet.get('betTypeId') in [135]:
            return Market(
                type_name='1X2',
                type=bet.get('name'),
                line='0.0',
                odds=bet.get('odd', 0)
            )
        elif bet.get('betTypeId') in [148]:
            return Market(
                type_name='First Half 1X2',
                type=f"1H{bet.get('name')}",
                line='0.0',
                odds=bet.get('odd', 0)
            )
        elif bet['betTypeId'] in [186]:
            return Market(
                type_name='12',
                type=bet.get('name', 0),
                line='0.0',
                odds=bet.get('odd', 0)
            )
        elif bet['betTypeId'] in [137, 213]:
            type_ = ''
            if bet.get('name') in ['Manje', 'Under']:
                type_ = 'U'
            elif bet.get('name') in ['Vise', 'Over']:
                type_ = 'O'
            return Market(
                type_name='Total',
                type=type_,
                line=bet.get('sbv'),
                odds=bet.get('odd')
            )
        elif bet['betTypeId'] in [143]:
            type_ = ''
            if bet.get('name') in ['Manje', 'Under']:
                type_ = '1HU'
            elif bet.get('name') in ['Vise', 'Over']:
                type_ = '1HO'
            return Market(
                type_name='First Half Total',
                type=type_,
                line=bet.get('sbv'),
                odds=bet.get('odd')
            )

        elif bet['betTypeId'] in [161, 162]:
            type_ = ''
            if bet.get('name') in ['Manje', 'Under']:
                type_ = 'HU' if bet['betTypeId'] == 161 else 'AU'
            elif bet.get('name') in ['Vise', 'Over']:
                type_ = 'HO' if bet['betTypeId'] == 161 else 'AO'
            return Market(
                type_name='Individual Total',
                type=type_,
                line=bet.get('sbv'),
                odds=bet.get('odd')
            )

        elif bet['betTypeId'] in [196, 788]:
            return Market(
                type_name='Handicap',
                type=f"H{bet['name']}",
                line=bet.get('sbv'),
                odds=bet.get('odd', 0)
            )
        else:
            return False


if __name__ == "__main__":

    parser = AdmiralBetMe(ParserService.prematch)
    ee = asyncio.run(parser.get_24_hour_matches())
    print(ee)
    url = 'https://admiralbet.me/sport-prematch?sport=Fudbal&region=Italija&competition=' \
          'Italija_3_grupa_B&competitionId=1-23-2831&event=4179503&eventName=Juventus_U23_-_Entella'
    details = asyncio.run(parser.get_match_details(url))
    print(details)
