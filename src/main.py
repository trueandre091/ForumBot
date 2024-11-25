import asyncio
import logging

from utils.bot import dp, bot
from utils import handlers
from utils.db.database import create_tables, cleanup_outdated_contacts

logging.basicConfig(level=logging.INFO)


async def main():
    await create_tables()
    await cleanup_outdated_contacts()
    print("Бот работает")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
