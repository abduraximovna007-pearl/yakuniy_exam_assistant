from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from crud import (
    approve_test, reject_test, get_pending_test,
    get_test_participants, get_recent_completed_sessions,
    get_tests_with_stats, get_global_rating, get_system_stats,
    get_user
)
from config import ADMIN_ID, TEST_PRICE, is_admin
from database import async_session
from models import Question
from sqlalchemy import select, func
from states import AdminCardState
from keyboards import admin_panel_keyboard, admin_back_keyboard, admin_menu

router = Router()


async def check_is_admin(telegram_id: int) -> bool:
    if is_admin(telegram_id):
        return True
    user = await get_user(telegram_id)
    if user and user.role == "admin":
        return True
    return False


async def _count_questions(test_id: int) -> int:
    async with async_session() as db:
        count = await db.scalar(
            select(func.count(Question.id)).where(Question.test_id == test_id)
        )
        return count or 0


# ── Karta raqami yuborish ──────────────────────────────────────────────────

@router.callback_query(F.data.startswith("send_card_"))
async def request_card_number(callback: CallbackQuery, state: FSMContext):
    if not await check_is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return

    # Format: send_card_{test_id}_{telegram_user_id}
    parts = callback.data.split("_")
    test_id = int(parts[2])
    telegram_user_id = int(parts[3])

    test = await get_pending_test(test_id)
    if not test:
        await callback.answer("❌ Test topilmadi!", show_alert=True)
        return

    await state.set_state(AdminCardState.waiting_for_card)
    await state.update_data(test_id=test_id, telegram_user_id=telegram_user_id, title=test.title)

    await callback.message.answer(
        f"💳 <b>{test.title}</b> testi uchun\n"
        f"Foydalanuvchiga yuboriladigan <b>karta raqamini</b> kiriting:\n\n"
        "Masalan: <code>8600 1234 5678 9012</code>"
    )
    await callback.answer()


@router.message(AdminCardState.waiting_for_card)
async def handle_card_number(message: Message, state: FSMContext, bot: Bot):
    if not await check_is_admin(message.from_user.id):
        return

    data = await state.get_data()
    test_id = data.get("test_id")
    telegram_user_id = data.get("telegram_user_id")
    title = data.get("title", "Test")
    card_number = message.text.strip()

    await state.clear()

    # Userga karta raqamini yuborish
    try:
        await bot.send_message(
            chat_id=telegram_user_id,
            text=(
                f"💳 <b>To'lov ma'lumotlari</b>\n\n"
                f"📋 Test: <b>{title}</b>\n"
                f"💰 Miqdor: <b>{TEST_PRICE:,} so'm</b>\n"
                f"🏦 Karta raqami: <code>{card_number}</code>\n\n"
                "To'lovni amalga oshirib, <b>skrinshot (rasm)</b> yuboring 👇"
            )
        )
        await message.answer(
            f"✅ Karta raqami foydalanuvchiga yuborildi!\n"
            f"🏦 Karta: <code>{card_number}</code>"
        )
    except Exception as e:
        await message.answer(f"❌ Foydalanuvchiga yuborib bo'lmadi: {e}")


# ── Tasdiqlash / Rad etish ─────────────────────────────────────────────────

@router.callback_query(F.data.startswith("confirm_"))
async def confirm_test(callback: CallbackQuery, bot: Bot):
    if not await check_is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return

    parts = callback.data.split("_")
    test_id = int(parts[1])
    telegram_user_id = int(parts[2])

    test = await get_pending_test(test_id)
    if not test:
        await callback.answer("❌ Test topilmadi!", show_alert=True)
        return

    if test.status == "approved":
        await callback.answer("ℹ️ Test allaqachon tasdiqlangan!", show_alert=True)
        return

    q_count = await _count_questions(test_id)
    await approve_test(test_id, question_count=q_count)

    try:
        if callback.message.photo:
            await callback.message.edit_caption(
                (callback.message.caption or "") +
                f"\n\n✅ <b>TASDIQLANDI</b>\n❓ Savollar: {q_count} ta"
            )
        else:
            await callback.message.edit_text(
                callback.message.text + f"\n\n✅ <b>TASDIQLANDI</b>"
            )
    except Exception:
        pass

    await callback.answer("✅ Test tasdiqlandi!")

    try:
        await bot.send_message(
            chat_id=telegram_user_id,
            text=(
                f"🎉 <b>Tabriklaymiz!</b> Testingiz tasdiqlandi!\n\n"
                f"📋 Test: <b>{test.title}</b>\n"
                f"❓ Savollar: <b>{q_count} ta</b>\n\n"
                "Endi '📝 Test ishlash' bo'limida sizning testingiz mavjud! 🚀"
            )
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("reject_"))
async def reject_test_handler(callback: CallbackQuery, bot: Bot):
    if not await check_is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return

    parts = callback.data.split("_")
    test_id = int(parts[1])
    telegram_user_id = int(parts[2])

    test = await get_pending_test(test_id)
    if not test:
        await callback.answer("❌ Test topilmadi!", show_alert=True)
        return

    if test.status == "rejected":
        await callback.answer("ℹ️ Test allaqachon rad etilgan!", show_alert=True)
        return

    await reject_test(test_id)

    try:
        if callback.message.photo:
            await callback.message.edit_caption(
                (callback.message.caption or "") + "\n\n❌ <b>RAD ETILDI</b>"
            )
        else:
            await callback.message.edit_text(
                callback.message.text + "\n\n❌ <b>RAD ETILDI</b>"
            )
    except Exception:
        pass

    await callback.answer("❌ Test rad etildi!")

    try:
        await bot.send_message(
            chat_id=telegram_user_id,
            text=(
                f"❌ Testingiz rad etildi.\n\n"
                f"📋 Test: <b>{test.title}</b>\n\n"
                "Muammo tuzatilib, qayta yuklashingiz mumkin: '📤 Test yuklash'"
            )
        )
    except Exception:
        pass


# ── Admin Panel va Natijalar ──────────────────────────────────────────────

@router.message(Command("admin"))
@router.message(F.text == "👨‍💼 Admin panel")
async def show_admin_panel(message: Message):
    if not await check_is_admin(message.from_user.id):
        await message.answer("❌ Bu bo'lim faqat admin uchun!")
        return

    await message.answer(
        "👨‍💼 <b>Admin boshqaruv paneli</b>\n\n"
        "Quyidagi bo'limlardan birini tanlang 👇",
        reply_markup=admin_menu()
    )


@router.message(F.text == "📋 Ochiq testlar va ishlaganlar")
async def msg_admin_tests_list(message: Message):
    if not await check_is_admin(message.from_user.id):
        return

    tests_stats = await get_tests_with_stats()
    if not tests_stats:
        await message.answer("📭 Hozircha tasdiqlangan (ochiq) testlar mavjud emas.")
        return

    btns = []
    for item in tests_stats:
        t = item["test"]
        count = item["participants_count"]
        btns.append([
            InlineKeyboardButton(
                text=f"📋 {t.title} ({count} nafar)",
                callback_data=f"admin_test_view_{t.id}"
            )
        ])

    await message.answer(
        "📋 <b>Ochiq testlar ro'yxati:</b>\n\n"
        "O'quvchilar natijalarini ko'rish uchun testni bosing 👇",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )


@router.message(F.text == "👥 Oxirgi ishlagan o'quvchilar")
async def msg_admin_recent_students(message: Message):
    if not await check_is_admin(message.from_user.id):
        return

    sessions = await get_recent_completed_sessions(limit=25)
    if not sessions:
        await message.answer("👥 Hozircha hech kim test ishlamagan.")
        return

    lines = ["👥 <b>Oxirgi test ishlagan o'quvchilar (oxirgi 25 ta):</b>\n"]
    for i, (ts, user, t) in enumerate(sessions, 1):
        pct = round(ts.score / ts.total * 100) if ts.total else 0
        date_str = ts.completed_at.strftime("%d.%m %H:%M") if ts.completed_at else "—"
        lines.append(
            f"{i}. <b>{user.full_name}</b> ({user.faculty}, {user.group_name})\n"
            f"   📋 Test: {t.title}\n"
            f"   🎯 Natija: <b>{ts.score}/{ts.total}</b> ({pct}%) | ⏱ {date_str}"
        )

    text = "\n\n".join(lines)
    if len(text) > 4000:
        text = text[:3950] + "\n\n<i>...(qolgan natijalar qisqartirildi)</i>"

    await message.answer(text)


@router.message(F.text == "🌐 Barcha o'quvchilar reytingi")
async def msg_admin_global_rating(message: Message):
    if not await check_is_admin(message.from_user.id):
        return

    ratings = await get_global_rating(limit=30)
    if not ratings:
        await message.answer("🏆 Hozircha hech qanday reyting ma'lumoti mavjud emas.")
        return

    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    lines = ["🌐 <b>Barcha o'quvchilar bo'yicha umumiy reyting:</b>\n"]

    for i, (u, total_score) in enumerate(ratings, 1):
        medal = medals.get(i, f"{i}.")
        lines.append(
            f"{medal} <b>{u.full_name}</b> ({u.faculty}, {u.group_name})\n"
            f"   🎯 Jami to'plagan bali: <b>{total_score or 0} ball</b>"
        )

    text = "\n\n".join(lines)
    if len(text) > 4000:
        text = text[:3950] + "\n\n<i>...(qolgan reyting qisqartirildi)</i>"

    await message.answer(text)


@router.message(F.text == "📊 Tizim statistikasi")
async def msg_admin_stats(message: Message):
    if not await check_is_admin(message.from_user.id):
        return

    stats = await get_system_stats()
    text = (
        "📊 <b>Tizim statistikasi:</b>\n\n"
        f"👥 Ro'yxatdan o'tgan talabalar: <b>{stats['users']} nafar</b>\n"
        f"📋 Tasdiqlangan ochiq testlar: <b>{stats['tests']} ta</b>\n"
        f"❓ Bazadagi jami savollar: <b>{stats['questions']} ta</b>\n"
        f"🏁 Ishlangan test urinishlari: <b>{stats['sessions']} ta</b>"
    )
    await message.answer(text)


@router.callback_query(F.data == "admin_panel_main")
async def callback_admin_panel_main(callback: CallbackQuery):
    if not await check_is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return

    await callback.message.edit_text(
        "👨‍💼 <b>Admin boshqaruv paneli</b>\n\n"
        "Quyidagi bo'limlardan birini tanlang:",
        reply_markup=admin_panel_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_tests_list")
async def admin_tests_list_handler(callback: CallbackQuery):
    if not await check_is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return

    tests_stats = await get_tests_with_stats()
    if not tests_stats:
        await callback.message.edit_text(
            "📭 Hozircha tasdiqlangan (ochiq) testlar mavjud emas.",
            reply_markup=admin_back_keyboard()
        )
        await callback.answer()
        return

    btns = []
    for item in tests_stats:
        t = item["test"]
        count = item["participants_count"]
        btns.append([
            InlineKeyboardButton(
                text=f"📋 {t.title} ({count} nafar)",
                callback_data=f"admin_test_view_{t.id}"
            )
        ])
    btns.append([InlineKeyboardButton(text="◀️ Admin panelga qaytish", callback_data="admin_panel_main")])

    await callback.message.edit_text(
        "📋 <b>Ochiq testlar ro'yxati:</b>\n\n"
        "O'quvchilar natijalarini ko'rish uchun testni tanlang 👇",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_test_view_"))
async def admin_test_view_handler(callback: CallbackQuery):
    if not await check_is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return

    test_id = int(callback.data.split("_")[-1])
    test = await get_pending_test(test_id)
    if not test:
        await callback.answer("❌ Test topilmadi!", show_alert=True)
        return

    participants = await get_test_participants(test_id)
    if not participants:
        await callback.message.edit_text(
            f"📋 <b>{test.title}</b>\n\n"
            f"❓ Jami savollar: {test.question_count} ta\n"
            f"👥 Ishlagan o'quvchilar: 0 nafar\n\n"
            "Hozircha hech bir o'quvchi bu testni ishlamagan.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Testlar ro'yxatiga qaytish", callback_data="admin_tests_list")]
            ])
        )
        await callback.answer()
        return

    lines = [
        f"📋 <b>{test.title}</b> testi natijalari:\n"
        f"👥 Jami ishlaganlar: <b>{len(participants)} nafar</b>\n"
    ]

    for i, (ts, user) in enumerate(participants, 1):
        pct = round(ts.score / ts.total * 100) if ts.total else 0
        date_str = ts.completed_at.strftime("%d.%m.%Y %H:%M") if ts.completed_at else "—"
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        lines.append(
            f"{emoji} <b>{user.full_name}</b>\n"
            f"   🏛️ Fakultet: {user.faculty} | Guruh: {user.group_name}\n"
            f"   🎯 Ball: <b>{ts.score}/{ts.total}</b> ({pct}%) | ⏱ {date_str}"
        )

    text = "\n\n".join(lines)
    if len(text) > 4000:
        text = text[:3950] + "\n\n<i>...(qolgan natijalar qisqartirildi)</i>"

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Testlar ro'yxatiga qaytish", callback_data="admin_tests_list")]
        ])
    )
    await callback.answer()


@router.callback_query(F.data == "admin_recent_students")
async def admin_recent_students_handler(callback: CallbackQuery):
    if not await check_is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return

    sessions = await get_recent_completed_sessions(limit=25)
    if not sessions:
        await callback.message.edit_text(
            "👥 Hozircha hech kim test ishlamagan.",
            reply_markup=admin_back_keyboard()
        )
        await callback.answer()
        return

    lines = ["👥 <b>Oxirgi test ishlagan o'quvchilar (oxirgi 25 ta):</b>\n"]
    for i, (ts, user, t) in enumerate(sessions, 1):
        pct = round(ts.score / ts.total * 100) if ts.total else 0
        date_str = ts.completed_at.strftime("%d.%m %H:%M") if ts.completed_at else "—"
        lines.append(
            f"{i}. <b>{user.full_name}</b> ({user.faculty}, {user.group_name})\n"
            f"   📋 Test: {t.title}\n"
            f"   🎯 Natija: <b>{ts.score}/{ts.total}</b> ({pct}%) | ⏱ {date_str}"
        )

    text = "\n\n".join(lines)
    if len(text) > 4000:
        text = text[:3950] + "\n\n<i>...(qolgan natijalar qisqartirildi)</i>"

    await callback.message.edit_text(
        text,
        reply_markup=admin_back_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_global_rating")
async def admin_global_rating_handler(callback: CallbackQuery):
    if not await check_is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return

    ratings = await get_global_rating(limit=30)
    if not ratings:
        await callback.message.edit_text(
            "🏆 Hozircha hech qanday reyting ma'lumoti mavjud emas.",
            reply_markup=admin_back_keyboard()
        )
        await callback.answer()
        return

    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    lines = ["🌐 <b>Barcha o'quvchilar bo'yicha umumiy reyting:</b>\n"]

    for i, (u, total_score) in enumerate(ratings, 1):
        medal = medals.get(i, f"{i}.")
        lines.append(
            f"{medal} <b>{u.full_name}</b> ({u.faculty}, {u.group_name})\n"
            f"   🎯 Jami to'plagan bali: <b>{total_score or 0} ball</b>"
        )

    text = "\n\n".join(lines)
    if len(text) > 4000:
        text = text[:3950] + "\n\n<i>...(qolgan reyting qisqartirildi)</i>"

    await callback.message.edit_text(
        text,
        reply_markup=admin_back_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_stats")
async def admin_stats_handler(callback: CallbackQuery):
    if not await check_is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return

    stats = await get_system_stats()
    text = (
        "📊 <b>Tizim statistikasi:</b>\n\n"
        f"👥 Ro'yxatdan o'tgan talabalar: <b>{stats['users']} nafar</b>\n"
        f"📋 Tasdiqlangan ochiq testlar: <b>{stats['tests']} ta</b>\n"
        f"❓ Bazadagi jami savollar: <b>{stats['questions']} ta</b>\n"
        f"🏁 Ishlangan test urinishlari: <b>{stats['sessions']} ta</b>"
    )

    await callback.message.edit_text(
        text,
        reply_markup=admin_back_keyboard()
    )
    await callback.answer()


