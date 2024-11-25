import re
import sqlite3
import json

from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram import F
from random import choice, shuffle

from utils.fsm.states import ContactForm
from utils.bot import dp, bot
from utils.config import load_config
from view.text import get_message
from utils.fn import get_username_by_id, get_contacts, get_meetings_times
import utils.db.database as db
from view.keyboard import get_accept_kb, main_kb, times_kb, dates_keyboard, next_last_kb, zones_inline_kb

# Получаем зоны из конфига
config = load_config()
zones = config['meeting']['zones']

users = dict()


class Swipe:
    def __init__(self, msg: Message, items: list[list]):
        self.msg = msg
        shuffle(items)
        self.items = items
        self.size = len(items)
        self.index = 0
        self.telegram = 0
        users[msg.from_user.id] = self

    async def reply(self):
        self.msg = await self.msg.message.edit_text(text=self.items[self.index][0], parse_mode="HTML",
                                                    reply_markup=next_last_kb)
        if len(self.items[self.index][0]) > 8:
            self.telegram = self.items[self.index][1]

    async def next(self, clb):
        text_before = self.items[self.index][0]
        self.index = (self.index + 1) % self.size
        if text_before == self.items[self.index][0]:
            await clb.answer("Конец списка!")
        else:
            await clb.message.edit_text(text=self.items[self.index][0], parse_mode="HTML", reply_markup=next_last_kb)
            if len(self.items[self.index][0]) > 8:
                self.telegram = self.items[self.index][1]

    async def back(self, clb):
        text_before = self.items[self.index][0]
        self.index = (self.index - 1) % self.size
        if text_before == self.items[self.index][0]:
            await clb.answer("Конец списка!")
        else:
            await clb.message.edit_text(text=self.items[self.index][0], parse_mode="HTML", reply_markup=next_last_kb)
            if len(self.items[self.index][0]) > 8:
                self.telegram = self.items[self.index][1]

    async def choose(self, clb: Message, meeting_id, date_time):
        meeting = await db.get_meeting_by_id(meeting_id)
        telegram1, telegram2 = get_contacts(clb, meeting)
        username1, username2 = await get_username_by_id(telegram1), await get_username_by_id(telegram2)
        contact1 = await db.get_contact_by_telegram(telegram1)
        kb = get_accept_kb(meeting_id)

        company = f"компании {contact1['company_name']}" if contact1['company_name'] != 'отсутствует' else ""
        description = f"\nОписание: {contact1['description']} " if contact1['description'] != 'отсутствует' else ""

        txt = (
            f"Здравствуйте! Вам поступило предложение встретиться 🗨️\n"
            f"<b>{date_time[0]} ноября {date_time[1]}</b>\n"
            f"{contact1['contact_position']} {company} {contact1['contact_name']} "
            f"{description}\n\n"
            f"Телеграм: @{await get_username_by_id(contact1['telegram'])}\n"
            f"Телефон: {contact1['phone']}\n"
        )
        try:
            await bot.send_message(chat_id=str(self.items[self.index][1]), text=txt, reply_markup=kb, parse_mode="HTML")
            await self.msg.edit_text(text=f"Вы выбрали: {self.items[self.index][0]}\n\n"
                                          f"<b>Приглашение на встречу отправлено</b> @{username2}",
                                     parse_mode="HTML")
        except:
            await self.msg.edit_text(text=f"<b>Приглашение на встречу не было отправлено</b> @{username2}"
                                          f"\nПользователь запретил отправку сообщений.",
                                     parse_mode="HTML")
            await db.delete_contact_by_telegram(self.items[self.index][1])
        finally:
            await self.msg.answer(text=get_message('bot_info'), parse_mode="HTML", reply_markup=main_kb)

        users.pop(self.msg.from_user.id, None)


async def reply_swipe(msg: CallbackQuery, items: list):
    if not items:
        await msg.answer("Участники ещё не зарегистрировались!", show_alert=True)
        return
    swp = Swipe(msg, items)
    await swp.reply()


@dp.callback_query(F.data == "swipe.next")
async def swipe_next(clb: CallbackQuery):
    swp = users.get(clb.from_user.id)
    if not swp:
        await clb.answer("Сначала используйте команду /main.")
        return
    await swp.next(clb)


@dp.callback_query(F.data == "swipe.back")
async def swipe_back(clb: CallbackQuery):
    swp = users.get(clb.from_user.id)
    if not swp:
        await clb.answer("Сначала используйте команду /main.")
        return
    await swp.back(clb)


@dp.callback_query(StateFilter(ContactForm.set_meeting), F.data == "swipe.choose")
async def swipe_choose_contact(clb: CallbackQuery, state: FSMContext):
    swp = users.get(clb.from_user.id)
    if not swp:
        await clb.answer("Сначала используйте команду /main.")
        return
        
    user = await db.get_contact_by_telegram(str(swp.telegram))
    meeting_times = json.loads(user["meeting_times"])
    
    # Получаем времена встреч для всех дат
    times_dict = get_meetings_times(meeting_times)
    await state.update_data(times_dict=times_dict)
    await state.update_data(telegram2=swp.telegram)

    config = load_config()
    
    text = "<b>Выберите время встречи:</b>\n\n<b>Свободные даты и время:</b>\n"
    for date in config['meeting']['dates']:
        times = times_dict.get(date, [])
        text += f"🗓️ {date}: {', '.join(times)}\n\n"

    if user["speaker_place"]:
        text = f"<b>Спикер форума</b>\n" + text
        text += f"<b>Место встречи</b>: {user['speaker_place']}"
        message = await clb.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=dates_keyboard
        )
        await state.update_data(place=user["speaker_place"])
    else:
        text += "<b>Зоны встреч</b>:\n"
        for zone in config['meeting']['zones']:
            text += f"{zone}\n"
            
        message = await clb.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=zones_inline_kb
        )
        await state.set_state(ContactForm.set_place)


@dp.callback_query(StateFilter(ContactForm.set_place))
async def swipe_choose_place(clb: CallbackQuery, state: FSMContext):
    place = clb.data
    await state.update_data(place=place)
    message = await clb.message.edit_reply_markup(reply_markup=dates_keyboard)
    await state.set_state(ContactForm.set_meeting)


@dp.callback_query(lambda c: c.data in [date.split()[0] for date in load_config()['meeting']['dates']])
async def swipe_choose_date(clb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    times_dict = data["times_dict"]
    
    # Находим полную дату по числу
    config = load_config()
    selected_date = next(date for date in config['meeting']['dates'] 
                        if date.startswith(clb.data))
    
    times = times_dict.get(selected_date, [])

    await state.update_data(date=selected_date)
    message = await clb.message.edit_reply_markup(reply_markup=times_kb(times))

    await state.set_state(ContactForm.time_choose)


@dp.callback_query(StateFilter(ContactForm.time_choose), lambda c: re.match(r'^[0-2][0-9]:[0-5][0-9]$', c.data))
async def swipe_choose_time(clb: CallbackQuery, state: FSMContext):
    swp = users.get(clb.from_user.id)
    if not swp:
        await clb.answer("Сначала используйте команду /main.")
        return

    data = await state.get_data()
    telegram2 = data["telegram2"]

    date = data["date"]
    time = clb.data
    place = data["place"]

    data = {
        "date": date,
        "time": time,
        "contact1_id": str(clb.from_user.id),
        "contact2_id": str(telegram2),
        "place": place,
        "status": -1
    }
    try:
        meeting_id = await db.save_meeting_to_db(data)
    except Exception as e:
        print(e)
        await clb.message.answer(get_message("error"), parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
        return

    await swp.choose(clb, meeting_id, [date, time])
    await state.set_state(ContactForm.main)
