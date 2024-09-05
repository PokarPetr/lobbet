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
