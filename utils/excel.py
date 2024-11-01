from google.connection import connect_to_google_sheet

from utils.bot import num_of_tables
import db.database as db


def to_char(n: int):
    if n <= ord('Z'):
        return chr(n)
    return 'A'+chr(ord('A') + n - ord('Z') - 1)


def fill_table():
    sheet = connect_to_google_sheet()
    sheet.update_acell('B2', "14 ноября")
    sheet.update(f"B3:B{2+num_of_tables}", [[f"Стол №{i}"] for i in range(1, num_of_tables+1)])  # i from 0 to num-1
    sheet.update_acell('Y2', "15 ноября")
    sheet.update(f"Y3:Y{2 + num_of_tables}", [[f"Стол №{i}"] for i in range(1, num_of_tables+1)])
    sheet.update("C2:W2", [[f"{10+i//3}:{(i%3)*2}0" for i in range(21)]])
    sheet.update("Z2:AT2", [[f"{10+i//3}:{(i%3)*2}0" for i in range(21)]])


def insert(table: int, time: str, date: int, contact_1: str, contact_2: str) -> None:
    connect_to_google_sheet().update_acell(
        f"{to_char(37 + int(time[3]) // 2 + (int(time[0:2])) * 3 + (date == 15) * 23)}{table + 2}",
        f"Занято (@{contact_1} и @{contact_2})")


def delete(table: int, time: str, date: int) -> None:
    connect_to_google_sheet().update_acell(
        f"{to_char(37 + int(time[3]) // 2 + (int(time[0:2])) * 3 + (date == 15) * 23)}{table + 2}", ""
    )


async def free_times():
    tmp = await db.get_meetings_with_status_zero()
    lst = [set(range(1, num_of_tables+1))]*42
    for d in tmp:
        lst[(int(d["time"][0:2])-10)*3+int(d["time"][3])//2+21*(d["date"] == "15")].discard(d["table_num"])
    res = dict()
    for time in range(42):
        if len(lst[time]):
            res[f"{time//21+14} 1{(time%21)//3}:{time%3*2}0"] = lst[time]
    return res
