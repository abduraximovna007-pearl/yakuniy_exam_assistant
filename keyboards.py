from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_menu(is_admin: bool = False):
    keyboard = [
        [KeyboardButton(text="📝 Test ishlash"), KeyboardButton(text="📤 Test yuklash")],
        [KeyboardButton(text="🏆 Reyting"), KeyboardButton(text="👤 Profil")],
    ]
    if is_admin:
        keyboard.append([KeyboardButton(text="👨‍💼 Admin panel")])
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
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

def admin_panel_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Ochiq testlar va ishlaganlar", callback_data="admin_tests_list")],
            [InlineKeyboardButton(text="👥 Oxirgi ishlagan o'quvchilar", callback_data="admin_recent_students")],
            [InlineKeyboardButton(text="🌐 Barcha o'quvchilar reytingi", callback_data="admin_global_rating")],
            [InlineKeyboardButton(text="📊 Tizim statistikasi", callback_data="admin_stats")],
        ]
    )

def admin_back_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Admin panelga qaytish", callback_data="admin_panel_main")]
        ]
    )

def start_test_keyboard(test_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Testni boshlash", callback_data=f"start_test_{test_id}")]
        ]
    )

def answer_keyboard(session_id: int, q_index: int, variants: dict):
    emoji_map = {"A": "🅰️ A", "B": "🅱️ B", "C": "🅲 C", "D": "🅳 D"}
    btns = []
    for letter in ["A", "B", "C", "D"]:
        if letter in variants and variants[letter]:
            btns.append(
                InlineKeyboardButton(
                    text=emoji_map.get(letter, letter),
                    callback_data=f"answer_{session_id}_{q_index}_{letter}"
                )
            )
    rows = [btns[i:i+2] for i in range(0, len(btns), 2)]
    rows.append([InlineKeyboardButton(text="🛑 Testni yakunlash (Natijani ko'rish)", callback_data=f"stop_test_{session_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def show_errors_keyboard(session_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🤖 Xatolar uchun AI tushuntirish", callback_data=f"errors_{session_id}")]
        ]
    )

def ai_explanation_keyboard(session_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🤖 Xatolar uchun AI tushuntirish", callback_data=f"errors_{session_id}")]
        ]
    )