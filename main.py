import asyncio
import logging

import aiosqlite

import config
from aiogram import Bot, Dispatcher
from app.handlers import router, init_db
from middleware import DBMiddleware


bot = Bot(token=config.API_TOKEN)
dp = Dispatcher()


async def main():
    db_connection = await aiosqlite.connect("db.sqlite3")
    dp.update.outer_middleware(DBMiddleware(db_connection))
    dp.include_router(router)
    await init_db(db_connection)
    await dp.start_polling(bot, db=db_connection)
    await db_connection.close()


if __name__ == "__main__":
    try:
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            level=logging.INFO,
        )
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exiting...")
