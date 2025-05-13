from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.enums.parse_mode import ParseMode
import sqlite3

from aiohttp import request

import app.keyboards as kb



router = Router()
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Создание таблицы при первом запуске
cursor.execute('''CREATE TABLE IF NOT EXISTS bookings
               (id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date TEXT,
                slot INTEGER,
                description TEXT)''')
conn.commit()

@router.message(CommandStart())
async def send_welcome(message: Message):
    await message.answer("Привет! Это бот для записи в прачечную 14 общежития СПБГУ!", reply_markup=kb.main)

@router.message(F.text == "Посмотреть расписание")
async def show_schedule(message: Message):
    await message.answer("Вот ваше расписание", reply_markup=kb.dates_kb())

@router.message(F.text == "Мои брони")
async def show_schedule(message: Message):
    user_dates = cursor.execute('''SELECT date FROM bookings WHERE user_id=?''', (message.from_user.id,)).fetchall()
    user_dates = set(date[0] for date in user_dates)
    await message.answer("Даты на которые вы записались:", reply_markup=kb.dates_kb(user_dates))

@router.message(F.text == "Информация")
async def show_schedule(message: Message):
    await message.answer(
        "📬 <b>Добро пожаловать в информационную прачечную СПбГУ!</b>\n\n"
        "📍 <b>Расположение:</b>\n"
        "1-й этаж, центральное крыло\n\n"
        "🕓 <b>Часы работы:</b>\n"
        "Ежедневно, кроме праздничных дней\n"
        "⏰ с 9:00 до 21:00\n"
        "🍽 Обеденный перерыв: с 14:00 до 15:00\n\n"
        "💰 <b>Стоимость услуг:</b>\n"
        "🧺 Стирка — 120₽\n"
        "🔥 Сушка — 110₽\n\n"
        "💳 <b>Оплата:</b> <a href='https://pay.spbu.ru/additional-drying/ '>Перейти к оплате</a>\n\n"
        "📞 <b>Телефон для справок:</b>\n"
        "+7 (812) 363-60-00 (доб. 9114)",
        parse_mode=ParseMode.HTML
    )

@router.callback_query(F.data.startswith("date"))
async def date_seletected(callback: CallbackQuery):
    date = callback.data.split("_")[1]
    booked_slots = cursor.execute('''SELECT slot FROM bookings WHERE date=?''', (date,)).fetchall()
    booked_slots = [slot[0] for slot in booked_slots]
    user_slot = cursor.execute('''SELECT slot FROM bookings WHERE user_id=? AND date=?''',
                               (callback.from_user.id,date)).fetchone()
    user_slot = user_slot[0] if user_slot is not None else None

    await callback.message.answer("Tra-lalalal", reply_markup=kb.slots_kb(date,booked_slots, user_slot))

@router.callback_query(F.data.startswith("slot"))
async def slot_selected(callback: CallbackQuery):
    _, date, slot = callback.data.split("_")
    user_id = callback.from_user.id
    active_slot = cursor.execute('''SELECT slot FROM bookings WHERE user_id=? AND date=?''', (user_id,date)).fetchone()
    if active_slot is not None:
        await callback.message.answer(f"Вы уже записались под номером {active_slot[0]}")
    else:
        cursor.execute('''INSERT INTO bookings (user_id, date, slot) VALUES (?, ?, ?)''', (user_id,date,slot))
        conn.commit()
        await callback.answer(f"Вы записались на {date} под слотом {slot}")

@router.callback_query(F.data.startswith("close_slot"))
async def close_slot(callback: CallbackQuery):
    await callback.answer("Этот слот занят! Запишитесь на другой слот или в другой день")

@router.callback_query(F.data.startswith("my_slot"))
async def my_slot(callback: CallbackQuery):
    _, _ , date, slot = callback.data.split("_")
    await callback.message.answer(f"Это слот {slot} на {date} зарезервирован за Вами! Хотите ли вы его отменить?",
                                  reply_markup=kb.cancel_slot())