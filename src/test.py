import datetime

import utils.db.database as db
import asyncio

CID = 0
MID = 0

aan = [
    "Отели", "Рестораны", "Туризм",
    "Пищевые производства", "Культурное наследие",
    "Информационные технологии"
]

contact_name = ""
contact_position = ""
company_name = ""
activity_area = ",".join(aan)
interests = ",".join(aan)
description = ""
website = ""
phone = ""
telegram = ""
times = list(map(str, range(10, 17)))
meeting_times_14 = ",".join(times)
meeting_times_15 = ",".join(times)
paid = None
speaker_place = ""

date = "15"
time = "14:00"
contact1_id = 0
contact2_id = 0
table_num = 0
place = "Зона b2b встреч - 2 этаж"
result = ""
comments = ""
status = 0


async def fn():
    # await db.a_add_contact(
    #     contact_name=contact_name,
    #     contact_position=contact_position,
    #     company_name=company_name,
    #     activity_area=activity_area,
    #     interests=interests,
    #     description=description if description else "отсутствует",
    #     website=website if website else "отсутствует",
    #     phone=phone,
    #     telegram=telegram,
    #     meeting_times_14=meeting_times_14 if meeting_times_14 else "отсутствуют",
    #     meeting_times_15=meeting_times_15 if meeting_times_15 else "отсутствуют",
    #     paid=paid,
    #     speaker_place=speaker_place if speaker_place else None
    # )

    # await db.a_update_contact(
    #     CID,
    #     contact_name=contact_name,
    #     contact_position=contact_position,
    #     company_name=company_name,
    #     activity_area=activity_area,
    #     interests=interests,
    #     description=description if description else "отсутствует",
    #     website=website if website else "отсутствует",
    #     phone=phone,
    #     telegram=telegram,
    #     meeting_times_14=meeting_times_14 if meeting_times_14 else "отсутствуют",
    #     meeting_times_15=meeting_times_15 if meeting_times_15 else "отсутствуют",
    #     paid=paid,
    #     speaker_place=speaker_place if speaker_place else None
    # )

    await db.a_add_meeting(
        date=date,
        time=time,
        contact1_id=contact1_id,
        contact2_id=contact2_id,
        table_num=table_num if table_num else None,
        place=place,
        result=result if result else None,
        comments=comments if comments else None,
        status=status,
        last_datetime=datetime.datetime.now()
    )

    # await db.a_update_meeting(
    #     MID,
    #     date=date,
    #     time=time,
    #     contact1_id=contact1_id,
    #     contact2_id=contact2_id,
    #     table_num=table_num if table_num else None,
    #     place=place,
    #     result=result if result else None,
    #     comments=comments if comments else None,
    #     status=status,
    #     last_datetime=datetime.datetime.now()
    # )

    # await db.delete_contact_by_telegram()
    # await db.delete_meeting_by_id(3)


asyncio.run(fn())
