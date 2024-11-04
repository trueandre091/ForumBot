import asyncio
import logging

from utils.bot import dp, bot, threshold_minutes
from utils.google.sheet import fill_table
from utils import handlers
from utils.periodic import periodic_cleanup
from utils.db.database import create_tables

logging.basicConfig(level=logging.INFO)


async def main():
    await create_tables()
    fill_table()
    print("Бот работает")
    await asyncio.gather(
        dp.start_polling(bot),
        periodic_cleanup(interval_minutes=(threshold_minutes/2)+1, threshold_minutes=threshold_minutes)
    )


if __name__ == "__main__":
    asyncio.run(main())