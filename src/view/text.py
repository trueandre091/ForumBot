import yaml
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MESSAGES_FILE = os.path.join(BASE_DIR, 'text.yaml')


def load_messages():
    with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


messages = load_messages()


def get_message(key, default="Сообщение отсутствует."):
    return messages.get(key, default)


stickers = {
    "dobro": "CAACAgIAAxkBAAIIEWcjrLdZn5tMewwl67oJvXMhJawuAAJiWwACj0EZSb3bxXqC4gPONgQ",
    "info": "CAACAgIAAxkBAAIIE2cjrNtoCc01fz7oTgywBODy0GdgAALRXAAC4dgZSeKexlkM8OwKNgQ",
    "time": "CAACAgIAAxkBAAIIFWcjrQ0RFzEBqoFtbr7DOkPlHnxHAAK6YAACKXQYSRJH5eefW3VcNgQ",
    "hurry": "CAACAgIAAxkBAAIIF2cjrSQcrN7yl2gPY8b3uZ1VvcH-AALWXwACro8ZSR7l5jStMTEfNgQ",
    "ideas": "CAACAgIAAxkBAAIIGWcjrS4ynx7iryvlidfp5kekqNsgAALnYgACfH0hSZ_D6MVlfs8pNgQ",
    "okey": "CAACAgIAAxkBAAIIG2cjrTl8f73K_tvX45Qa0OfF8YhpAAJsWAACiYggSUfEu1AyH0zcNgQ",
    "time1": "CAACAgIAAxkBAAIIHWcjrUa_HXKVmgbJpWVLLjuXqphXAAI7XQAC3xggSbTS10bU-UhhNgQ",
}
