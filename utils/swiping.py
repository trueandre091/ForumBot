import sqlite3

from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery, ReplyKeyboardRemove
from aiogram import F
import re

from fsm.states import ContactForm
from utils.bot import dp, bot
from utils.excel import free_times
from view.text import get_message
from utils.fn import format_time_ranges, is_time_in_range, pattern, get_username_by_id
import db.database as db
from view.keyboard import get_accept_kb, main_kb

next_last_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Назад", callback_data="swipe.back"),
     InlineKeyboardButton(text="Вперёд", callback_data="swipe.next")],
    [InlineKeyboardButton(text="Выбрать", callback_data="swipe.choose")]
])

users = dict()


class Swipe:
    def __init__(self, msg: Message, items: list[list]):
        self.msg = msg
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
        await self.msg.edit_text(text=f"Вы выбрали: {self.items[self.index][0]}\n\n"
                                      f"Приглашение на встречу отправлено @{await get_username_by_id(self.items[self.index][1])}",

                                 parse_mode="HTML")
        await self.msg.answer(
            text=get_message('bot_info'), parse_mode="HTML", reply_markup=main_kb
        )
        tmp = await db.get_contact_by_telegram(str(clb.from_user.id))
        kb = get_accept_kb(meeting_id)

        company = f"компании {tmp['company_name']} " if tmp['company_name'] != 'отсутствует' else ""
        description = f"\nОписание: {tmp['description']} " if tmp['description'] != 'отсутствует' else ""

        txt = (
            f"Здравствуйте! Вам поступило предложение встретиться 🗨️\n"
            f"<b>{date_time[0]} ноября {date_time[1]}</b>\n"
            f"{tmp['contact_position']} {company} {tmp['contact_name']} "
            f"{description}\n\n"
            f"Телеграм: @{await get_username_by_id(tmp['telegram'])}\n"
            f"Телефон: {tmp['phone']}\n"
        )

        await bot.send_message(chat_id=str(self.items[self.index][1]), text=txt, reply_markup=kb, parse_mode="HTML")

        users.pop(self.msg.from_user.id, None)


async def reply_swipe(msg: CallbackQuery, items: list):
    if not items:
        await msg.answer("Список пуст.")
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
    meeting_times_14 = user["meeting_times_14"].split(",")
    meeting_times_15 = user["meeting_times_15"].split(",")

    ft = await free_times()
    times_14 = [i[3:] for i in ft.keys() if i[:2] == "14" and i[3:5] in meeting_times_14]
    times_15 = [i[3:] for i in ft.keys() if i[:2] == "15" and i[3:5] in meeting_times_15]
    await state.update_data(times_14=times_14)
    await state.update_data(times_15=times_15)

    message_id = await clb.message.reply(
        text=f"<b>Выберите время встречи:</b>\n\n<b>Свободные даты и время:</b>\n🗓️ 14 ноября: {', '.join(times_14)}\n\n"
             f"🗓️ 15 ноября: {', '.join(times_15)}\n\n", parse_mode="HTML")
    await state.set_state(ContactForm.time_choose)
    await state.update_data(info_msg_id=message_id.message_id)
    await reply_swipe(clb,
                      [[f"14 ноября {a}", swp.telegram, a] for a in times_14] + [[f"15 ноября {a}", swp.telegram, a] for
                                                                                 a in times_15])


@dp.callback_query(StateFilter(ContactForm.time_choose), F.data == "swipe.choose")
async def swipe_choose_time(clb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await bot.delete_message(chat_id=clb.from_user.id, message_id=data['info_msg_id'])
    await state.clear()

    swp = users.get(clb.from_user.id)
    date_time = swp.items[swp.index][0]
    if not swp:
        await clb.message.answer("Сначала используйте команду /main.")
        return
    user = await db.get_contact_by_telegram(str(swp.items[swp.index][1]))

    date = date_time.split()[0]
    time = date_time.split()[2]

    ft = await free_times()
    table = ft[" ".join([date, time])].pop()

    data = {
        "date": date,
        "time": time,
        "contact1_id": str(clb.from_user.id),
        "contact2_id": str(user["telegram"]),
        "table_num": table,
        "status": -1
    }
    try:
        meeting_id = await db.save_meeting_to_db(data)
    except sqlite3.IntegrityError:
        try:
            meeting_id = (await db.get_meeting_by_datetime_and_table(date=date, time=time, table_num=table))['id']
        except Exception as e:
            print(e)
            await clb.message.answer(get_message("error"), parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
            return

    await swp.choose(clb, meeting_id, [date, time])
    await state.set_state(ContactForm.main)
