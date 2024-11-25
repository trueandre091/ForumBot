from datetime import datetime
from typing import List, Tuple
from utils.config import load_config
from utils.bot import bot
import utils.db.database as db
import json

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
        company = f"компании {contact2['company_name']}" if contact2['company_name'] != '/skip' else ""
        description = f"\nОписание: {contact2['description']}" if contact2['description'] != '/skip' else ""

        message += (
            f"🕑 {num}. <b>{meeting['date']} {meeting['time']}</b>\n"
            f"<b>Место встречи: {meeting['place']}</b>\n"
            f"Участник: {contact2['contact_position']} {company} {contact2['contact_name']}\n\n"
        )
        num += 1

    return message


async def get_card(user):
    config = load_config()
    meeting_times = json.loads(user['meeting_times'], strict=False)
    
    times_formatted = []
    for date in config['meeting']['dates']:
        times = meeting_times.get(date, "отсутствуют")
        if times != "отсутствуют":
            try:
                times = format_time_ranges(times)
            except Exception as e:
                print(e)
                times = "отсутствуют"
        times_formatted.append(f"🗓️ {date}: {times}")

    times_str = "\n".join(times_formatted)  # Предварительно объединяем список

    message = (
        f"{user['contact_position']}\n"
        f"{user['contact_name']}\n\n"
        f"Компания: {user['company_name']}\n"
        f"Описание: {user['description']}\n"
        f"Веб-сайт: {user['website']}\n"
        f"Номер телефона: {user['phone']}\n"
        f"Телеграм: @{await get_username_by_id(user['telegram'])}\n\n"
        f"<b>Временные возможности во время форума:</b>\n"
        f"{times_str}"
    )
    
    if user["speaker_place"]:
        message = f"<b>Спикер форума</b>\n{message}"
        message += f"\n\n<b>Место встречи</b>: {user['speaker_place']}"
    
    return message


def get_meetings_times(meeting_times: dict) -> dict:
    """Генерирует словарь времен встреч для каждой даты."""
    def generate_times(hours: List[str]) -> List[str]:
        """Генерирует список времен для заданных часов."""
        times = []
        for hour in hours:
            for minute in range(0, 60, 20):
                times.append(f"{hour.zfill(2)}:{minute:02d}")
        return times

    result = {}
    for date, hours in meeting_times.items():
        if hours != "отсутствуют":
            times = sorted(
                generate_times(hours), 
                key=lambda x: (int(x[0:2]) - 10 * 3) + (int(x[3]) // 2)
            )
            result[date] = times
        else:
            result[date] = []
            
    return result
