"""Инлайн-клавиатуры диспетчера."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Топ", callback_data="top")],
            [InlineKeyboardButton(text="Статистика", callback_data="stats")],
            [InlineKeyboardButton(text="Загрузить layout", callback_data="upload")],
            [InlineKeyboardButton(text="Подписка /watch", callback_data="watch")],
        ]
    )


def back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="В меню", callback_data="menu")]]
    )
