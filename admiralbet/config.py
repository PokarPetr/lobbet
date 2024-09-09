from imports import logging

BOOKIE = 'admiralbet'
MAIN_URL = 'https://webapi.admiralbet.me'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.4 Safari/605.1.15',
    'Content-Type': 'text/plain;charset=UTF-8',
    'Language': 'en-US',
    'OfficeId': '1175',
}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S'
)

PROXIES = [
    None,
]
SEMAPHORE_REQUESTS = 20
UPDATE_INTERVAL = 15

LOG_DIR = 'logs'
PARSED_MATCHES_DIR = 'parsed_matches'

REFORMAT_DATA = {
 'event_id': {
              'format': int,
              'data_key': 'id'},
 'match_name': {
              'format': str,
              'data_key': 'name'},
 'start_time': {
              'format': float,
              'data_key': 'dateTime'},
 'home_team': {
              'format': str,
              'data_key': 'home_team'},
 'away_team': {
              'format': str,
              'data_key': 'away_team'},
 'league_id': {
              'format': int,
              'data_key': 'competitionId'},
 'league':  {
              'format': str,
              'data_key': 'competitionName'},
 'country': {
              'format': str,
              'data_key': 'regionName'},
 'sport': {
              'format': str,
              'data_key': 'sportName'},
 'type': {
              'format': str,
              'data_key': 'type'},
 'outcomes': {
              'format': list,
              'data_key': 'bets'},
 'time': {
              'format': float,
              'data_key': ''},
 }

REFORMAT_ODDS = {
 'type_name': {
              'format': str,
              'data_key': 'id'},
 'type': {
              'format': str,
              'data_key': 'name'},
 'line': {
              'format': float,
              'data_key': 'dateTime'},
 'odds': {
              'format': float,
              'data_key': 'home_team'},
 }