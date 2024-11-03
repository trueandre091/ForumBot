import yaml
import os
from utils.fn import get_username_by_id, format_time_ranges

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MESSAGES_FILE = os.path.join(BASE_DIR, 'text.yaml')


def load_messages():
    with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


messages = load_messages()


def get_message(key, default="Сообщение отсутствует."):
    return messages.get(key, default)


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
        return message


stickers = {
    "dobro": "CAACAgIAAxkBAAIIEWcjrLdZn5tMewwl67oJvXMhJawuAAJiWwACj0EZSb3bxXqC4gPONgQ",
    "info": "CAACAgIAAxkBAAIIE2cjrNtoCc01fz7oTgywBODy0GdgAALRXAAC4dgZSeKexlkM8OwKNgQ",
    "time": "CAACAgIAAxkBAAIIFWcjrQ0RFzEBqoFtbr7DOkPlHnxHAAK6YAACKXQYSRJH5eefW3VcNgQ",
    "hurry": "CAACAgIAAxkBAAIIF2cjrSQcrN7yl2gPY8b3uZ1VvcH-AALWXwACro8ZSR7l5jStMTEfNgQ",
    "ideas": "CAACAgIAAxkBAAIIGWcjrS4ynx7iryvlidfp5kekqNsgAALnYgACfH0hSZ_D6MVlfs8pNgQ",
    "okey": "CAACAgIAAxkBAAIIG2cjrTl8f73K_tvX45Qa0OfF8YhpAAJsWAACiYggSUfEu1AyH0zcNgQ",
    "time1": "CAACAgIAAxkBAAIIHWcjrUa_HXKVmgbJpWVLLjuXqphXAAI7XQAC3xggSbTS10bU-UhhNgQ",
}
