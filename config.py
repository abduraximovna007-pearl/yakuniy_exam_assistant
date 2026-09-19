import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///testbot.db")
TEST_PRICE = int(os.getenv("TEST_PRICE", "15000"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")