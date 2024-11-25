from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from utils.config import load_config

config = load_config()
zones = config['meeting']['zones']

activity_areas = [
    "Ресторан",
    "Кафе",
    "Бар",
    "Кофейня",
    "Столовая",
    "Фастфуд",
    "Кейтеринг",
    "Отель",
    "Хостел",
    "Гостиница",
    "Санаторий",
    "Пансионат",
    "Поставщик продуктов питания",
    "Поставщик оборудования",
    "Поставщик посуды и инвентаря",
    "Поставщик мебели",
    "Поставщик текстиля",
    "Поставщик услуг автоматизации",
    "Поставщик систем безопасности",
    "Поставщик клининговых услуг",
    "Другое"
]

def create_activity_area_kb():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=area)] for area in activity_areas
        ] + [[KeyboardButton(text="Выбор сделан ✍️")]],
        resize_keyboard=True
    )
    return keyboard

activity_area_kb = create_activity_area_kb()

def create_zones_kb():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=zone)] for zone in zones],
        resize_keyboard=True
    )
    return keyboard

zones_kb = create_zones_kb()

zones_buttons = [
    [InlineKeyboardButton(text=zones[0], callback_data=zones[0])],
    [InlineKeyboardButton(text=zones[1], callback_data=zones[1])],
    [InlineKeyboardButton(text=zones[2], callback_data=zones[2])]
]
zones_inline_kb = InlineKeyboardMarkup(inline_keyboard=zones_buttons)

time_names = ["10:00-11:00", "11:00-12:00",
              "12:00-13:00", "13:00-14:00",
              "14:00-15:00", "15:00-16:00",
              "16:00-17:00",
              "Выбор сделан ✍️"]
time_buttons = []
for i in range(len(time_names) - 1):
    if not i % 2:
        time_buttons.append([KeyboardButton(text=time_names[i])])
    else:
        time_buttons[-1].append(KeyboardButton(text=time_names[i]))
time_buttons.append([KeyboardButton(text=time_names[-1])])
time_kb = ReplyKeyboardMarkup(keyboard=time_buttons, resize_keyboard=True)

main_names = {
    "Изменить информацию о себе": "change_info",
    "Назначить встречу": "set_meeting",
    "Мои встречи": "meetings",
    "Обратиться к организатору": "help"
}
main_buttons = []
for name, data in main_names.items():
    main_buttons.append([InlineKeyboardButton(text=name, callback_data=data)])
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
            buttons[t // 4].append(InlineKeyboardButton(text=str(t + 1), callback_data=f"delete {t + 1}"))
        else:
            buttons.append([InlineKeyboardButton(text=str(t + 1), callback_data=f"delete {t + 1}")])
    buttons.append([InlineKeyboardButton(text="Назад", callback_data=f"main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


delete_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Удалить", callback_data=f"yes_delete")],
        [InlineKeyboardButton(text="В основное меню", callback_data="no_delete")],
        [InlineKeyboardButton(text="Оценить", callback_data="rate")]
    ]
)

next_last_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Посмотреть следующую визитку", callback_data="swipe.next")],
    [InlineKeyboardButton(text="Вернуться к предыдущей визитке", callback_data="swipe.back")],
    [InlineKeyboardButton(text="Выбрать", callback_data="swipe.choose")],
    [InlineKeyboardButton(text="В основное веню", callback_data="main_menu")]
])


def rating_kb(n):
    buttons = []
    for t in range(n):
        if t % 4:
            buttons[t // 4].append(InlineKeyboardButton(text=str(t + 1), callback_data=f"rate {t + 1}"))
        else:
            buttons.append([InlineKeyboardButton(text=str(t + 1), callback_data=f"rate {t + 1}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


dates_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="14 ноября", callback_data="14")],
        [InlineKeyboardButton(text="15 ноября", callback_data="15")]
    ]
)


def times_kb(times):
    names = [f"{a}" for a in times]
    keyboard = [[]]
    for name in names:
        if not len(keyboard[-1]) % 4:
            keyboard.append([])
        keyboard[-1].append(InlineKeyboardButton(text=name[:5], callback_data=name))
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
