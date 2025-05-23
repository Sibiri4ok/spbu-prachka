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
    [KeyboardButton(text="Статус")],
    ], resize_keyboard=True)

main_admin = ReplyKeyboardMarkup(keyboard= [
    [KeyboardButton(text="Изменить расписание")],
    [KeyboardButton(text="Добавить / изменить статус")],
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

def dates_admin_kb(user_dates=None):
    builder = InlineKeyboardBuilder()
    dates = [datetime.now(TIMEZONE) + timedelta(days=i) for i in range(7)]
    for dt in dates:
        if user_dates is None or dt.strftime('%Y-%m-%d') in user_dates:
            builder.button(
                text=dt.strftime("%d.%m"),
                callback_data=f"admin_date_{dt.strftime('%Y-%m-%d')}"
            )
    builder.adjust(4)
    return builder.as_markup()

def slots_kb(date: str, booked_slots: List, user_slot: int):
    builder = InlineKeyboardBuilder()
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

def slots_admin_kb(date: str, booked_slots: List):
    slots = {
        slots[2]: (slots[0], slots[1]) for slots in booked_slots
    }
    builder = InlineKeyboardBuilder()
    for slot_num in range(1, 21):
        if slot_num in slots:
            builder.button(
                text=f"{slot_num}. {slots[slot_num][0]}",
                callback_data=f"admin_close_slot_{date}_{slot_num}"
            )
        else:
            builder.button(
                text=f"{slot_num}. Свободное место",
                callback_data=f"admin_available_slot_{date}_{slot_num}"
            )
    builder.adjust(2)
    return builder.as_markup()

def cancel_slot(date: str, user_slot: int):
    button1 = InlineKeyboardButton(
        text=f"Вернуться назад",
        callback_data=f"back_to_slots_{date}_{user_slot}"
    )
    button2 = InlineKeyboardButton(
        text='Отменить слот',
        callback_data=f'cancel_slot_{date}_{user_slot}'
    )

    return InlineKeyboardMarkup(inline_keyboard=[[button1], [button2]])

def admin_close_options_slot(date: str, user_slot: int):

    button1 = InlineKeyboardButton(
        text=f"Вернуться назад",
        callback_data=f"admin_date_{date}"
    )
    button2 = InlineKeyboardButton(
        text='Удалить слот',
        callback_data=f'admin_delete_slot_{date}_{user_slot}'
    )
    return InlineKeyboardMarkup(inline_keyboard=[[button1], [button2]])

def admin_available_options_slot(date: str, user_slot: int):

    button1 = InlineKeyboardButton(
        text=f"Вернуться назад",
        callback_data=f"admin_date_{date}"
    )
    button2 = InlineKeyboardButton(
        text='Добавить студента',
        callback_data=f'admin_add_slot_{date}_{user_slot}'
    )
    return InlineKeyboardMarkup(inline_keyboard=[[button1], [button2]])

def add_remove_info():
    button1 = InlineKeyboardButton(
        text=f"Добавить сообщение",
        callback_data=f"add_info"
    )
    button2 = InlineKeyboardButton(
        text='Удалить сообщение',
        callback_data=f'remove_info'
    )
    return InlineKeyboardMarkup(inline_keyboard=[[button1], [button2]])