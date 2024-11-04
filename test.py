import utils.db.database as db
import asyncio

# asyncio.run(drop_table())

# asyncio.run(db.delete_meeting_by_id(23))
asyncio.run(db.migrate_meetings_table())

