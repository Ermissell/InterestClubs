import asyncio
import logging
import aiohttp

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode

import keyboards as kb
import os
import random


API_TOKEN = "token_name"
bot = Bot(token=API_TOKEN)

dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(
        f"Привет, {message.from_user.full_name}! С этим ботом ты можешь записаться в клубы и на мероприятия. Для получения справочной информации введи команду /help"
    )
    await message.answer("Выберите действие в меню:", reply_markup=kb.startMenu)


@dp.message(Command("help"))
async def command_help_handler(message: Message) -> None:
    await message.answer(f"Справочная информация о боте, хехе")


@dp.message(F.text == "⬅️ Назад")
async def backToMainMenu(message: Message):
    await message.answer("Выберите действие в меню:", reply_markup=kb.startMenu)


@dp.message(F.text == "Профиль пользователя")
async def submenu(message: Message):
    await message.answer("тут информация о пользователе", reply_markup=kb.subMenu)


@dp.message(F.text == "Меню группы")
async def submenu(message: Message):
    await message.answer("тут информация о группах", reply_markup=kb.subMenu2)


@dp.message(F.text == "Меню мероприятия")
async def submenu(message: Message):
    await message.answer("тут информация о мероприятиях", reply_markup=kb.subMenu3)


@dp.message()
async def echo_handler(message: Message) -> None:
    await message.send_copy(chat_id=message.chat.id)


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
