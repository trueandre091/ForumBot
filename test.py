from db.database import drop_table
import db.database as db
import asyncio
from utils.sheet import free_times

# asyncio.run(drop_table())

# asyncio.run(db.delete_meeting_by_id(23))
asyncio.run(db.migrate_meetings_table())

