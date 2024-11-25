from aiogram import Bot
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from utils.config import load_config

config = load_config()
bot = Bot(token=config['bot']['api'])
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
ref = config['bot']['ref']
