import asyncio
import json

import aiosqlite
import os

from utils.config import load_config
from utils.bot import bot
from view.text import get_message

DB_NAME = os.path.join(os.path.dirname(__file__), "DataBase.db")


async def create_tables():
    async with aiosqlite.connect(DB_NAME) as conn:
        cursor = await conn.cursor()
        await cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_name TEXT NOT NULL,
                contact_position TEXT NOT NULL,
                company_name TEXT,
                activity_area TEXT NOT NULL,
                interests TEXT NOT NULL,
                description TEXT,
                website TEXT,
                phone TEXT NOT NULL,
                telegram TEXT NOT NULL UNIQUE,
                meeting_times TEXT NOT NULL,
                speaker_place TEXT
            )
        ''')

        await cursor.execute('''
            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                contact1_id INTEGER NOT NULL,
                contact2_id INTEGER NOT NULL,
                table_num INTEGER,
                place TEXT,
                result TEXT,
                comments TEXT,
                status INTEGER NOT NULL,
                last_datetime TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
                FOREIGN KEY (contact1_id) REFERENCES contacts (id),
                FOREIGN KEY (contact2_id) REFERENCES contacts (id)
            )
        ''')

        await cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS update_last_datetime
            AFTER UPDATE ON meetings
            FOR EACH ROW
            BEGIN
                UPDATE meetings SET last_datetime = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END;
        ''')
        await conn.commit()
    print("Таблицы contacts и meetings созданы (если еще не существовали)")


# ----------------------------------------------contacts--------------------------------------------------


async def save_contact_to_db(data):
    query = '''
        INSERT INTO contacts (
            contact_name, contact_position, company_name, 
            activity_area, interests, description, 
            website, phone, telegram, meeting_times,
            speaker_place
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(query, (
            data['contact_name'],
            data['contact_position'],
            data['company_name'],
            json.dumps(data.get('activity_area', [])),
            json.dumps(data.get('interests', [])),
            data.get('description', ''),
            data.get('website', ''),
            data['phone'],
            str(data['telegram']),
            json.dumps(data.get('meeting_times', {})),
            data.get('speaker_place', None)
        ))
        await db.commit()


async def update_contact_in_db(data):
    query = '''
        UPDATE contacts 
        SET 
            contact_name = COALESCE(?, contact_name),
            contact_position = COALESCE(?, contact_position),
            company_name = COALESCE(?, company_name),
            activity_area = COALESCE(?, activity_area),
            interests = COALESCE(?, interests),
            description = COALESCE(?, description),
            website = COALESCE(?, website),
            phone = COALESCE(?, phone),
            meeting_times = COALESCE(?, meeting_times),
            speaker_place = COALESCE(?, speaker_place)
        WHERE telegram = ?
    '''

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(query, (
            data.get('contact_name'),
            data.get('contact_position'),
            data.get('company_name'),
            json.dumps(data.get('activity_area', [])) if 'activity_area' in data else None,
            json.dumps(data.get('interests', [])) if 'interests' in data else None,
            data.get('description'),
            data.get('website'),
            data.get('phone'),
            json.dumps(data.get('meeting_times', {})) if 'meeting_times' in data else None,
            data.get('speaker_place'),
            data['telegram']
        ))
        await db.commit()
    print(f"Информация о контакте с telegram={data['telegram']} обновлена.")


async def get_contact_by_telegram(telegram: str) -> dict:
    """Получает полную строку контакта по значению поля telegram."""
    async with aiosqlite.connect(DB_NAME) as conn:
        cursor = await conn.execute("SELECT * FROM contacts WHERE telegram = ?", (telegram,))
        result = await cursor.fetchone()
        if result:
            columns = [column[0] for column in cursor.description]
            return dict(zip(columns, result))
        return None


async def delete_contact_by_telegram(telegram: str) -> bool:
    """Удаляет контакт по значению поля telegram и возвращает True, если удаление успешно."""
    async with aiosqlite.connect(DB_NAME) as conn:
        cursor = await conn.execute("DELETE FROM contacts WHERE telegram = ?", (telegram,))
        await conn.commit()
        # Проверка, было ли удалено хотя бы одно совпадение
        if cursor.rowcount > 0:
            print("Контакт успешно удалён.")
            return True
        else:
            print("Контакт с указанным Telegram не найден.")
            return False


async def get_contacts_by_meeting_time(day: int) -> list[dict]:
    """Получает строки контактов по значению поля meeting_times_14 или meeting_times_15."""
    column = "meeting_times_14" if day == 14 else "meeting_times_15"
    async with aiosqlite.connect(DB_NAME) as conn:
        cursor = await conn.execute(f"SELECT * FROM contacts WHERE {column} IS NOT NULL")
        results = await cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in results]


async def get_contacts_by_meeting_times_and_activity_area(meeting_times: dict, activity_areas: list[str], telegram: str) -> list[dict]:
    """
    Получает контакты с совпадающими временами встреч и сферами деятельности.
    
    Args:
        meeting_times (dict): Словарь с датами и временем {date: [times]}
        activity_areas (list[str]): Список сфер деятельности
        telegram (str): Telegram ID текущего пользователя (для исключения из результатов)
        
    Returns:
        list[dict]: Список контактов с совпадающими временами и сферами деятельности
    """
    async with aiosqlite.connect(DB_NAME) as conn:
        # Получаем всех пользователей, кроме текущего
        cursor = await conn.execute("SELECT * FROM contacts WHERE telegram != ?", (str(telegram),))
        rows = await cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        
        matching_contacts = []
        for row in rows:
            contact = dict(zip(columns, row))
            try:
                # Преобразуем JSON-строки в Python-объекты
                contact_times = json.loads(contact['meeting_times'], strict=False)
                contact_areas = json.loads(contact['activity_area'], strict=False)

                print(contact_areas, contact_times, meeting_times, activity_areas)
                
                # Проверяем совпадение хотя бы одной сферы д��ятельности
                has_matching_area = any(area in contact_areas for area in activity_areas)
                if not has_matching_area:
                    continue
                
                # Проверяем совпадение хотя бы одного времени
                has_matching_time = False
                for date, times in meeting_times.items():
                    contact_date_times = contact_times.get(date, [])
                    if any(time in contact_date_times for time in times):
                        has_matching_time = True
                        break
                
                if has_matching_time:
                    # Преобразуем JSON-строки для остальных полей
                    contact['interests'] = json.loads(contact['interests'])
                    matching_contacts.append(contact)
                    
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Error processing contact {contact.get('telegram')}: {e}")
                continue
                
        return matching_contacts


async def migrate_contacts_table():
    """Переносит данные из старой таблицы contacts в новую и удаляет старую таблицу."""
    async with aiosqlite.connect(DB_NAME) as conn:
        cursor = await conn.cursor()

        # Создание временной новой таблицы с той же структурой
        await cursor.execute('''
            CREATE TABLE IF NOT EXISTS new_contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_name TEXT NOT NULL,
                contact_position TEXT NOT NULL,
                company_name TEXT,
                activity_area TEXT NOT NULL,
                interests TEXT NOT NULL,
                description TEXT,
                website TEXT,
                phone TEXT NOT NULL,
                telegram TEXT NOT NULL UNIQUE,
                meeting_times JSON NOT NULL,
                speaker_place TEXT
            )
        ''')

        # Копирование данных из старой таблицы в новую
        await cursor.execute('''
            INSERT INTO new_contacts (id, contact_name, contact_position, company_name, activity_area, interests, description, website, phone, telegram, meeting_times, speaker_place)
            SELECT id, contact_name, contact_position, company_name, activity_area, interests, description, website, phone, telegram, meeting_times, speaker_place
            FROM contacts
        ''')

        # Удаление старой таблицы
        await cursor.execute('DROP TABLE contacts')

        # Переименование новой таблицы в старую
        await cursor.execute('ALTER TABLE new_contacts RENAME TO contacts')

        # Сохранение изменений
        await conn.commit()

        print("Данные успешно перенесены, старая таблица удалена.")


# ----------------------------------------------meetings--------------------------------------------------


async def save_meeting_to_db(data):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute('''
            INSERT INTO meetings (date, time, contact1_id, contact2_id, place, result, comments, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['date'], data['time'], data['contact1_id'], data['contact2_id'], data['place'],
            data.get('result', ''), data.get('comments', ''), data['status']
        ))
        await db.commit()
        meeting_id = cursor.lastrowid
    return meeting_id


async def update_meeting_in_db(meeting_id: int, data):
    query = '''
        UPDATE meetings 
        SET place = COALESCE(?, place),
            result = COALESCE(?, result),
            comments = COALESCE(?, comments),
            status = COALESCE(?, status)
        WHERE status = -1 and date = ? and time = ? and contact1_id = ? and contact2_id = ?
    '''

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(query, (
            data.get('place'),
            data.get('result'),
            data.get('comments'),
            data.get('status'),
            data.get('date'),
            data.get('time'),
            data['contact1_id'],
            data['contact2_id'],
        ))
        await db.commit()
        meeting_id = cursor.lastrowid
    return meeting_id


async def update_meeting(meeting_id: int, **kwargs):
    if not kwargs:
        print("Нет параметров для обновления.")
        return

    columns = ", ".join([f"{key} = ?" for key in kwargs.keys()])
    values = list(kwargs.values())

    values.append(meeting_id)

    sql_query = f"UPDATE meetings SET {columns} WHERE id = ?"

    async with aiosqlite.connect(DB_NAME) as db:
        try:
            await db.execute(sql_query, values)
            await db.commit()
        except aiosqlite.Error as e:
            print("Ошибка при обновлении встречи:", e)


async def get_meeting_by_datetime_and_table(date: str, time: str, table_num: int):
    query = """
    SELECT * FROM meetings
    WHERE date = ? AND time = ? AND table_num = ?
    """

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, (date, time, table_num)) as cursor:
            row = await cursor.fetchone()

    return dict(row) if row else None


async def get_meetings_by_contact_id(contact_id: int) -> list[dict]:
    """Получает строки встреч по значениям полей contact1_id или contact2_id."""
    async with aiosqlite.connect(DB_NAME) as conn:
        cursor = await conn.execute(f"SELECT * FROM meetings WHERE contact1_id = ? or contact2_id = ?",
                                    (contact_id, contact_id))
        results = await cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in results]


async def get_meeting_by_id(meeting_id: int) -> dict:
    """Получает встречу по её ID и возвращает в виде словаря."""
    async with aiosqlite.connect(DB_NAME) as conn:
        cursor = await conn.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,))
        result = await cursor.fetchone()
        if result:
            columns = [column[0] for column in cursor.description]
            return dict(zip(columns, result))
        return None  # Если встреча с таким ID не найдена


async def update_meeting_status(meeting_id: int, new_status: int) -> bool:
    """Изменяет статус встречи по ID и возвращает True, если статус был обновлён."""
    query = '''
        UPDATE meetings 
        SET status = ? 
        WHERE id = ?
    '''
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(query, (new_status, meeting_id))
        await db.commit()
        return cursor.rowcount > 0


async def delete_meeting_by_id(meeting_id: int) -> bool:
    """Удаляет встречу по ID и возвращает True, если встреча была удален."""
    query = '''
        DELETE FROM meetings 
        WHERE id = ?
    '''
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(query, (meeting_id,))
        await db.commit()
        return cursor.rowcount > 0


async def get_meeting_by_date_time(date: str, time: str) -> dict:
    """Получает полную строку встречи по дате и времени."""
    async with aiosqlite.connect(DB_NAME) as conn:
        cursor = await conn.execute("SELECT * FROM meetings WHERE date = ? AND time = ?", (date, time))
        result = await cursor.fetchone()
        if result:
            columns = [column[0] for column in cursor.description]
            return dict(zip(columns, result))
        return None


async def get_meeting_by_details(date: str, time: str, contact1_id: int, contact2_id: int) -> dict:
    """Получает полную строку встречи по дате, времени, contact1_id и contact2_id."""
    async with aiosqlite.connect(DB_NAME) as conn:
        cursor = await conn.execute(
            "SELECT * FROM meetings WHERE date = ? AND time = ? AND contact1_id = ? AND contact2_id = ?",
            (date, time, contact1_id, contact2_id)
        )
        result = await cursor.fetchone()
        if result:
            columns = [column[0] for column in cursor.description]
            return dict(zip(columns, result))
        return None


async def get_meetings_with_status(status) -> list[dict]:
    """Возвращает список словарей встреч, где status = 0."""
    async with aiosqlite.connect(DB_NAME) as conn:
        cursor = await conn.execute("SELECT * FROM meetings WHERE status = ?", (status,))
        results = await cursor.fetchall()
        columns = [column[0] for column in cursor.description]

        meetings = [dict(zip(columns, row)) for row in results]
        return meetings


async def delete_old_meetings(threshold_minutes=None):
    config = load_config()
    if threshold_minutes is None:
        threshold_minutes = config['settings']['threshold_minutes']
        
    async with aiosqlite.connect(DB_NAME) as conn:
        cursor = await conn.cursor()

        await cursor.execute(f'''
            SELECT * FROM meetings
            WHERE julianday('now') - julianday(last_datetime) > {threshold_minutes / 1440.0}
            AND status = -1
        ''')

        rows = await cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        deleted_meetings = [dict(zip(columns, row)) for row in rows]

        await cursor.execute(f'''
            DELETE FROM meetings
            WHERE julianday('now') - julianday(last_datetime) > {threshold_minutes / 1440.0}
            AND status = -1
        ''')

        await conn.commit()
        return deleted_meetings


async def migrate_meetings_table():
    """Переносит данные из старой таблицы meetings в новую и удаляет старую таблицу."""
    async with aiosqlite.connect(DB_NAME) as conn:
        cursor = await conn.cursor()

        # Создание временной новой таблицы с той же структурой
        await cursor.execute('''
            CREATE TABLE IF NOT EXISTS new_meetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                contact1_id INTEGER NOT NULL,
                contact2_id INTEGER NOT NULL,
                table_num INTEGER,
                place TEXT,
                result TEXT,
                comments TEXT,
                status INTEGER NOT NULL,
                last_datetime TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
                FOREIGN KEY (contact1_id) REFERENCES contacts (id),
                FOREIGN KEY (contact2_id) REFERENCES contacts (id)
            )
        ''')

        # Копирование данных из старой таблицы в новую
        await cursor.execute('''
            INSERT INTO new_meetings (id, date, time, contact1_id, contact2_id, table_num, place, result, comments, status)
            SELECT id, date, time, contact1_id, contact2_id, table_num, place, result, comments, status
            FROM meetings
        ''')

        # Удаление старой таблицы
        await cursor.execute('DROP TABLE meetings')

        # Переименование новой таблицы в старую
        await cursor.execute('ALTER TABLE new_meetings RENAME TO meetings')

        # Сохранение изменений
        await conn.commit()

        print("Данные успешно перенесены, старая таблица удалена.")


# ----------------------------------------------admin--------------------------------------------------


async def a_add_contact(**kwargs):
    """
    Добавляет новый контакт в таблицу contacts.

    Параметры:
    - contact_name (str): Обязательный параметр.
    - contact_position (str): Обязательный параметр.
    - company_name (str):
    - activity_area (str): Обязательный параметр.
    - interests (str): Обязательный параметр.
    - description (str):
    - website (str):
    - phone (str): Обязательный параметр.
    - telegram (str): Обязательный параметр, должен быть уникальным.
    - meeting_times_14 (str): Обязательный параметр.
    - meeting_times_15 (str): Обязате��ьный параметр.
    - paid (str):
    - speaker_place (str):

    Возвращает:
    - id добавленного контакта (целое число).
    """
    query = '''
        INSERT INTO contacts (contact_name, contact_position, company_name, activity_area,
                              interests, description, website, phone, telegram,
                              meeting_times_14, meeting_times_15, paid, speaker_place)
        VALUES (:contact_name, :contact_position, :company_name, :activity_area, :interests,
                :description, :website, :phone, :telegram, :meeting_times_14,
                :meeting_times_15, :paid, :speaker_place)
    '''
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(query, kwargs) as cursor:
            await db.commit()
            return cursor.lastrowid


async def a_update_contact(contact_id, **kwargs):
    """
    Обновляет информацию о существующем контакте по его id.

    Параметры:
    - contact_id (int): Идентификатор контакта, который нужно обновить. Обязательный параметр.
    - Остальные параметры:
        - contact_name (str): Имя контакта.
        - contact_position (str): Должность контакта.
        - company_name (str): Название компании.
        - activity_area (str): Сфера деятельности.
        - interests (str): Интересы контакта.
        - description (str): Описание контакта.
        - website (str): Вебсайт компании или контакта.
        - phone (str): Номер телефона.
        - telegram (str): Telegram-аккаунт.
        - meeting_times_14 (str): Время для встреч 14.
        - meeting_times_15 (str): Время для встреч 15.
        - paid (str): Статус оплаты.
        - speaker_place (str): Место выступления спикера.

    Возвращает:
    - Количество обновленных строк (обычно 1, если обновление прошло успешно).
    """
    query = f'''
        UPDATE contacts
        SET {', '.join([f"{key} = :{key}" for key in kwargs])}
        WHERE id = :contact_id
    '''
    async with aiosqlite.connect(DB_NAME) as db:
        kwargs['contact_id'] = contact_id
        async with db.execute(query, kwargs) as cursor:
            await db.commit()
            return cursor.rowcount


async def a_add_meeting(**kwargs):
    """
    Добавляет новую встречу в таблицу meetings.

    Параметры:
    - date (str): Обязательный параметр.
    - time (str): Обязательный параметр.
    - contact1_id (int): Обязательный параметр.
    - contact2_id (int): Обязательный параметр.
    - table_num (int):
    - place (str):
    - result (str):
    - comments (str):
    - status (int): Обязательный параметр.
    - last_datetime (str): по умолчанию CURRENT_TIMESTAMP

    Возвращает:
    - id добавленной встречи (целое число).
    """
    query = '''
        INSERT INTO meetings (date, time, contact1_id, contact2_id, table_num,
                              place, result, comments, status, last_datetime)
        VALUES (:date, :time, :contact1_id, :contact2_id, :table_num,
                :place, :result, :comments, :status, :last_datetime)
    '''
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(query, kwargs) as cursor:
            await db.commit()
            return cursor.lastrowid


async def a_update_meeting(meeting_id, **kwargs):
    """
    Обновляет информацию о существующей встрече по ее id.

    Параметры:
    - meeting_id (int): Идентификатор встречи, которую нужно обновить. Обязательный параметр.
    - Остальные параметры:
        - date (str): Дата встречи.
        - time (str): Время встречи.
        - contact1_id (int): ID первого участника.
        - contact2_id (int): ID второго участника.
        - table_num (int): Номер стола.
        - place (str): Место встречи.
        - result (str): Результат встречи.
        - comments (str): Комментарии по встрече.
        - status (int): Статус встречи.
        - last_datetime (str): Последняя дата и время обновления записи.

    Возвращает:
    - Количество обновленных строк (обычно 1, если обновление прошло успешно).
    """
    query = f'''
        UPDATE meetings
        SET {', '.join([f"{key} = :{key}" for key in kwargs])}
        WHERE id = :meeting_id
    '''
    async with aiosqlite.connect(DB_NAME) as db:
        kwargs['meeting_id'] = meeting_id
        async with db.execute(query, kwargs) as cursor:
            await db.commit()
            return cursor.rowcount


async def drop_table():
    async with aiosqlite.connect(DB_NAME) as conn:
        cursor = await conn.execute("DROP TABLE IF EXISTS meetings")


async def cleanup_outdated_contacts():
    """
    Удаляет контакты с устаревшими датами встреч и уведомляет пользователей.
    Сравнивает даты в БД с датами из конфига.
    """
    from utils.config import load_config
    from utils.bot import bot
    from view.text import get_message
    
    config = load_config()
    valid_dates = config['meeting']['dates']  # Получаем актуальные даты из конфига
    
    async with aiosqlite.connect(DB_NAME) as conn:
        # Получаем все контакты
        cursor = await conn.execute("SELECT id, telegram, meeting_times, contact_name FROM contacts")
        rows = await cursor.fetchall()
        
        for row in rows:
            contact_id, telegram, meeting_times, contact_name = row
            try:
                # Парсим JSON с датами встреч
                times = json.loads(meeting_times)
                contact_dates = set(times.keys())
                
                # Если есть даты, которых нет в конфиге - удаляем контакт
                if not all(date in valid_dates for date in contact_dates):
                    # Отправляем уведомление пользователю
                    try:
                        message = (
                            f"Уважаемый(ая) {contact_name}!\n\n"
                            "Даты проведения форума были изменены. "
                            "Пожалуйста, пройдите регистрацию повторно, чтобы выбрать актуальные даты для встреч /start\n\n"
                            f"Актуальные даты форума: {', '.join(valid_dates)}"
                        )
                        await bot.send_message(
                            chat_id=telegram,
                            text=message,
                            parse_mode="HTML"
                        )
                        print(f"Уведомление отправлено контакту {telegram}")
                    except Exception as e:
                        print(f"Ошибка при отправке уведомления контакту {telegram}: {e}")
                    
                    # Удаляем контакт из базы
                    await conn.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
                    print(f"Удален контакт {telegram} с устаревшими датами: {contact_dates}")
            
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Ошибка при обработке контакта {telegram}: {e}")
                try:
                    # Отправляем уведомление об ошибке и необходимости перерегистрации
                    message = (
                        f"Уважаемый(ая) {contact_name}!\n\n"
                        "В вашей регистрационной записи обнаружена ошибка. "
                        "Пожалуйста, пройдите регистрацию повторно.\n\n"
                        f"Даты форума: {', '.join(valid_dates)}"
                    )
                    await bot.send_message(
                        chat_id=telegram,
                        text=message,
                        parse_mode="HTML"
                    )
                except Exception as send_error:
                    print(f"Ошибка при отправке уведомления контакту {telegram}: {send_error}")
                
                # Удаляем контакт с ошибочными данными
                await conn.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
                
        await conn.commit()
