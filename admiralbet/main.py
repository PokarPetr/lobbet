import asyncio
from parser import update_odds_periodically

if __name__ == "__main__":
    asyncio.run(update_odds_periodically())
