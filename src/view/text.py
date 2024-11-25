import yaml
import os
from utils.config import load_config

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MESSAGES_FILE = os.path.join(BASE_DIR, 'text.yaml')


def load_messages():
    with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


messages = load_messages()


def get_message(key, **kwargs):
    """
    Получает сообщение по ключу и форматирует его с переданными параметрами.
    
    Args:
        key (str): Ключ сообщения
        **kwargs: Параметры для форматирования
    
    Returns:
        str: Отформатированное сообщение
    """
    message = messages.get(key, "Сообщение отсутствует.")
    if kwargs:
        try:
            return message.format(**kwargs)
        except KeyError:
            return message
    return message


def get_time_select_message(date):
    """
    Получает сообщение для выбора времени с указанной датой.
    
    Args:
        date (str): Дата из конфига (например, "14 ноября")
    
    Returns:
        str: Отформатированное сообщение
    """
    return get_message('time_select', date=date)


stickers = {
    "dobro": "CAACAgIAAxkBAAEKaudnRO32t3V_IteCwWVXc5A9RgErawAC6V8AAonNeUlv5p8lh0hchjYE",
    "info": "CAACAgIAAxkBAAEKaulnRO4EldI3dbeDE-qIp8INrJBkmAACpV4AAmGOgEmUdLtrxiP4ujYE",
    "time": "CAACAgIAAxkBAAEKavFnRO4T7zMIuH2GGmtfCAwKDNR5AgAC8lAAAkJceEnhg-3vVZ_dRDYE",
    "hurry": "CAACAgIAAxkBAAEKautnRO4LG0viPS4_33FGpOF-D78SIAACq1IAAjNNeElMK41fmzw7LjYE",
    "ideas": "CAACAgIAAxkBAAEKavNnRO5G8Ji_DnDQNzxMWwQF0opFxgACZFQAAiC1eEkvegnNpTEHMjYE",
    "okey": "CAACAgIAAxkBAAEKavdnRO5VXl3uYReLj1V5L7XilIlHfwACwFUAAgEYgUkJuWFR5BmGBzYE",
    "time1": "CAACAgIAAxkBAAEKau1nRO4Oo4edaU5I0Zb2xa9B0T1_5AACUFIAArCleEmSrLXDa-T1tjYE",
}
