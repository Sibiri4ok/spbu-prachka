from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from config import TIMEZONE
from datetime import datetime
from aiogram.enums.parse_mode import ParseMode
import sqlite3

from aiohttp import request

import app.keyboards as kb
from config import ADMINS

router = Router()
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Создание таблицы при первом запуске
cursor.execute('''CREATE TABLE IF NOT EXISTS bookings
               (id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name VARCHAR(30),
                description VARCHAR(50),
                date TEXT,
                slot INTEGER)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS info
               (id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                content TEXT)''')
conn.commit()


class BookingForm(StatesGroup):
    name = State()
    description = State()

class AdminBookingForm(StatesGroup):
    name = State()
    description = State()

class InfoMessage(StatesGroup):
    content = State()

class IdMessage(StatesGroup):
    ID = State()

@router.message(CommandStart())
async def send_welcome(message: Message):
    await message.answer("Привет! Это бот для записи в прачечную №14 СПБГУ!", reply_markup=kb.main)
    if message.from_user.id in ADMINS:
        await message.answer("Вы авторизовались как администратор!", reply_markup=kb.main_admin)

@router.message(F.text == "Посмотреть расписание")
async def show_schedule(message: Message):
    await message.answer("Расписание:", reply_markup=kb.dates_kb())

@router.message(F.text == "Мои брони")
async def show_schedule(message: Message):
    user_dates = cursor.execute('''SELECT date FROM bookings WHERE user_id=?''',
                                (message.from_user.id,)).fetchall()
    user_dates = set(date[0] for date in user_dates)
    if len(user_dates) == 0:
        await message.answer("У Вас нет забронированных дат!")
    else:
        await message.answer("Даты на которые вы записались:", reply_markup=kb.dates_kb(user_dates))



@router.message(F.text == "Информация")
async def show_info(message: Message):
    await message.answer(
        "📬 <b>Добро пожаловать в прачечную №14 СПбГУ!</b>\n\n"
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
    msg = cursor.execute('''SELECT date, content FROM info''').fetchall()
    print(msg)

    for date, content in msg:
        await message.answer(f"Дата: {date.split('-')[-1]}.{date.split('-')[-2]}\nСообщение: {content}")



@router.callback_query(F.data.startswith("date"))
async def date_seletected(callback: CallbackQuery):
    date = callback.data.split("_")[1]
    booked_slots = cursor.execute('''SELECT slot FROM bookings WHERE date=?''', (date,)).fetchall()
    booked_slots = [slot[0] for slot in booked_slots]
    user_slot = cursor.execute('''SELECT slot FROM bookings WHERE user_id=? AND date=?''',
                               (callback.from_user.id,date)).fetchone()
    user_slot = user_slot[0] if user_slot is not None else None

    await callback.message.answer(f"Слоты на {date.split('-')[-1]}.{date.split('-')[-2]}:",
                                  reply_markup=kb.slots_kb(date,booked_slots, user_slot))

@router.callback_query(F.data.startswith("slot"))
async def slot_selected(callback: CallbackQuery, state: FSMContext):
    _, date, slot = callback.data.split("_")
    user_id = callback.from_user.id
    active_slot = cursor.execute('''SELECT slot FROM bookings WHERE user_id=? AND date=?''',
                                 (user_id,date)).fetchone()
    if active_slot is not None:
        await callback.answer(f"Вы уже записались на слот №{active_slot[0]}")
    else:
        await state.update_data(date=date, slot=slot)
        await state.set_state(BookingForm.name)
        await callback.message.answer(f"Введите ваше ФИО:")


@router.message(BookingForm.name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(BookingForm.description)
    await message.answer("Какой услугой Вы хотите воспользоваться и в каком количестве (стирка/сушка)?")

@router.message(BookingForm.description)
async def get_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    data = await state.get_data()
    user_id = message.from_user.id

    cursor.execute('''INSERT INTO bookings (user_id, name, description, date, slot ) VALUES (?, ?, ?, ?, ?)''',
                   (user_id, data['name'], data['description'], data['date'], data['slot']))

    conn.commit()

    booked_slots = cursor.execute('''SELECT slot FROM bookings WHERE date=?''', (data['date'], )).fetchall()
    booked_slots = [slot[0] for slot in booked_slots]
    await message.answer(f"Вы записаны на {data['date'].split('-')[-1]}.{data['date'].split('-')[-2]} под слотом №{data['slot']}!")
    await message.answer(f"Слоты на {data['date'].split('-')[-1]}.{data['date'].split('-')[-2]}:",
                         reply_markup=kb.slots_kb(data['date'], booked_slots, int(data['slot'])))
    await state.clear()
@router.callback_query(F.data.startswith("close_slot"))
async def close_slot(callback: CallbackQuery):
    await callback.answer("Этот слот занят! Запишитесь на другой слот или в другой день")

@router.callback_query(F.data.startswith("my_slot"))
async def my_slot(callback: CallbackQuery):
    date, slot = callback.data.split("_")[2:]
    await callback.message.answer(f"Этот слот №{slot} на {date.split('-')[-1]}.{date.split('-')[-2]} "
                                  f"зарезервирован за Вами! Хотите ли Вы его отменить?",
                                  reply_markup=kb.cancel_slot(date, int(slot)))

@router.callback_query(F.data.startswith("cancel_slot"))
async def cancel_slot(callback: CallbackQuery):
    date, slot = callback.data.split("_")[2:]
    cursor.execute('''DELETE FROM bookings WHERE date=? AND slot=?''', (date, slot)).fetchone()
    conn.commit()

    booking_slots = cursor.execute('''SELECT slot FROM bookings WHERE date=?''', (date,)).fetchall()
    booking_slots = [slot[0] for slot in booking_slots]

    await callback.answer(f"Ваш слот №{slot} на {date.split('-')[-1]}.{date.split('-')[-2]} был отменен")

    await callback.message.answer(f"Слоты на {date.split('-')[-1]}.{date.split('-')[-2]}:",
                                  reply_markup=kb.slots_kb(date, booking_slots, None))

@router.callback_query(F.data.startswith("back_to_slots"))
async def back_to_slots(callback: CallbackQuery):
    date, user_slot = callback.data.split("_")[-2:]
    booked_slots = cursor.execute('''SELECT slot
                                     FROM bookings
                                     WHERE date =?''', (date,)).fetchall()
    booked_slots = [slot[0] for slot in booked_slots]
    await callback.message.edit_reply_markup(reply_markup=kb.slots_kb(date, booked_slots, int(user_slot)))

@router.message(F.text == 'Изменить расписание')
async def admin_show_schedule(message: Message):
    await message.answer("Выберите дату:", reply_markup=kb.dates_admin_kb())

@router.message(F.text == 'Добавить/удалить информацию')
async def admin_show_info(message: Message):
    await message.answer("Что вы хотите сделать?", reply_markup=kb.add_remove_info())

@router.callback_query(F.data == 'remove_info')
async def remove_info(callback: CallbackQuery, state: FSMContext):
    messages = cursor.execute('''SELECT * FROM info''').fetchall()

    await state.set_state(IdMessage.ID)
    await callback.message.answer("Выберите id сообщения, которое хотите удалить")
    for id, date, content in messages:
        await callback.message.answer(f"id: {id} Дата: {date} \nСообщение: {content}")

@router.message(IdMessage.ID)
async def get_id(message: Message, state: FSMContext):
    await state.update_data(id = message.text)
    data = await state.get_data()
    validate_id = cursor.execute('''SELECT * FROM info WHERE id=?''', (data['id'],)).fetchone()
    cursor.execute('''DELETE FROM info WHERE id=?''', (data['id'],)).fetchone()
    conn.commit()

    await state.clear()
    if validate_id is None:
        await message.answer("Сообщения с таким id нет")
    else:
        await message.answer(f"Сообщение с id={data['id']} было успешно удалено!")


@router.callback_query(F.data == 'add_info')
async def add_info(callback: CallbackQuery, state: FSMContext):
    await state.set_state(InfoMessage.content)
    await callback.message.answer("Введите информацию")

@router.message(InfoMessage.content)
async def get_info(message: Message, state: FSMContext):
    await state.update_data(content=message.text)

    msg = await state.get_data()

    cursor.execute('''INSERT INTO info (date, content) VALUES (?, ?)''',
                   (datetime.now(TIMEZONE).strftime('%Y-%m-%d'),msg['content'],))
    conn.commit()

    await state.clear()

    await message.answer("Информация успешна добавлена!")



@router.callback_query(F.data.startswith("admin_date"))
async def admin_date_selected(callback: CallbackQuery):
    _, _, date = callback.data.split("_")
    booked_slots = cursor.execute('''SELECT name, description, slot FROM bookings WHERE date=? ORDER BY slot''',
                                  (date,)).fetchall()
    await callback.message.answer(f"Слоты на {date.split('-')[-1]}.{date.split('-')[-2]}:",
                                  reply_markup=kb.slots_admin_kb(date, booked_slots))

@router.callback_query(F.data.startswith("admin_close_slot"))
async def admin_slot_selected(callback: CallbackQuery):
    _, _, _, date, slot_num = callback.data.split("_")
    await callback.message.answer('Что вы хотите сделать?',
                                  reply_markup=kb.admin_close_options_slot(date, int(slot_num)))

@router.callback_query(F.data.startswith("admin_delete_slot"))
async def admin_delete_slot(callback: CallbackQuery):
    _, _, _, date, slot_num = callback.data.split("_")
    name, description, date, slot  = cursor.execute('''SELECT name, description, date, slot FROM bookings WHERE date=? AND slot=?''',
                                  (date, slot_num)).fetchone()
    cursor.execute('''DELETE FROM bookings WHERE date=? and slot=?''', (date,slot_num)).fetchone()
    conn.commit()

    booked_slots = cursor.execute('''SELECT name, description, slot FROM bookings WHERE date=? ORDER BY slot''',
                                  (date,)).fetchall()
    await callback.answer(f"Слот под номером {slot} для {name} был успешно удален!")
    await callback.message.answer(f"Слоты на {date.split('-')[-1]}.{date.split('-')[-2]}:",
                                  reply_markup=kb.slots_admin_kb(date, booked_slots))

@router.callback_query(F.data.startswith("admin_available_slot"))
async def admin_available_slot(callback: CallbackQuery):
    _, _, _, date, slot_num = callback.data.split("_")
    await callback.message.answer('Что вы хотите сделать?',
                                  reply_markup=kb.admin_available_options_slot(date, int(slot_num)))

@router.callback_query(F.data.startswith("admin_add_slot_"))
async def admin_add_slot(callback: CallbackQuery, state: FSMContext):
    _, _, _, date, slot_num = callback.data.split("_")
    await state.update_data(date=date, slot=int(slot_num))
    await state.set_state(AdminBookingForm.name)
    await callback.message.answer(f"Введите ФИО студента:")

@router.message(AdminBookingForm.name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AdminBookingForm.description)
    await message.answer("Какая услуга нужна студенту и в каком количестве (стирка/сушка)?")

@router.message(AdminBookingForm.description)
async def get_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    data = await state.get_data()
    user_id = message.from_user.id

    cursor.execute('''INSERT INTO bookings (user_id, name, description, date, slot ) VALUES (?, ?, ?, ?, ?)''',
                   (user_id, data['name'], data['description'], data['date'], data['slot']))

    conn.commit()

    booked_slots = cursor.execute('''SELECT name, description, slot FROM bookings WHERE date=? ORDER BY slot''',
                                  (data['date'],)).fetchall()
    await message.answer(f"Вы записали сдудента {data['name']} на {data['date'].split('-')[-1]}.{data['date'].split('-')[-2]} под слотом №{data['slot']}!")
    await message.answer(f"Слоты на {data['date'].split('-')[-1]}.{data['date'].split('-')[-2]}:",
                         reply_markup=kb.slots_admin_kb(data['date'], booked_slots))
    await state.clear()

