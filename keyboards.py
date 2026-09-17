from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Test ishlash"), KeyboardButton(text="📤 Test yuklash")],
            [KeyboardButton(text="🏆 Reyting"), KeyboardButton(text="👤 Profil")],
        ],
        resize_keyboard=True
    )

def cancel():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True
    )

def admin_confirm_keyboard(test_id: int, user_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"confirm_{test_id}_{user_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{test_id}_{user_id}"),
            ],
            [
                InlineKeyboardButton(text="💳 Karta raqami yuborish", callback_data=f"send_card_{test_id}_{user_id}"),
            ]
        ]
    )

def start_test_keyboard(test_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Testni boshlash", callback_data=f"start_test_{test_id}")]
        ]
    )

def answer_keyboard(session_id: int, q_index: int, variants: dict):
    rows = []
    for letter in ["A", "B", "C", "D"]:
        if letter in variants and variants[letter]:
            val = str(variants[letter]).strip()
            # Kengaytirilgan tugma matni (har bir qatorda 1 tadan to'liq kenglikda)
            btn_text = f"{letter}) {val[:60]}..." if len(val) > 60 else f"{letter}) {val}"
            rows.append([
                InlineKeyboardButton(
                    text=btn_text,
                    callback_data=f"answer_{session_id}_{q_index}_{letter}"
                )
            ])
    rows.append([InlineKeyboardButton(text="🛑 Testni yakunlash (Natijani ko'rish)", callback_data=f"stop_test_{session_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def show_errors_keyboard(session_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Xatolarni ko'rish", callback_data=f"errors_{session_id}")]
        ]
    )