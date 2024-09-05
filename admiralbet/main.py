from imports import run
from admiralbet_parser import schedule_odds_updates

"""
   Entry point of the application. It schedules periodic updates for fetching and processing odds data.
"""
if __name__ == "__main__":
    run(schedule_odds_updates())
