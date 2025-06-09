import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import sqlite3
import hashlib
from datetime import datetime

# Настройка бота
API_TOKEN = "8091469144:AAFICJucLvkl0x5Zqjda08vMd9yjpUyty6Y"
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# База данных


def init_db():
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        telegram_id INTEGER UNIQUE,
        email TEXT UNIQUE,
        password TEXT,
        full_name TEXT,
        is_admin INTEGER DEFAULT 0
    )"""
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS user_groups (
        user_id INTEGER,
        group_name TEXT,
        UNIQUE(user_id, group_name),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )"""
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS user_events (
        user_id INTEGER,
        event_name TEXT,
        UNIQUE(user_id, event_name),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )"""
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        text TEXT,
        type TEXT,  
        created_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )"""
    )

    # Добавляем тестового админа
    admin_email = "admin@example.com"
    admin_password = hashlib.sha256("admin123".encode()).hexdigest()

    cursor.execute("SELECT * FROM users WHERE email = ?", (admin_email,))
    if not cursor.fetchone():
        cursor.execute(
            """
        INSERT INTO users (telegram_id, email, password, full_name, is_admin)
        VALUES (?, ?, ?, ?, ?)
        """,
            (123456789, admin_email, admin_password, "Администратор", 1),
        )

    conn.commit()
    conn.close()


init_db()


# Состояния для FSM
class Form(StatesGroup):
    email = State()
    password = State()
    login_email = State()
    login_password = State()
    feedback_text = State()
    report_text = State()
    select_group = State()
    select_event = State()
    leave_group = State()
    leave_event = State()


# Клавиатуры
def get_start_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👤 Профиль"),
                KeyboardButton(text="👥 Группы"),
            ],
            [
                KeyboardButton(text="🎭 Мероприятия"),
                KeyboardButton(text="📨 Оставить отзыв"),
                KeyboardButton(text="⚠️ Написать жалобу"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел...",
    )


def get_profile_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="📊 Моя статистика")],
        [KeyboardButton(text="📝 Мои записи")],
    ]
    if is_admin:
        buttons.append([KeyboardButton(text="👑 Админ-панель")])
    buttons.append([KeyboardButton(text="🚪 Выйти")])
    buttons.append([KeyboardButton(text="🔙 Назад")])

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
    )


def get_groups_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 Все группы")],
            [KeyboardButton(text="➕ Записаться в группу")],
            [KeyboardButton(text="➖ Отписаться от группы")],
            [KeyboardButton(text="🔙 Назад")],
        ],
        resize_keyboard=True,
    )


def get_events_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Ближайшие мероприятия")],
            [KeyboardButton(text="🎟 Записаться на мероприятие")],
            [KeyboardButton(text="✖️ Отписаться от мероприятия")],
            [KeyboardButton(text="🔙 Назад")],
        ],
        resize_keyboard=True,
    )


def get_admin_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Пользователи")],
            [KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="📨 Отзывы и жалобы")],
            [KeyboardButton(text="🔙 Назад")],
        ],
        resize_keyboard=True,
    )


def get_groups_keyboard() -> ReplyKeyboardMarkup:
    groups = [
        "Программирование на Python",
        "Фотография для начинающих",
        "Английский intermediate",
    ]
    keyboard = [[KeyboardButton(text=group)] for group in groups]
    keyboard.append([KeyboardButton(text="🔙 Назад")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_events_keyboard() -> ReplyKeyboardMarkup:
    events = [
        "Встреча IT-сообщества",
        "Мастер-класс по фотографии",
        "Языковой клуб: Английский",
    ]
    keyboard = [[KeyboardButton(text=event)] for event in events]
    keyboard.append([KeyboardButton(text="🔙 Назад")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_user_groups_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT group_name FROM user_groups WHERE user_id = ?", (user_id,))
    groups = [row[0] for row in cursor.fetchall()]
    conn.close()

    keyboard = [[KeyboardButton(text=group)] for group in groups]
    keyboard.append([KeyboardButton(text="🔙 Назад")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_user_events_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT event_name FROM user_events WHERE user_id = ?", (user_id,))
    events = [row[0] for row in cursor.fetchall()]
    conn.close()

    keyboard = [[KeyboardButton(text=event)] for event in events]
    keyboard.append([KeyboardButton(text="🔙 Назад")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


# Проверка админских прав
async def is_admin(telegram_id: int) -> bool:
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT is_admin FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()
    conn.close()
    return user and user[0] == 1


# Обработчики команд
@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (message.from_user.id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        welcome_text = (
            f"С возвращением, <b>{message.from_user.full_name}</b>! 👋\n\n"
            "Я бот для управления группами и мероприятиями.\n"
            "Используй меню ниже для навигации."
        )
        await message.answer(welcome_text, reply_markup=get_start_menu())
    else:
        welcome_text = (
            f"Привет, <b>{message.from_user.full_name}</b>! 👋\n\n"
            "Я бот для управления группами и мероприятиями.\n"
            "Для начала работы необходимо зарегистрироваться.\n"
            "Отправьте /register для регистрации или /login для входа."
        )
        await message.answer(welcome_text, reply_markup=ReplyKeyboardRemove())


@dp.message(Command("register"))
async def command_register_handler(message: Message, state: FSMContext):
    await state.set_state(Form.email)
    await message.answer(
        "Введите ваш email для регистрации:", reply_markup=ReplyKeyboardRemove()
    )


@dp.message(Command("login"))
async def command_login_handler(message: Message, state: FSMContext):
    await state.set_state(Form.login_email)
    await message.answer(
        "Введите ваш email для входа:", reply_markup=ReplyKeyboardRemove()
    )


@dp.message(Command("logout"))
async def command_logout_handler(message: Message):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET telegram_id = NULL WHERE telegram_id = ?",
        (message.from_user.id,),
    )
    conn.commit()
    conn.close()
    await message.answer(
        "Вы успешно вышли из аккаунта. Для входа используйте /login",
        reply_markup=ReplyKeyboardRemove(),
    )


@dp.message(F.text == "⚠️ Написать жалобу")
async def write_report_handler(message: Message, state: FSMContext):
    await state.set_state(Form.report_text)
    await message.answer(
        "Опишите вашу проблему или жалобу:", reply_markup=ReplyKeyboardRemove()
    )


@dp.message(Form.report_text)
async def process_report(message: Message, state: FSMContext):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE telegram_id = ?", (message.from_user.id,)
    )
    user_id = cursor.fetchone()[0]

    cursor.execute(
        """
    INSERT INTO feedback (user_id, text, type, created_at)
    VALUES (?, ?, ?, ?)
    """,
        (user_id, message.text, "report", datetime.now().isoformat()),
    )

    conn.commit()
    conn.close()

    await message.answer(
        "Ваша жалоба отправлена администратору. Спасибо за обратную связь!",
        reply_markup=get_start_menu(),
    )
    await state.clear()


@dp.message(F.text == "📨 Оставить отзыв")
async def write_feedback_handler(message: Message, state: FSMContext):
    await state.set_state(Form.feedback_text)
    await message.answer("Напишите ваш отзыв:", reply_markup=ReplyKeyboardRemove())


@dp.message(Form.feedback_text)
async def process_feedback(message: Message, state: FSMContext):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE telegram_id = ?", (message.from_user.id,)
    )
    user_id = cursor.fetchone()[0]

    cursor.execute(
        """
    INSERT INTO feedback (user_id, text, type, created_at)
    VALUES (?, ?, ?, ?)
    """,
        (user_id, message.text, "feedback", datetime.now().isoformat()),
    )

    conn.commit()
    conn.close()

    await message.answer(
        "Спасибо за ваш отзыв! Мы ценим ваше мнение.", reply_markup=get_start_menu()
    )
    await state.clear()


@dp.message(Command("admin"))
async def command_admin_handler(message: Message):
    if await is_admin(message.from_user.id):
        await message.answer("Админ-панель:", reply_markup=get_admin_menu())
    else:
        await message.answer("У вас нет прав доступа к этой команде.")


# Обработчики состояний регистрации
@dp.message(Form.email)
async def process_email(message: Message, state: FSMContext):
    await state.update_data(email=message.text)
    await state.set_state(Form.password)
    await message.answer("Теперь введите пароль:")


@dp.message(Form.password)
async def process_password(message: Message, state: FSMContext):
    data = await state.get_data()
    email = data["email"]
    password = hashlib.sha256(message.text.encode()).hexdigest()

    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
        INSERT INTO users (telegram_id, email, password, full_name)
        VALUES (?, ?, ?, ?)
        """,
            (message.from_user.id, email, password, message.from_user.full_name),
        )
        conn.commit()
        await message.answer(
            "Регистрация успешно завершена!", reply_markup=get_start_menu()
        )
    except sqlite3.IntegrityError:
        await message.answer("Этот email уже зарегистрирован. Попробуйте другой.")

    conn.close()
    await state.clear()


# Обработчики состояний входа
@dp.message(Form.login_email)
async def process_login_email(message: Message, state: FSMContext):
    await state.update_data(login_email=message.text)
    await state.set_state(Form.login_password)
    await message.answer("Введите ваш пароль:")


@dp.message(Form.login_password)
async def process_login_password(message: Message, state: FSMContext):
    data = await state.get_data()
    email = data["login_email"]
    password = hashlib.sha256(message.text.encode()).hexdigest()

    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE email = ? AND password = ?", (email, password)
    )
    user = cursor.fetchone()

    if user:
        cursor.execute(
            "UPDATE users SET telegram_id = ? WHERE email = ?",
            (message.from_user.id, email),
        )
        conn.commit()
        await message.answer("Вход выполнен успешно!", reply_markup=get_start_menu())
    else:
        await message.answer("Неверный email или пароль. Попробуйте снова.")

    conn.close()
    await state.clear()


# Обработчики кнопок
@dp.message(F.text == "🔙 Назад")
async def back_to_main_menu(message: Message):
    if await is_admin(message.from_user.id):
        await message.answer("Главное меню:", reply_markup=get_start_menu())
    else:
        await message.answer("Главное меню:", reply_markup=get_start_menu())


@dp.message(F.text == "🚪 Выйти")
async def logout_handler(message: Message):
    await command_logout_handler(message)


@dp.message(F.text == "👤 Профиль")
async def profile_menu(message: Message):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (message.from_user.id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        await message.answer(
            "Сначала необходимо зарегистрироваться. Отправьте /register"
        )
        return

    is_admin_user = await is_admin(message.from_user.id)
    menu_text = (
        "<b>Меню профиля:</b>\n\n"
        "Здесь вы можете:\n"
        "- Просмотреть свою статистику\n"
        "- Увидеть свои текущие записи\n"
        "- Изменить настройки профиля"
    )
    await message.answer(menu_text, reply_markup=get_profile_menu(is_admin_user))


@dp.message(F.text == "👥 Группы")
async def groups_menu(message: Message):
    menu_text = (
        "<b>Меню групп:</b>\n\n"
        "Доступные действия:\n"
        "- Просмотреть список всех групп\n"
        "- Записаться в интересующую вас группу\n"
        "- Управлять своими текущими группами"
    )
    await message.answer(menu_text, reply_markup=get_groups_menu())


@dp.message(F.text == "🎭 Мероприятия")
async def events_menu(message: Message):
    menu_text = (
        "<b>Меню мероприятий:</b>\n\n"
        "Здесь вы можете:\n"
        "- Узнать о предстоящих мероприятиях\n"
        "- Записаться на интересующие события\n"
        "- Просмотреть свои текущие записи"
    )
    await message.answer(menu_text, reply_markup=get_events_menu())


@dp.message(F.text == "👑 Админ-панель")
async def admin_panel_button(message: Message):
    await command_admin_handler(message)


# Подменю профиля
@dp.message(F.text == "📊 Моя статистика")
async def my_stats(message: Message):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE telegram_id = ?", (message.from_user.id,)
    )
    user = cursor.fetchone()

    if not user:
        await message.answer(
            "Сначала необходимо зарегистрироваться. Отправьте /register"
        )
        return

    user_id = user[0]

    cursor.execute("SELECT COUNT(*) FROM user_groups WHERE user_id = ?", (user_id,))
    groups_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM user_events WHERE user_id = ?", (user_id,))
    events_count = cursor.fetchone()[0]

    conn.close()

    stats_text = (
        "<b>Ваша статистика:</b>\n\n"
        f"📌 <b>Группы:</b> {groups_count}\n"
        f"📌 <b>Мероприятия:</b> {events_count}\n"
        f"📌 <b>Активность:</b> {'высокая' if groups_count + events_count > 3 else 'средняя' if groups_count + events_count > 0 else 'низкая'}\n\n"
        f"{'Вы очень активный пользователь!' if groups_count + events_count > 3 else 'Запишитесь на мероприятия, чтобы повысить активность!' if groups_count + events_count == 0 else ''}"
    )
    await message.answer(stats_text)


@dp.message(F.text == "📝 Мои записи")
async def my_records(message: Message):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE telegram_id = ?", (message.from_user.id,)
    )
    user = cursor.fetchone()

    if not user:
        await message.answer(
            "Сначала необходимо зарегистрироваться. Отправьте /register"
        )
        return

    user_id = user[0]

    cursor.execute("SELECT group_name FROM user_groups WHERE user_id = ?", (user_id,))
    groups = cursor.fetchall()

    cursor.execute("SELECT event_name FROM user_events WHERE user_id = ?", (user_id,))
    events = cursor.fetchall()

    conn.close()

    groups_text = (
        "\n".join([f"- {group[0]}" for group in groups]) if groups else "- Нет записей"
    )
    events_text = (
        "\n".join([f"- {event[0]}" for event in events]) if events else "- Нет записей"
    )

    records_text = (
        "<b>Ваши текущие записи:</b>\n\n"
        f"👥 <b>Группы:</b>\n{groups_text}\n\n"
        f"🎭 <b>Мероприятия:</b>\n{events_text}"
    )
    await message.answer(records_text)


# Подменю групп
@dp.message(F.text == "📚 Все группы")
async def all_groups(message: Message):
    groups_text = (
        "<b>Доступные группы:</b>\n\n"
        "1. <b>Программирование на Python</b>\n"
        "   🕒 Вт/Чт 19:00-21:00\n"
        "   👨‍🏫 Преподаватель: Иван Петров\n\n"
        "2. <b>Фотография для начинающих</b>\n"
        "   🕒 Пн/Ср 18:00-20:00\n"
        "   👨‍🏫 Преподаватель: Анна Сидорова\n\n"
        "3. <b>Английский intermediate</b>\n"
        "   🕒 Пн/Ср/Пт 17:00-19:00\n"
        "   👨‍🏫 Преподаватель: Джон Смит"
    )
    await message.answer(groups_text)


@dp.message(F.text == "➕ Записаться в группу")
async def join_group_menu(message: Message, state: FSMContext):
    await state.set_state(Form.select_group)
    await message.answer(
        "Выберите группу для записи:", reply_markup=get_groups_keyboard()
    )


@dp.message(
    Form.select_group,
    F.text.in_(
        [
            "Программирование на Python",
            "Фотография для начинающих",
            "Английский intermediate",
        ]
    ),
)
async def join_group(message: Message, state: FSMContext):
    group_name = message.text

    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE telegram_id = ?", (message.from_user.id,)
    )
    user = cursor.fetchone()

    if not user:
        await message.answer(
            "Сначала необходимо зарегистрироваться. Отправьте /register"
        )
        return

    user_id = user[0]

    try:
        cursor.execute(
            "INSERT INTO user_groups (user_id, group_name) VALUES (?, ?)",
            (user_id, group_name),
        )
        conn.commit()
        await message.answer(
            f"Вы успешно записаны в группу '{group_name}'!",
            reply_markup=get_groups_menu(),
        )
    except sqlite3.IntegrityError:
        await message.answer(
            f"Вы уже записаны в группу '{group_name}'!", reply_markup=get_groups_menu()
        )

    conn.close()
    await state.clear()


@dp.message(F.text == "➖ Отписаться от группы")
async def leave_group_menu(message: Message, state: FSMContext):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE telegram_id = ?", (message.from_user.id,)
    )
    user = cursor.fetchone()

    if not user:
        await message.answer(
            "Сначала необходимо зарегистрироваться. Отправьте /register"
        )
        return

    user_id = user[0]

    cursor.execute("SELECT group_name FROM user_groups WHERE user_id = ?", (user_id,))
    groups = cursor.fetchall()
    conn.close()

    if not groups:
        await message.answer("Вы не записаны ни в одну группу.")
        return

    await state.set_state(Form.leave_group)
    await message.answer(
        "Выберите группу для отписки:", reply_markup=get_user_groups_keyboard(user_id)
    )


@dp.message(Form.leave_group)
async def leave_group(message: Message, state: FSMContext):
    group_name = message.text

    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE telegram_id = ?", (message.from_user.id,)
    )
    user = cursor.fetchone()

    if not user:
        await message.answer(
            "Сначала необходимо зарегистрироваться. Отправьте /register"
        )
        return

    user_id = user[0]

    cursor.execute(
        "DELETE FROM user_groups WHERE user_id = ? AND group_name = ?",
        (user_id, group_name),
    )
    conn.commit()

    if cursor.rowcount > 0:
        await message.answer(
            f"Вы успешно отписались от группы '{group_name}'!",
            reply_markup=get_groups_menu(),
        )
    else:
        await message.answer(
            f"Вы не были записаны в группу '{group_name}'!",
            reply_markup=get_groups_menu(),
        )

    conn.close()
    await state.clear()


# Подменю мероприятий
@dp.message(F.text == "📅 Ближайшие мероприятия")
async def upcoming_events(message: Message):
    events_text = (
        "<b>Ближайшие мероприятия:</b>\n\n"
        "1. <b>Встреча IT-сообщества</b>\n"
        "   📅 15 июня 2024\n"
        "   🕒 19:00-22:00\n"
        '   📍 Коворкинг "Техноград"\n\n'
        "2. <b>Мастер-класс по фотографии</b>\n"
        "   📅 20 июня 2024\n"
        "   🕒 18:00-21:00\n"
        '   📍 Фотостудия "Объектив"\n\n'
        "3. <b>Языковой клуб: Английский</b>\n"
        "   📅 25 июня 2024\n"
        "   🕒 17:00-19:00\n"
        '   📍 Кафе "Лондон"'
    )
    await message.answer(events_text)


@dp.message(F.text == "🎟 Записаться на мероприятие")
async def join_event_menu(message: Message, state: FSMContext):
    await state.set_state(Form.select_event)
    await message.answer(
        "Выберите мероприятие для записи:", reply_markup=get_events_keyboard()
    )


@dp.message(
    Form.select_event,
    F.text.in_(
        [
            "Встреча IT-сообщества",
            "Мастер-класс по фотографии",
            "Языковой клуб: Английский",
        ]
    ),
)
async def join_event(message: Message, state: FSMContext):
    event_name = message.text

    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE telegram_id = ?", (message.from_user.id,)
    )
    user = cursor.fetchone()

    if not user:
        await message.answer(
            "Сначала необходимо зарегистрироваться. Отправьте /register"
        )
        return

    user_id = user[0]

    try:
        cursor.execute(
            "INSERT INTO user_events (user_id, event_name) VALUES (?, ?)",
            (user_id, event_name),
        )
        conn.commit()
        await message.answer(
            f"Вы успешно записаны на мероприятие '{event_name}'!",
            reply_markup=get_events_menu(),
        )
    except sqlite3.IntegrityError:
        await message.answer(
            f"Вы уже записаны на мероприятие '{event_name}'!",
            reply_markup=get_events_menu(),
        )

    conn.close()
    await state.clear()


@dp.message(F.text == "✖️ Отписаться от мероприятия")
async def leave_event_menu(message: Message, state: FSMContext):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE telegram_id = ?", (message.from_user.id,)
    )
    user = cursor.fetchone()

    if not user:
        await message.answer(
            "Сначала необходимо зарегистрироваться. Отправьте /register"
        )
        return

    user_id = user[0]

    cursor.execute("SELECT event_name FROM user_events WHERE user_id = ?", (user_id,))
    events = cursor.fetchall()
    conn.close()

    if not events:
        await message.answer("Вы не записаны ни на одно мероприятие.")
        return

    await state.set_state(Form.leave_event)
    await message.answer(
        "Выберите мероприятие для отписки:",
        reply_markup=get_user_events_keyboard(user_id),
    )


@dp.message(Form.leave_event)
async def leave_event(message: Message, state: FSMContext):
    event_name = message.text

    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE telegram_id = ?", (message.from_user.id,)
    )
    user = cursor.fetchone()

    if not user:
        await message.answer(
            "Сначала необходимо зарегистрироваться. Отправьте /register"
        )
        return

    user_id = user[0]

    cursor.execute(
        "DELETE FROM user_events WHERE user_id = ? AND event_name = ?",
        (user_id, event_name),
    )
    conn.commit()

    if cursor.rowcount > 0:
        await message.answer(
            f"Вы успешно отписались от мероприятия '{event_name}'!",
            reply_markup=get_events_menu(),
        )
    else:
        await message.answer(
            f"Вы не были записаны на мероприятие '{event_name}'!",
            reply_markup=get_events_menu(),
        )

    conn.close()
    await state.clear()


# Админские функции
@dp.message(F.text == "👥 Пользователи")
async def admin_users(message: Message):
    if not await is_admin(message.from_user.id):
        await message.answer("У вас нет прав доступа к этой команде.")
        return

    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute("SELECT full_name, email, is_admin FROM users")
    users = cursor.fetchall()
    conn.close()

    users_text = "<b>Список пользователей:</b>\n\n" + "\n".join(
        [
            f"{i + 1}. {user[0]} ({user[1]}) {'👑' if user[2] else ''}"
            for i, user in enumerate(users)
        ]
    )

    await message.answer(users_text)


@dp.message(F.text == "📊 Статистика")
async def admin_stats(message: Message):
    if not await is_admin(message.from_user.id):
        await message.answer("У вас нет прав доступа к этой команде.")
        return

    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM user_groups")
    total_groups = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM user_events")
    total_events = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
    total_admins = cursor.fetchone()[0]

    conn.close()

    stats_text = (
        "<b>Общая статистика:</b>\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"👑 Администраторов: {total_admins}\n"
        f"📚 Всего записей в группы: {total_groups}\n"
        f"🎭 Всего записей на мероприятия: {total_events}"
    )

    await message.answer(stats_text)


@dp.message(F.text == "📨 Отзывы и жалобы")
async def admin_feedback(message: Message):
    if not await is_admin(message.from_user.id):
        await message.answer("У вас нет прав доступа к этой команде.")
        return

    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        """
    SELECT f.id, u.full_name, f.text, f.type, f.created_at 
    FROM feedback f
    JOIN users u ON f.user_id = u.id
    ORDER BY f.created_at DESC
    """
    )
    feedbacks = cursor.fetchall()
    conn.close()

    if not feedbacks:
        await message.answer("Нет отзывов и жалоб.")
        return

    feedback_text = "<b>Отзывы и жалобы:</b>\n\n"
    for fb in feedbacks:
        feedback_text += (
            f"📌 <b>{'⚠️ Жалоба' if fb[3] == 'report' else '📨 Отзыв'} от {fb[1]}</b>\n"
            f"🕒 {fb[4]}\n"
            f"{fb[2]}\n\n"
        )

    await message.answer(feedback_text)


# Запуск бота
async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
