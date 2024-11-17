from aiogram import Bot
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

with open("config.txt", encoding="utf-8") as f:
    TOKEN = f.readline().split()[1]
    num_of_tables = int(f.readline().split()[1])
    threshold_minutes = int(f.readline().split()[1])
    admins = [int(i) for i in (f.readline().split())[1:]]
    ref = f.readline().split()[1]
    f.readline()
    zones = [i for i in (f.readline().split(","))]
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
