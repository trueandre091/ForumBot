import asyncio

import aiosqlite
import os

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
                meeting_times_14 TEXT NOT NULL,
                meeting_times_15 TEXT NOT NULL
            )
        ''')

        await cursor.execute('''
            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                contact1_id INTEGER NOT NULL,
                contact2_id INTEGER NOT NULL,
                table_num INTEGER NOT NULL,
                result TEXT,
                comments TEXT,
                status INTEGER NOT NULL,
                FOREIGN KEY (contact1_id) REFERENCES contacts (id),
                FOREIGN KEY (contact2_id) REFERENCES contacts (id),
                UNIQUE (date, time, table_num)
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
    meeting_times_14 = ",".join(data['meeting_times_14']) if None not in data['meeting_times_14'] else "отсутствуют"
    meeting_times_15 = ",".join(data['meeting_times_15']) if None not in data['meeting_times_15'] else "отсутствуют"
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT INTO contacts (contact_name, contact_position, company_name, activity_area, interests, description, 
                                  website, phone, telegram, meeting_times_14, meeting_times_15)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['contact_name'], data['contact_position'], data['company_name'], ",".join(data['activity_area']),
            ",".join(data['interests']), data['description'], data['website'], data['phone'], data['telegram'],
            meeting_times_14, meeting_times_15
        ))
        await db.commit()


async def update_contact_in_db(data):
    meeting_times_14 = ",".join(data['meeting_times_14']) if None not in data['meeting_times_14'] else "отсутствуют"
    meeting_times_15 = ",".join(data['meeting_times_15']) if None not in data['meeting_times_15'] else "отсутствуют"

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
            meeting_times_14 = COALESCE(?, meeting_times_14),
            meeting_times_15 = COALESCE(?, meeting_times_15)
        WHERE telegram = ?
    '''

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(query, (
            data.get('contact_name'),
            data.get('contact_position'),
            data.get('company_name'),
            ",".join(data.get('activity_area', [])) if 'activity_area' in data else None,
            ",".join(data.get('interests', [])) if 'interests' in data else None,
            data.get('description'),
            data.get('website'),
            data.get('phone'),
            meeting_times_14,
            meeting_times_15,
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


async def get_contacts_by_meeting_times_and_activity_area(meeting_times_14: list[str], meeting_times_15: list[str],
                                                          activity_areas: list[str], telegram: str) -> list[dict]:
    """Получает строки контактов, соответствующие условиям meeting_times_14, meeting_times_15 и activity_area."""

    async with aiosqlite.connect(DB_NAME) as conn:
        meeting_time_conditions = []
        values = []

        if meeting_times_14:
            meeting_time_conditions.append(' OR '.join([f"meeting_times_14 LIKE ?" for _ in meeting_times_14]))
            for value in meeting_times_14:
                values.append(f"%{value}%")

        if meeting_times_15:
            meeting_time_conditions.append(' OR '.join([f"meeting_times_15 LIKE ?" for _ in meeting_times_15]))
            for value in meeting_times_15:
                values.append(f"%{value}%")

        activity_area_conditions = ' OR '.join([f"activity_area LIKE ?" for _ in activity_areas])
        values.extend([f"%{area}%" for area in activity_areas])

        query = f'''
                    SELECT * FROM contacts 
                    WHERE ({' OR '.join(meeting_time_conditions)}) 
                    AND ({activity_area_conditions}) 
                    AND telegram != ?
                '''

        values.append(str(telegram))

        cursor = await conn.execute(query, values)
        rows = await cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        await cursor.close()

        return [dict(zip(columns, row)) for row in rows]


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
                meeting_times_14 TEXT NOT NULL,
                meeting_times_15 TEXT NOT NULL,
                paid TEXT
            )
        ''')

        # Копирование данных из старой таблицы в новую
        await cursor.execute('''
            INSERT INTO new_contacts (id, contact_name, contact_position, company_name, activity_area, interests, description, website, phone, telegram, meeting_times_14, meeting_times_15)
            SELECT id, contact_name, contact_position, company_name, activity_area, interests, description, website, phone, telegram, meeting_times_14, meeting_times_15
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
            INSERT INTO meetings (date, time, contact1_id, contact2_id, table_num, result, comments, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['date'], data['time'], data['contact1_id'], data['contact2_id'], data['table_num'],
            data.get('result', ''), data.get('comments', ''), data['status']
        ))
        await db.commit()
        meeting_id = cursor.lastrowid
    return meeting_id


async def update_meeting_in_db(meeting_id: int, data):
    query = '''
        UPDATE meetings 
        SET table_num = COALESCE(?, table_num),
            result = COALESCE(?, result),
            comments = COALESCE(?, comments),
            status = COALESCE(?, status)
        WHERE status = -1 and date = ? and time = ? and contact1_id = ? and contact2_id = ?
    '''

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(query, (
            data.get('table_num'),
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
    """Удаляет встречу по ID и возвращает True, если встреча была удалена."""
    query = '''
        DELETE FROM meetings 
        WHERE id = ?
    '''
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(query, (meeting_id,))
        await db.commit()
        return cursor.rowcount > 0


async def get_meeting_by_table_num(table_num: int) -> dict:
    """Получает полную строку встречи по номеру стола."""
    async with aiosqlite.connect(DB_NAME) as conn:
        cursor = await conn.execute("SELECT * FROM meetings WHERE table_num = ?", (table_num,))
        result = await cursor.fetchone()
        if result:
            columns = [column[0] for column in cursor.description]
            return dict(zip(columns, result))
        return None


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


async def delete_meeting_by_details(date: str, time: str, contact1_id: int, contact2_id: int, table_num: int) -> bool:
    """Удаляет строку встречи по дате, времени, contact1_id и contact2_id и table_num"""
    async with aiosqlite.connect(DB_NAME) as conn:
        cursor = await conn.execute(
            "DELETE FROM meetings WHERE date = ? AND time = ? AND contact1_id = ? AND contact2_id = ? AND table_num = ?",
            (date, time, contact1_id, contact2_id, table_num)
        )
        await conn.commit()
        # Проверка количества удаленных строк: если больше нуля, значит удаление прошло успешно
        return cursor.rowcount > 0


async def get_meetings_with_status(status) -> list[dict]:
    """Возвращает список словарей встреч, где status = 0."""
    async with aiosqlite.connect(DB_NAME) as conn:
        cursor = await conn.execute("SELECT * FROM meetings WHERE status = ?", (status,))
        results = await cursor.fetchall()
        columns = [column[0] for column in cursor.description]

        meetings = [dict(zip(columns, row)) for row in results]
        return meetings


async def delete_old_meetings(threshold_minutes=15):
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
                table_num INTEGER NOT NULL,
                result TEXT,
                comments TEXT,
                status INTEGER NOT NULL,
                last_datetime TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
                FOREIGN KEY (contact1_id) REFERENCES contacts (id),
                FOREIGN KEY (contact2_id) REFERENCES contacts (id),
                UNIQUE (date, time, table_num)
            )
        ''')

        # Копирование данных из старой таблицы в новую
        await cursor.execute('''
            INSERT INTO new_meetings (id, date, time, contact1_id, contact2_id, table_num, result, comments, status)
            SELECT id, date, time, contact1_id, contact2_id, table_num, result, comments, status
            FROM meetings
        ''')

        # Удаление старой таблицы
        await cursor.execute('DROP TABLE meetings')

        # Переименование новой таблицы в старую
        await cursor.execute('ALTER TABLE new_meetings RENAME TO meetings')

        # Сохранение изменений
        await conn.commit()

        print("Данные успешно перенесены, старая таблица удалена.")


async def drop_table():
    async with aiosqlite.connect(DB_NAME) as conn:
        cursor = await conn.execute("DROP TABLE IF EXISTS meetings")
