from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup,InlineKeyboardButton
from datetime import datetime, timedelta

from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List
from config import TIMEZONE

main = ReplyKeyboardMarkup(keyboard= [
    [KeyboardButton(text="Посмотреть расписание")],
    [KeyboardButton(text="Мои брони")],
    [KeyboardButton(text="Информация")],
    ], resize_keyboard=True)

def dates_kb(user_dates=None):
    builder = InlineKeyboardBuilder()
    dates = [datetime.now(TIMEZONE) + timedelta(days=i) for i in range(7)]
    for dt in dates:
        if user_dates is None or dt.strftime('%Y-%m-%d') in user_dates:
            builder.button(
                text=dt.strftime("%d.%m"),
                callback_data=f"date_{dt.strftime('%Y-%m-%d')}"
            )
    builder.adjust(4)
    return builder.as_markup()

def slots_kb(date: str, booked_slots: List, user_slot: int):
    builder = InlineKeyboardBuilder()
    print(date, booked_slots, user_slot)
    for slot_num in range(1, 21):
        if slot_num in booked_slots and slot_num == user_slot:
            builder.button(text="👀", callback_data=f"my_slot_{date}_{slot_num}")
        elif slot_num in booked_slots:
            builder.button(
                text=f"❌",
                callback_data=f"close_slot"
            )
        else:
            builder.button(text="✅", callback_data=f"slot_{date}_{slot_num}")
    builder.adjust(5)
    return builder.as_markup()

def cancel_slot():
    button1 = InlineKeyboardButton(
        text='Вернуться на главное меню',
        callback_data='return_to_start' #FIXXX
    )
    button2 = InlineKeyboardButton(
        text='Отменить слот!',
        callback_data='cancel_slot' #FIXXX
    )

    return InlineKeyboardMarkup(inline_keyboard=[[button1], [button2]])