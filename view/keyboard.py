from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

activity_area_buttons = [
    [KeyboardButton(text="Отели"), KeyboardButton(text="Рестораны"), KeyboardButton(text="Туризм")],
    [KeyboardButton(text="Пищевые производства")], [KeyboardButton(text="Информационные технологии")],
    [KeyboardButton(text="❌ Завершить выбор ❌")]
]
activity_area_kb = ReplyKeyboardMarkup(keyboard=activity_area_buttons, resize_keyboard=True)

time_buttons = [
    [KeyboardButton(text="10:00-11:00"), KeyboardButton(text="11:00-12:00")],
    [KeyboardButton(text="12:00-13:00"), KeyboardButton(text="13:00-14:00")],
    [KeyboardButton(text="14:00-15:00"), KeyboardButton(text="15:00-16:00")],
    [KeyboardButton(text="16:00-17:00")],
    [KeyboardButton(text="❌ Завершить выбор / Отсутствуют ❌")]
]
time_kb = ReplyKeyboardMarkup(keyboard=time_buttons, resize_keyboard=True)

main_buttons = [
    [InlineKeyboardButton(text="Изменить информацию о себе", callback_data="change_info")],
    [InlineKeyboardButton(text="Назначить встречу", callback_data="set_meeting")],
    [InlineKeyboardButton(text="Мои встречи", callback_data="meetings")],
    [InlineKeyboardButton(text="Обратиться к организатору", callback_data="help")]
]
main_kb = InlineKeyboardMarkup(inline_keyboard=main_buttons)


def get_accept_kb(meeting_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Согласиться", callback_data=f"YES {meeting_id}")],
            [InlineKeyboardButton(text="Отклонить", callback_data=f"NO {meeting_id}")]
        ]
    )


def number_kb(n: int):
    buttons = []
    for t in range(n):
        if t % 4:
            buttons[t//4].append(InlineKeyboardButton(text=str(t+1), callback_data=f"delete {t+1}"))
        else:
            buttons.append([InlineKeyboardButton(text=str(t+1), callback_data=f"delete {t+1}")])
    buttons.append([InlineKeyboardButton(text="Назад", callback_data=f"main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


delete_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Удалить", callback_data=f"yes_delete")],
        [InlineKeyboardButton(text="Назад", callback_data="no_delete")],
        [InlineKeyboardButton(text="Оценить", callback_data="rate")]
    ]
)


def rating_kb(n):
    buttons = []
    for t in range(n):
        if t % 4:
            buttons[t // 4].append(InlineKeyboardButton(text=str(t + 1), callback_data=f"rate {t + 1}"))
        else:
            buttons.append([InlineKeyboardButton(text=str(t + 1), callback_data=f"rate {t + 1}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

