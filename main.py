import asyncio
import logging

import config
from aiogram import Bot, Dispatcher
from aiogram.types import Message, ReplyKeyboardMarkup
from aiogram.filters import CommandStart
from app.handlers import router
import app.keyboards as kb



bot = Bot(token=config.API_TOKEN)
dp = Dispatcher()

async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exiting...")