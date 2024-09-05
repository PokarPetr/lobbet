from imports import run
from admiralbet_parser import update_odds_periodically

"""
   Entry point of the application. It schedules periodic updates for fetching and processing odds data.
"""
if __name__ == "__main__":
    run(update_odds_periodically())
