from aiogram import Bot
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

with open("config.txt") as f:
    TOKEN = f.readline().split()[1]
    num_of_tables = int(f.readline().split()[1])
    threshold_minutes = int(f.readline().split()[1])
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
