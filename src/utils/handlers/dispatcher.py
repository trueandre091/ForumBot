import re
import sqlite3

from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from aiogram.types import ReplyKeyboardRemove

from utils.bot import dp, ref
from utils.fn import format_time_ranges, pattern_phone
from utils.fsm.states import ContactForm
import utils.db.database as db
from view.text import get_message, stickers, get_time_select_message
from view.keyboard import activity_area_kb, time_kb, main_kb, activity_areas, zones_kb
from utils.config import load_config

router = Router()


@router.message(Command("main"))
async def main(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(text=get_message("bot_info"), parse_mode="HTML", reply_markup=main_kb)
    await state.set_state(ContactForm.main)


@router.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    if " " in message.text:
        speaker = message.text.split()[1]
        if speaker == ref:
            await state.update_data(speaker=True)
    else:
        await state.update_data(speaker=False)
    await message.answer_sticker(stickers["dobro"])
    await message.answer(get_message("forum_info"), parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
    await message.answer(get_message("fio"), parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
    await state.set_state(ContactForm.contact_name)


@router.message(StateFilter(ContactForm.contact_name))
async def process_contact_name(message: types.Message, state: FSMContext):
    contact_name = message.text
    words = contact_name.split()
    if len(words) != 3:
        await message.answer(get_message("fio_error"))
        return
    await state.update_data(contact_name=contact_name)
    await message.answer(get_message("position"), parse_mode="HTML",
                         reply_markup=ReplyKeyboardRemove())
    await state.set_state(ContactForm.contact_position)


@router.message(StateFilter(ContactForm.contact_position))
async def process_contact_position(message: types.Message, state: FSMContext):
    contact_position = message.text
    await state.update_data(contact_position=contact_position)
    await message.answer(get_message("company_name"), parse_mode="HTML",
                         reply_markup=ReplyKeyboardRemove())
    await state.set_state(ContactForm.company_name)


@router.message(StateFilter(ContactForm.company_name))
async def process_company_name(message: types.Message, state: FSMContext):
    company_name = message.text
    await state.update_data(company_name=company_name)
    await message.answer(get_message("activity_area"), parse_mode="HTML", reply_markup=activity_area_kb)
    await state.set_state(ContactForm.activity_area)


@router.message(StateFilter(ContactForm.activity_area))
async def process_activity_area(message: types.Message, state: FSMContext):
    activity_area = message.text
    data = await state.get_data()
    if activity_area == "Выбор сделан ✍️":
        if "activity_area" not in data:
            await message.answer(get_message("activity_area"), parse_mode="HTML", reply_markup=activity_area_kb)
            return

        await message.answer(get_message("interests"), parse_mode="HTML",
                             reply_markup=activity_area_kb)
        await state.set_state(ContactForm.interests)
        return

    if "activity_area" in data:
        data["activity_area"].append(activity_area) if activity_area in activity_areas else None
        data["activity_area"] = list(set(data["activity_area"]))
        await state.update_data(activity_area=data["activity_area"])
    else:
        await state.update_data(activity_area=[activity_area]) if activity_area in activity_areas else None


@router.message(StateFilter(ContactForm.interests))
async def process_interests(message: types.Message, state: FSMContext):
    interests = message.text
    data = await state.get_data()
    if interests == "Выбор сделан ✍️":
        if "interests" not in data:
            await message.answer(get_message("interests"), parse_mode="HTML",
                                 reply_markup=activity_area_kb)
            return
        await message.answer(get_message("description"), parse_mode="HTML",
                             reply_markup=ReplyKeyboardRemove())
        await state.set_state(ContactForm.description)
        return

    if "interests" in data:
        data["interests"].append(interests) if interests in activity_areas else None
        data["interests"] = list(set(data["interests"]))
        await state.update_data(interests=data["interests"])
    else:
        await state.update_data(interests=[interests]) if interests in activity_areas else None


@router.message(StateFilter(ContactForm.description))
async def process_description(message: types.Message, state: FSMContext):
    description = message.text
    await state.update_data(description=description)  # Сохраняем описание
    await message.answer(get_message("website"), parse_mode="HTML",
                         reply_markup=ReplyKeyboardRemove())
    await state.set_state(ContactForm.website)  # Переход к следующему состоянию


@router.message(StateFilter(ContactForm.website))
async def process_website(message: types.Message, state: FSMContext):
    website = message.text
    await state.update_data(website=website)
    await message.answer(get_message("phone"), parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
    await state.set_state(ContactForm.phone)


@router.message(StateFilter(ContactForm.phone))
async def process_phone(message: types.Message, state: FSMContext):
    phone = message.text
    if not re.match(pattern_phone, phone):
        await message.answer(get_message("phone"), parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
        return
    
    telegram = message.from_user.id
    await state.update_data(phone=phone)
    await state.update_data(telegram=telegram)
    await state.update_data(meeting_times={})
    
    data = await state.get_data()
    if data.get("speaker", False):
        await message.answer(get_message("speaker"), parse_mode="HTML", reply_markup=zones_kb)
        await state.set_state(ContactForm.speaker)
    else:
        config = load_config()
        dates = config['meeting']['dates']
        await state.update_data(remaining_dates=dates.copy())
        first_date = dates[0]
        await message.answer(
            get_time_select_message(first_date), 
            parse_mode="HTML", 
            reply_markup=time_kb
        )
        await state.set_state(ContactForm.meeting_times)


@router.message(StateFilter(ContactForm.meeting_times))
async def process_meeting_times(message: types.Message, state: FSMContext):
    data = await state.get_data()
    remaining_dates = data.get('remaining_dates', [])
    current_date = remaining_dates[0]
    
    if message.text == "Выбор сделан ✍️":
        remaining_dates.pop(0)  # Удаляем текущую дату
        
        if remaining_dates:  # Если есть ещё даты
            next_date = remaining_dates[0]
            await state.update_data(remaining_dates=remaining_dates)
            await message.answer(
                get_time_select_message(next_date),
                parse_mode="HTML",
                reply_markup=time_kb
            )
            return
        else:  # Если все даты обработаны
            await finish_registration(message, state)
            return
    
    # Обработка выбранного времени
    if "meeting_times" not in data:
        data["meeting_times"] = {}
    if current_date not in data["meeting_times"]:
        data["meeting_times"][current_date] = []
    
    data["meeting_times"][current_date].append(message.text[:2])
    data["meeting_times"][current_date] = list(set(data["meeting_times"][current_date]))
    await state.update_data(meeting_times=data["meeting_times"])


@router.message(StateFilter(ContactForm.speaker))
async def process_speaker(message: types.Message, state: FSMContext):
    config = load_config()
    zones = config['meeting']['zones']
    
    if message.text not in zones:
        await message.answer(get_message("speaker_place"), parse_mode="HTML", reply_markup=zones_kb)
        return
        
    await state.update_data(speaker_place=message.text)
    await finish_registration(message, state)


async def finish_registration(message: types.Message, state: FSMContext):
    data = await state.get_data()
    try:
        try:
            await db.save_contact_to_db(data)
        except Exception as e:
            try:
                await db.update_contact_in_db(data)
            except Exception as e:
                print(e)
        
        # Форматируем данные для вывода
        activity_area = ", ".join(data.get("activity_area", [])) or "не указано"
        interests = ", ".join(data.get("interests", [])) or "не указано"
        description = data.get("description", "отсутствует") if data.get("description") != "/skip" else "отсутствует"
        website = data.get("website", "отсутствует") if data.get("website") != "/skip" else "отсутствует"
        
        # Форматируем времена встреч
        meeting_times_str = []
        for date, times in data.get("meeting_times", {}).items():
            if times:
                sorted_times = sorted(times)
                meeting_times_str.append(f"{date}: {'-'.join([f'{time}:00' for time in sorted_times])}")
        
        meeting_times_formatted = "\n".join(meeting_times_str) if meeting_times_str else "не указано"
        
        # Формируем сообщение
        confirmation_message = (
            "Данные успешно сохранены!\n"
            f"💬 ФИО контактного лица: {data.get('contact_name')}\n"
            f"Должность: {data.get('contact_position')}\n"
            f"Название компании: {data.get('company_name')}\n"
            f"💬 Сфера деятельности: {activity_area}\n"
            f"💬 Интересы: {interests}\n"
            f"Описание: {description}\n"
            f"Сайт компании: {website}\n"
            f"Номер телефона: {data.get('phone')}\n"
            f"Телеграм: {data.get('telegram')} (@{message.from_user.username})\n\n"
            f"Временные возможности:\n{meeting_times_formatted}"
        )
        
        # Добавляем информацию о зоне встреч для спикеров
        if data.get("speaker_place"):
            confirmation_message += f"\n\nЗона встреч с вами: {data.get('speaker_place')}"
        
        await message.answer(confirmation_message, parse_mode="HTML", reply_markup=main_kb)
    except Exception as e:
        print(e)
        await message.answer(get_message("form_error"), parse_mode="HTML")
    await state.set_state(ContactForm.main)


# ----------------------------------------------mettings--------------------------------------------------


dp.include_router(router)
