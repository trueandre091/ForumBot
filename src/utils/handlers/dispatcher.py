import re
import sqlite3

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from aiogram.types import ReplyKeyboardRemove
from aiogram import Router

from utils.bot import dp
from utils.fn import format_time_ranges, pattern_phone
from utils.fsm.states import ContactForm
import utils.db.database as db
from view.text import get_message, stickers
from view.keyboard import activity_area_kb, time_kb, main_kb, activity_area_names

router = Router()


@router.message(Command("main"))
async def main(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(text=get_message("bot_info"), parse_mode="HTML", reply_markup=main_kb)
    await state.set_state(ContactForm.main)


@router.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer_sticker(stickers["dobro"])
    await message.answer(get_message("forum_info"), parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
    await message.answer("1/10 Введите ФИО:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(ContactForm.contact_name)


@router.message(StateFilter(ContactForm.contact_name))
async def process_contact_name(message: types.Message, state: FSMContext):
    contact_name = message.text
    words = contact_name.split()
    if len(words) != 3:
        await message.answer("Введите ФИО в формате Иванов Иван Иванович:")
        return
    await state.update_data(contact_name=contact_name)
    await message.answer("2/10 Введите Вашу должность в компании, если компании нет - 'Физ. лицо':",
                         reply_markup=ReplyKeyboardRemove())
    await state.set_state(ContactForm.contact_position)


@router.message(StateFilter(ContactForm.contact_position))
async def process_contact_position(message: types.Message, state: FSMContext):
    contact_position = message.text
    await state.update_data(contact_position=contact_position)
    await message.answer("3/10 Введите название компании\n\nНеобязательно, для пропуска нажмите /skip :",
                         reply_markup=ReplyKeyboardRemove())
    await state.set_state(ContactForm.company_name)


@router.message(StateFilter(ContactForm.company_name))
async def process_company_name(message: types.Message, state: FSMContext):
    company_name = message.text
    await state.update_data(company_name=company_name)
    await message.answer("4/10 Выберите сферы вашей деятельности (обязательно):", reply_markup=activity_area_kb)
    await state.set_state(ContactForm.activity_area)


@router.message(StateFilter(ContactForm.activity_area))
async def process_activity_area(message: types.Message, state: FSMContext):
    activity_area = message.text
    data = await state.get_data()
    if activity_area == "Выбор сделан ✍️":
        if "activity_area" not in data:
            await message.answer("4/10 Выберите сферы вашей деятельности (обязательно):", reply_markup=activity_area_kb)
            return

        await message.answer("5/10 Выберите сферы в которых вы заинтересованы (обязательно):",
                             reply_markup=activity_area_kb)
        await state.set_state(ContactForm.interests)
        return

    if "activity_area" in data:
        data["activity_area"].append(activity_area) if activity_area in activity_area_names else None
        data["activity_area"] = list(set(data["activity_area"]))
        await state.update_data(activity_area=data["activity_area"])
    else:
        await state.update_data(activity_area=[activity_area]) if activity_area in activity_area_names else None


@router.message(StateFilter(ContactForm.interests))
async def process_interests(message: types.Message, state: FSMContext):
    interests = message.text
    data = await state.get_data()
    if interests == "Выбор сделан ✍️":
        if "interests" not in data:
            await message.answer("5/10 Выберите сферы в которых вы заинтересованы (обязательно):",
                                 reply_markup=activity_area_kb)
            return
        await message.answer("6/10 Введите описание\n\nНеобязательно, для пропуска нажмите /skip :",
                             reply_markup=ReplyKeyboardRemove())
        await state.set_state(ContactForm.description)
        return

    if "interests" in data:
        data["interests"].append(interests) if interests in activity_area_names else None
        data["interests"] = list(set(data["interests"]))
        await state.update_data(interests=data["interests"])
    else:
        await state.update_data(interests=[interests]) if interests in activity_area_names else None


@router.message(StateFilter(ContactForm.description))
async def process_description(message: types.Message, state: FSMContext):
    description = message.text
    await state.update_data(description=description)  # Сохраняем описание
    await message.answer("7/10 Введите веб-сайт\n\nНеобязательно, для пропуска нажмите /skip :",
                         reply_markup=ReplyKeyboardRemove())
    await state.set_state(ContactForm.website)  # Переход к следующему состоянию


@router.message(StateFilter(ContactForm.website))
async def process_website(message: types.Message, state: FSMContext):
    website = message.text
    await state.update_data(website=website)  # Сохраняем веб-сайт
    await message.answer("8/10 Введите номер телефона (обязательно):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(ContactForm.phone)  # Переход к следующему состоянию


@router.message(StateFilter(ContactForm.phone))
async def process_phone(message: types.Message, state: FSMContext):
    phone = message.text
    if not re.match(pattern_phone, phone):
        await message.answer("8/10 Введите номер телефона (обязательно):", reply_markup=ReplyKeyboardRemove())
        return
    telegram = message.from_user.id
    await state.update_data(phone=phone)
    await state.update_data(telegram=telegram)
    await message.answer("9/10 Введите ваши временные возможности на форуме 14 ноября:", reply_markup=time_kb)
    await state.set_state(ContactForm.meeting_times_14)  # Переход к следующему состоянию


@router.message(StateFilter(ContactForm.meeting_times_14))
async def process_meeting_times_14(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if message.text == "Выбор сделан ✍️":
        if "meeting_times_14" not in data:
            await state.update_data(meeting_times_14=[None])
        await message.answer("10/10 Введите ваши временные возможности на форуме 15 ноября:")
        await state.set_state(ContactForm.meeting_times_15)  # Переход к следующему состоянию
        return

    if "meeting_times_14" in data:
        data["meeting_times_14"].append(message.text[:2])
        data["meeting_times_14"] = list(set(data["meeting_times_14"]))
        await state.update_data(meeting_times_14=data["meeting_times_14"])
    else:
        await state.update_data(meeting_times_14=[message.text[:2]])


@router.message(StateFilter(ContactForm.meeting_times_15))
async def process_meeting_times_15(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if message.text == "Выбор сделан ✍️":
        if "meeting_times_15" not in data:
            await state.update_data(meeting_times_15=[None])

        await state.set_state(ContactForm.main)
        data = await state.get_data()

        contact_name = data.get('contact_name')
        contact_position = data.get('contact_position')
        company_name = data['company_name'] = data.get('company_name') if data.get(
            'company_name') != "/skip" else "отсутствует"
        activity_area = ",".join(data.get('activity_area'))
        interests = ",".join(data.get('interests'))
        description = data['description'] = data.get('description') if data.get(
            'description') != "/skip" else "отсутствует"
        website = data['website'] = data.get('website') if data.get('website') != "/skip" else "отсутствует"
        phone = data.get('phone')
        telegram = str(data.get('telegram')) + f" ({message.from_user.username})"
        time_14 = data.get('meeting_times_14')
        time_15 = data.get('meeting_times_15')
        time_14 = format_time_ranges(time_14) if None not in time_14 else "отсутствуют"
        time_15 = format_time_ranges(time_15) if None not in time_15 else "отсутствуют"

        msg = (f"<b>Данные успешно сохранены!</b>\n"
               f"ФИО контактного лица: {contact_name}\n"
               f"Должность: {contact_position}\n"
               f"Название компании: {company_name}\n"
               f"Сфера деятельности: {activity_area}\n"
               f"Интересы: {interests}\n"
               f"Описание: {description}\n"
               f"Сайт компании: {website}\n"
               f"Номер телефона: {phone}\n"
               f"Телеграм: {telegram}\n"
               "\n<b>Временные возможности:</b>\n"
               f"Время (14 ноября): {time_14}\n"
               f"Время (15 ноября): {time_15}\n")
        await message.answer(text=msg, parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
        try:
            await db.save_contact_to_db(data)
        except sqlite3.IntegrityError as e:
            print(e)
            try:
                await db.update_contact_in_db(data)
            except Exception as e:
                print(e)
                await message.answer(get_message("error"), parse_mode="HTML", reply_markup=ReplyKeyboardRemove())

        await message.answer_sticker(stickers["info"])
        await message.answer(text=get_message("bot_info"), parse_mode="HTML", reply_markup=main_kb)
        return

    if "meeting_times_15" in data:
        data["meeting_times_15"].append(message.text[:2])
        data["meeting_times_15"] = list(set(data["meeting_times_15"]))
        await state.update_data(meeting_times_15=data["meeting_times_15"])
    else:
        await state.update_data(meeting_times_15=[message.text[:2]])


# ----------------------------------------------mettings--------------------------------------------------


dp.include_router(router)
