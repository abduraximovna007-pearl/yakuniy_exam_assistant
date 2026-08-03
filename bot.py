import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN
from database import init_db
from handlers import start, upload, test_take, rating, admin_actions

logging.basicConfig(level=logging.INFO)

async def main():
    await init_db()
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    dp.include_routers(
        start.router,
        upload.router,
        test_take.router,
        rating.router,
        admin_actions.router,
    )
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
