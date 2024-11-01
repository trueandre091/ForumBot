from db.database import drop_table
import asyncio
from utils.excel import free_times

asyncio.run(drop_table())

