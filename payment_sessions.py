# Pending payment sessions — user fayl yuklaydi, admin karta raqam yuborguncha saqlanadi
# {telegram_user_id: {"test_id": int, "user_db_id": int, "title": str, "q_count": int}}

_pending: dict = {}


def set_pending(telegram_id: int, test_id: int, user_db_id: int, title: str, q_count: int):
    _pending[telegram_id] = {
        "test_id": test_id,
        "user_db_id": user_db_id,
        "title": title,
        "q_count": q_count
    }


def get_pending(telegram_id: int) -> dict | None:
    return _pending.get(telegram_id)


def clear_pending(telegram_id: int):
    _pending.pop(telegram_id, None)
