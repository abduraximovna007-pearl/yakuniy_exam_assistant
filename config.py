import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8690557621:AAGRFNY86IKRRuUTl1S5bCzr3ivwmy7bmX4")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7101711362"))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///testbot.db")
TEST_PRICE = int(os.getenv("TEST_PRICE", "15000"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

def is_admin(telegram_id: int) -> bool:
    return telegram_id == ADMIN_ID or telegram_id == 7101711362