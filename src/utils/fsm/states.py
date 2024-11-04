from aiogram.fsm.state import State, StatesGroup


class ContactForm(StatesGroup):
    contact_name = State()
    contact_position = State()
    company_name = State()
    activity_area = State()
    interests = State()
    description = State()
    website = State()
    phone = State()
    telegram = State()
    meeting_times_14 = State()
    meeting_times_15 = State()
    main = State()
    meetings = State()
    set_meeting = State()
    time_choose = State()
    end_time_choose = State()
