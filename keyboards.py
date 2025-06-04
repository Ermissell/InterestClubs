from aiogram.types import (
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
)

startMenu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Профиль пользователя"),
            KeyboardButton(text="Меню группы"),
            KeyboardButton(text="Меню мероприятия"),
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
    input_field_placeholder="Начальное меню",
)

subMenu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Информация о пользователе"),
        ],
        [KeyboardButton(text="⬅️ Назад")],
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
    input_field_placeholder="Меню поменбше",
)

subMenu2 = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Информация о группах"),
        ],
        [KeyboardButton(text="⬅️ Назад")],
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
    input_field_placeholder="Меню поменбше",
)

subMenu3 = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Информация о мероприятиях"),
        ],
        [KeyboardButton(text="⬅️ Назад")],
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
    input_field_placeholder="Меню поменбше",
)
