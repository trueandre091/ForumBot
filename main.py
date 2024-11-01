import asyncio
import logging

from utils.bot import dp, bot
from utils.excel import fill_table
from utils.dispatcher import start
from utils.callback import callback_change_info
from db.database import create_tables

logging.basicConfig(level=logging.INFO)


async def main():
    await create_tables()
    fill_table()
    print("Бот работает")
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
