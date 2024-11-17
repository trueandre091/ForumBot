from datetime import datetime
from typing import List, Tuple

from utils.bot import bot
import utils.db.database as db

pattern_datetime = r"^\d{2} \d{2}:[024]0$"
pattern_phone = r"^(\+)?((\d{2,3}) ?\d|\d)(([ -]?\d)|( ?(\d{2,3}) ?)){5,12}\d$"


async def get_username_by_id(user_id: int):
    user = await bot.get_chat(user_id)
    return user.username if user.username else f"{user_id} (отсутствует username)"


def format_time_ranges(hours):
    # Преобразуем строки в целые числа и сортируем
    hours = sorted(map(int, [hour for hour in hours if hour != "отсутствуют"]))

    ranges = []
    start = hours[0]
    end = hours[0]

    for hour in hours[1:]:
        if hour == end + 1:  # Если следующий час последовательный
            end = hour
        else:
            # Добавляем текущий диапазон в список, увеличивая его на 1
            if start == end:
                ranges.append(f"{start}:00-{end + 1}:00")  # Один час от start
            else:
                ranges.append(f"{start}:00-{end + 1}:00")  # Диапазон start-end + 1
            start = hour
            end = hour

    # Добавляем последний диапазон, увеличивая его на 1
    if start == end:
        ranges.append(f"{start}:00-{end + 1}:00")
    else:
        ranges.append(f"{start}:00-{end + 1}:00")

    return " ".join(ranges)


def is_time_in_range(time_str, time_range):
    # Преобразуем время и границы диапазона в объекты datetime
    time = datetime.strptime(time_str, "%H:%M")
    start, end = map(lambda t: datetime.strptime(t, "%H:%M"), time_range.split("-"))

    # Проверяем, попадает ли время в диапазон
    return start <= time <= end


def get_contacts(clb, meeting) -> list[str, str]:
    if meeting["contact1_id"] == clb.from_user.id:
        telegram2 = meeting["contact2_id"]
        telegram1 = meeting["contact1_id"]
    else:
        telegram2 = meeting["contact1_id"]
        telegram1 = meeting["contact2_id"]
    return [telegram1, telegram2]


async def get_meetings_message(clb, meetings):
    message = ""
    num = 1
    for meeting in meetings:
        telegram1, telegram2 = get_contacts(clb, meeting)
        contact2 = await db.get_contact_by_telegram(telegram2)
        company = f"компании {contact2['company_name']}" if contact2['company_name'] != 'отсутствует' else ""
        description = f"\nОписание: {contact2['description']}" if contact2['description'] != 'отсутствует' else ""

        message += (
            f"🕑 {num}. <b>{meeting['date']} ноября {meeting['time']}</b>\n"
            f"<b>Место встречи: {meeting['place']}</b>\n"
            f"Участник: {contact2['contact_position']} {company} {contact2['contact_name']}\n\n"
        )
        num += 1

    return message


def get_meetings_times(meeting_times_14: List[str], meeting_times_15: List[str]) -> Tuple[List[str], List[str]]:
    def generate_times(hours: List[str]) -> List[str]:
        """Генерирует список времен для заданных часов."""
        times = []
        for hour in hours:
            for minute in range(0, 60, 20):
                times.append(f"{hour.zfill(2)}:{minute:02d}")  # zfill для корректного форматирования
        return times

    times_14 = sorted(generate_times(meeting_times_14), key=lambda x: (int(x[0:2]) - 10 * 3) + (int(x[3]) // 2))
    times_15 = sorted(generate_times(meeting_times_15), key=lambda x: (int(x[0:2]) - 10 * 3) + (int(x[3]) // 2))
    return times_14, times_15


async def get_card(user):
    meeting_times_14 = user['meeting_times_14'].split(',')
    meeting_times_15 = user['meeting_times_15'].split(',')
    try:
        times_14 = format_time_ranges(meeting_times_14)
    except:
        times_14 = "отсутствуют"

    try:
        times_15 = format_time_ranges(meeting_times_15)
    except:
        times_15 = "отсутствуют"

    if times_14 and times_15:
        message = (
            f"{user['contact_position']}\n"
            f"{user['contact_name']}\n\n"
            f"Компания: {user['company_name']}\nОписание: {user['description']}\n"
            f"Веб-сайт: {user['website']}\n"
            f"Номер телефона: {user['phone']}\n"
            f"Телеграм: @{await get_username_by_id(user['telegram'])}\n\n"
            f"<b>Временные возможности во время форума:</b>\n"
            f"🗓️ 14 ноября: {times_14}\n"
            f"🗓️ 15 ноября: {times_15}"
        )
        if user["speaker_place"]:
            message = f"<b>Спикер форума</b>\n" + message
            message += f"\n\n<b>Место встречи</b>: {user['speaker_place']}"
        return message
