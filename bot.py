import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from config import BOT_TOKEN
from database import init_db
from handlers import start, upload, test_take, rating, admin_actions

logging.basicConfig(level=logging.INFO)

# Render.com avtomatik PORT beradi
PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_HOST = os.environ.get("WEBHOOK_URL", "")  # Render URL
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"


async def on_startup(bot: Bot):
    await init_db()
    if WEBHOOK_HOST:
        webhook_url = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
        await bot.set_webhook(webhook_url)
        logging.info(f"Webhook set: {webhook_url}")
    else:
        logging.info("WEBHOOK_URL not set — running in polling mode")


async def on_shutdown(bot: Bot):
    if WEBHOOK_HOST:
        await bot.delete_webhook()


def create_app() -> web.Application:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    dp.include_routers(
        start.router,
        upload.router,
        test_take.router,
        rating.router,
        admin_actions.router,
    )
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()

    # Health check — Render botni tirik ko'radi
    async def health(request):
        return web.Response(text="OK")
    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    return app


async def polling_mode():
    """WEBHOOK_URL yo'q bo'lsa — lokal polling (test uchun)"""
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
    if WEBHOOK_HOST:
        # Server rejimi — webhook
        app = create_app()
        web.run_app(app, host="0.0.0.0", port=PORT)
    else:
        # Lokal rejimi — polling
        asyncio.run(polling_mode())
