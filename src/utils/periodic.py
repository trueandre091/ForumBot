import asyncio

import utils.db.database as db
from utils.bot import bot
from utils.fn import get_username_by_id
from utils.google.sheet import delete


async def periodic_cleanup(interval_minutes=7, threshold_minutes=15):
    while True:
        deleted_meetings = await db.delete_old_meetings(threshold_minutes)
        for meeting in deleted_meetings:
            telegram1 = meeting["contact1_id"]
            telegram2 = meeting["contact2_id"]
            username1 = await get_username_by_id(telegram1)
            username2 = await get_username_by_id(telegram2)
            await delete(meeting["table_num"], meeting["time"], int(meeting["date"]))

            message = (f"Приглашение на встречу с @{username2} {meeting['date']} ноября в {meeting['time']} "
                       f"не было принято в течение {threshold_minutes} минут - <b>бронь отменилась</b>")
            await bot.send_message(chat_id=telegram1, text=message, parse_mode="HTML")

        await asyncio.sleep(interval_minutes * 60)
