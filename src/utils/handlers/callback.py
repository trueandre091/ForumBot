from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ReplyKeyboardRemove

import utils.db.database as db
from utils.fsm.states import ContactForm
from utils.bot import dp, bot
from utils.config import load_config
from utils.fn import get_username_by_id, get_contacts, get_meetings_message, get_card
from utils.handlers.swiping import reply_swipe
from view.text import get_message, stickers
from view.keyboard import delete_kb, number_kb, main_kb, rating_kb
import json

# Где нужен threshold_minutes, получаем его из конфига:
config = load_config()
threshold_minutes = config['settings']['threshold_minutes']


@dp.callback_query(lambda c: c.data == 'change_info')
async def callback_change_info(callback_query: CallbackQuery, state: FSMContext):
    """
    Обработчик для изменения информации - перенаправляет на регистрацию
    """
    try:
        # Очищаем состояние
        await state.clear()
        
        # От��равляем сообщение о начале регистрации
        await callback_query.message.answer(
            get_message("forum_info"), 
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )
        
        # Запрашиваем ФИО
        await callback_query.message.answer(
            get_message("fio"),
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )
        
        # Устанавливаем начальное состояние регистрации
        await state.set_state(ContactForm.contact_name)
        
    except Exception as e:
        print(f"Error in callback_change_info: {e}")
        await callback_query.message.answer(
            get_message("error"),
            parse_mode="HTML"
        )


@dp.callback_query(lambda c: c.data == 'help')
async def callback_change_info(callback_query: CallbackQuery):
    await callback_query.answer("Обратиться к организатору")
    await callback_query.message.answer(text=get_message("help"), reply_markup=ReplyKeyboardRemove())


@dp.callback_query(lambda c: c.data == 'meetings')
async def callback_change_info(callback_query: CallbackQuery, state: FSMContext):
    meetings = await db.get_meetings_with_status(0)
    if not meetings:
        await callback_query.answer("Не назначено встреч", show_alert=True)
        return
    await callback_query.answer("Мои встречи")
    meetings = sorted(meetings, key=lambda x: x["date"])
    meetings = [meeting for meeting in meetings
                if meeting["contact1_id"] == callback_query.from_user.id or
                meeting["contact2_id"] == callback_query.from_user.id]
    if not meetings:
        await callback_query.answer("Вы не назначили встреч.\nЗапланируйте встречу, нажав 'Назначить встречу'", show_alert=True)
        return
    await state.update_data(meetings_list=meetings, clb=callback_query)
    message = await get_meetings_message(callback_query, meetings)

    try:
        await callback_query.message.edit_text(text=message, reply_markup=number_kb(len(meetings)), parse_mode="HTML")
    except TelegramBadRequest:
        pass


@dp.callback_query(lambda c: c.data[:7] == "delete ")
async def delete_meeting(clb: CallbackQuery, state: FSMContext):
    await clb.answer(f"Выбрана встреча номер {int(clb.data[7:])}")
    data = await state.get_data()
    meeting = data["meetings_list"][int(clb.data[7:]) - 1]

    telegram1, telegram2 = get_contacts(clb, meeting)
    contact2 = await db.get_contact_by_telegram(telegram2)
    if not contact2:
        await clb.message.answer(text=get_message("info_error"), parse_mode="HTML")
        return

    company = f"компании {contact2['company_name']}" if contact2['company_name'] != '/skip' else ""
    description = f"\nОписание: {contact2['description']}" if contact2['description'] != '/skip' else ""

    message = (
        f"🕑 <b>{meeting['date']} ноября {meeting['time']}</b>\n"
        f"Участник: {contact2['contact_position']} {company} {contact2['contact_name']}"
        f"{description}\n\n"
        f"Телеграм: @{await get_username_by_id(contact2['telegram'])}\n"
        f"Телефон: {contact2['phone']}\n"
        f"<b>Место встречи: {meeting['place']}</b>\n\n"
    )

    await state.update_data(button_number=int(clb.data[7:]), meetings_clb=clb)
    await clb.message.edit_text(text=message + "Вы хотите отменить встречу или оценить, как она прошла?",
                                reply_markup=delete_kb, parse_mode="HTML")


@dp.callback_query(lambda c: c.data == "no_delete")
async def no_delete(callback_query: CallbackQuery, state: FSMContext):
    meetings = await db.get_meetings_with_status(0)
    if not meetings:
        await callback_query.answer("Нет встреч")
        await callback_query.answer("Основное меню")
        await state.clear()
        await callback_query.message.edit_text(text=get_message('bot_info'), parse_mode="HTML", reply_markup=main_kb)
        await state.set_state(ContactForm.main)
        return
    await callback_query.answer("Мои встречи")

    meetings = sorted(meetings, key=lambda x: int(x["date"]) * 21 + (int(x["time"][:2])) * 3 + int(x["time"][3]) // 2)
    meetings = [meeting for meeting in meetings
                if meeting["contact1_id"] == callback_query.from_user.id or
                meeting["contact2_id"] == callback_query.from_user.id]
    if not meetings:
        await callback_query.answer("Вы не назначили встреч.\nЗапланируйте встречу, нажав 'Назначить встречу'", show_alert=True)
        return
    await state.update_data(meetings_list=meetings, clb=callback_query)
    message = await get_meetings_message(callback_query, meetings)

    await callback_query.message.edit_text(text=message, reply_markup=number_kb(len(meetings)), parse_mode="HTML")


@dp.callback_query(lambda c: c.data == "yes_delete")
async def yes_delete(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    meeting = data["meetings_list"][data["button_number"] - 1]

    telegram1, telegram2 = get_contacts(callback_query, meeting)
    username1, username2 = await get_username_by_id(telegram1), await get_username_by_id(telegram2)
    date = meeting["date"]
    time = meeting["time"]

    await db.update_meeting_status(meeting['id'], 1)
    await callback_query.answer("Удалено успешно")
    message = f"Встреча @{username1} и @{username2} {date} в {time} отклонена"


    meetings = await db.get_meetings_with_status(0)

    if not meetings:
        await callback_query.answer("Нет встреч", show_alert=True)
        await state.clear()
        await callback_query.message.edit_text(text=message, parse_mode="HTML")
        await callback_query.message.answer(text=get_message("bot_info"), parse_mode="HTML", reply_markup=main_kb)
        return

    meetings = sorted(meetings, key=lambda x: (x["date"], x["time"]))
    meetings = [meeting for meeting in meetings
                if meeting["contact1_id"] == callback_query.from_user.id or
                meeting["contact2_id"] == callback_query.from_user.id]
    if not meetings:
        await callback_query.answer("Вы не назначили встреч.\nЗапланируйте встречу, нажав 'Назначить встречу'", show_alert=True)
        return
    await state.update_data(meetings_list=meetings, clb=callback_query)
    message = await get_meetings_message(callback_query, meetings)

    await callback_query.message.edit_text(text=message, reply_markup=number_kb(len(meetings)), parse_mode="HTML")

    try:
        await bot.send_message(chat_id=telegram1, text=message)
    except TelegramForbiddenError:
        pass
    try:
        await bot.send_message(chat_id=telegram2, text=message)
    except TelegramForbiddenError:
        pass


@dp.callback_query(lambda c: c.data == 'rate')
async def callback_rate(clb: CallbackQuery, state: FSMContext):
    await clb.message.delete()
    data = await state.get_data()
    meeting = data["meetings_list"][data["button_number"] - 1]
    telegram1, telegram2 = get_contacts(clb, meeting)
    username2 = await get_username_by_id(telegram2)

    message = f"Поставьте оценку прошедшей встрече c @{username2}!"
    await clb.message.answer(text=message, reply_markup=rating_kb(5))


@dp.callback_query(lambda c: 'rate ' in str(c.data))
async def callback_rate_end(clb: CallbackQuery, state: FSMContext):
    await clb.message.delete()
    data = await state.get_data()
    meeting = data["meetings_list"][data["button_number"] - 1]
    telegram1, telegram2 = get_contacts(clb, meeting)
    await db.update_meeting_status(meeting['id'], 1)
    rating = clb.data.split()[1]
    await db.update_meeting(meeting['id'], result=rating)

    await clb.message.answer(text=get_message('bot_info'), parse_mode="HTML", reply_markup=main_kb)
    await clb.message.answer(text="Спасибо за оценку!")
    try:
        await bot.send_message(chat_id=telegram2, text=f"Встрече поставили оценку! {rating}/5")
    except TelegramForbiddenError:
        pass


@dp.callback_query(lambda c: c.data == 'main_menu')
async def callback_main(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer("Основное меню")
    await state.clear()
    await callback_query.message.edit_text(text=get_message('bot_info'), parse_mode="HTML", reply_markup=main_kb)
    user = await db.get_contact_by_telegram(str(callback_query.from_user.id))
    if not user:
        await callback_query.message.answer(text=get_message("info_error"))
        return
    await state.set_state(ContactForm.main)


@dp.callback_query(lambda c: c.data == 'set_meeting')
async def callback_change_info(callback_query: CallbackQuery, state: FSMContext):
    user = await db.get_contact_by_telegram(str(callback_query.from_user.id))
    if not user:
        await callback_query.message.answer(text=get_message("info_error"))
        return
    interests = json.loads(user["interests"], strict=False)
    meeting_times = json.loads(user["meeting_times"], strict=False)
    
    users = await db.get_contacts_by_meeting_times_and_activity_area(
        meeting_times,
        interests,
        callback_query.from_user.id
    )
    
    await state.set_state(ContactForm.set_meeting)
    await reply_swipe(callback_query, [[await get_card(user), user['telegram']] for user in users])


@dp.callback_query(lambda c: "YES " in c.data)
async def callback_YES(callback_query: CallbackQuery, state: FSMContext):
    data = callback_query.data.split()
    meeting = await db.get_meeting_by_id(int(data[1]))
    await callback_query.answer("Приглашение принято")

    telegram1, telegram2 = get_contacts(callback_query, meeting)
    username1, username2 = await get_username_by_id(telegram1), await get_username_by_id(telegram2)
    date = meeting["date"]
    time = meeting["time"]
    try:
        await db.update_meeting_status(int(data[1]), 0)
    except Exception as e:
        print(e)
        await callback_query.message.answer(text=get_message("error"), parse_mode="HTML")

    message = f"Назначена встреча @{username1} и @{username2} {date} в {time}, место встречи: <b>{meeting['place']}</b>"
    try:
        await bot.send_message(chat_id=telegram2, text=message, parse_mode="HTML")
        await bot.send_sticker(chat_id=telegram2, sticker=stickers["okey"])
    except:
        pass

    await state.clear()
    await callback_query.message.delete()
    await callback_query.message.answer(text=message, parse_mode="HTML")
    await callback_query.message.answer_sticker(stickers["okey"])
    await state.set_state(ContactForm.main)
    await state.update_data(clb=callback_query)


@dp.callback_query(lambda c: "NO " in c.data)
async def callback_NO(callback_query: CallbackQuery, state: FSMContext):
    data = callback_query.data.split()
    meeting = await db.get_meeting_by_id(int(data[1]))
    await callback_query.answer("Приглашение отклонено")

    telegram1 = meeting["contact1_id"]
    telegram2 = meeting["contact2_id"]
    username1 = await get_username_by_id(telegram1)
    username2 = await get_username_by_id(telegram2)
    date = meeting["date"]
    time = meeting["time"]

    try:
        await db.update_meeting_status(meeting['id'], 2)
    except Exception as e:
        print(e)
        await callback_query.message.answer(text=get_message("error"), parse_mode="HTML")

    message = f"Встреча @{username1} и @{username2} {date} в {time} отклонена"

    await callback_query.message.edit_text(text=message)
    await callback_query.message.answer_sticker(stickers["time"])
    try:
        await bot.send_message(chat_id=telegram1, text=message)
        await bot.send_sticker(chat_id=telegram1, sticker=stickers["time"])
    except:
        pass

    await state.clear()
    await state.set_state(ContactForm.main)
    await state.update_data(clb=callback_query)
