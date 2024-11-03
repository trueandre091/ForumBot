import asyncio
import logging
import time

from utils.bot import dp, bot, threshold_minutes
from utils.sheet import fill_table
import utils.handlers
from utils.periodic import periodic_cleanup
from db.database import create_tables

logging.basicConfig(level=logging.INFO)


async def main():
    await create_tables()
    fill_table()
    print("Бот работает")
    await asyncio.gather(
        dp.start_polling(bot),
        periodic_cleanup(interval_minutes=1, threshold_minutes=threshold_minutes)
    )


if __name__ == "__main__":
    while True:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("Бот остановлен пользователем.")
            break
        except Exception as e:
            print(f"Произошла ошибка: {e}. Перезапуск через 5 секунд...")
            time.sleep(5)
        finally:
            try:
                asyncio.run(bot.session.close()) # Добавлен asyncio.run
                print("Сессия закрыта.")
            except Exception as close_error:
                print(f"Ошибка при закрытии сессии: {close_error}")
