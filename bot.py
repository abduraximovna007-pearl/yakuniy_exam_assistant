import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from config import BOT_TOKEN, ADMIN_ID
from database import init_db, async_session
from models import User
from sqlalchemy import select, update, func
from handlers import start, upload, test_take, rating, admin_actions

logging.basicConfig(level=logging.INFO)

# Render.com avtomatik PORT va RENDER_EXTERNAL_URL beradi
PORT = int(os.environ.get("PORT", 8080))
DEFAULT_WEBHOOK = "https://yakuniy-exam-assistant.onrender.com"
WEBHOOK_HOST = (os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("WEBHOOK_URL") or DEFAULT_WEBHOOK).rstrip("/")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"


async def on_startup(bot: Bot):
    await init_db()
    try:
        async with async_session() as session:
            await session.execute(
                update(User).where(
                    (User.telegram_id == ADMIN_ID) |
                    (User.telegram_id == 7101711362) |
                    (func.lower(User.full_name).like("%durdona%"))
                ).values(role="admin")
            )
            await session.commit()
    except Exception as e:
        logging.error(f"Failed to auto-update admin role: {e}")

    if WEBHOOK_HOST and BOT_TOKEN:
        webhook_url = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
        await bot.set_webhook(webhook_url, drop_pending_updates=True)
        logging.info(f"Webhook set: {webhook_url}")
    else:
        logging.info("Webhook o'rnatilmadi")


async def on_shutdown(bot: Bot):
    logging.info("Bot shutting down...")


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

    async def api_users(request):
        async with async_session() as session:
            res = await session.execute(select(User))
            users = res.scalars().all()
            return web.json_response([
                {"id": u.id, "telegram_id": u.telegram_id, "name": u.full_name, "faculty": u.faculty, "group": u.group_name, "role": u.role}
                for u in users
            ])
    app.router.add_get("/api/users", api_users)

    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    return app


async def polling_mode():
    """Lokal polling rejimi (test uchun)"""
    await init_db()
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    await bot.delete_webhook(drop_pending_updates=True)
    dp = Dispatcher()
    dp.include_routers(
        start.router,
        upload.router,
        test_take.router,
        rating.router,
        admin_actions.router,
    )
    logging.info("Bot lokal polling rejimida ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    import sys
    if not BOT_TOKEN:
        logging.error("XATOLIK: BOT_TOKEN aniqlanmadi! Server Environment variables bo'limiga BOT_TOKEN qo'shing.")
        raise SystemExit("BOT_TOKEN is required!")

    if "--polling" in sys.argv or os.environ.get("MODE") == "polling":
        # Lokal polling rejimi
        asyncio.run(polling_mode())
    elif WEBHOOK_HOST or os.environ.get("PORT"):
        # Server rejimi — webhook / web server
        app = create_app()
        web.run_app(app, host="0.0.0.0", port=PORT)
    else:
        # Lokal rejimi — polling
        asyncio.run(polling_mode())
