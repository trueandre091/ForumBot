from datetime import datetime

from utils.bot import bot

pattern = r"^\d{2} \d{2}:[024]0$"


async def get_username_by_id(user_id: int):
    user = await bot.get_chat(user_id)
    return user.username


def format_time_ranges(hours):
    # Преобразуем строки в целые числа и сортируем
    hours = sorted(map(int, [hour for hour in hours if hour != "отсутствуют"]))

    ranges = []
    start = hours[0]
    end = hours[0]

    for hour in hours[1:]:
        if hour == end + 1:  # Если следующий час последовательный
            end = hour
        else:
            # Добавляем текущий диапазон в список, увеличивая его на 1
            if start == end:
                ranges.append(f"{start}:00-{end + 1}:00")  # Один час от start
            else:
                ranges.append(f"{start}:00-{end + 1}:00")  # Диапазон start-end + 1
            start = hour
            end = hour

    # Добавляем последний диапазон, увеличивая его на 1
    if start == end:
        ranges.append(f"{start}:00-{end + 1}:00")
    else:
        ranges.append(f"{start}:00-{end + 1}:00")

    return " ".join(ranges)


def is_time_in_range(time_str, time_range):
    # Преобразуем время и границы диапазона в объекты datetime
    time = datetime.strptime(time_str, "%H:%M")
    start, end = map(lambda t: datetime.strptime(t, "%H:%M"), time_range.split("-"))

    # Проверяем, попадает ли время в диапазон
    return start <= time <= end
