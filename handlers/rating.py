from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from crud import get_user, get_rating, get_user_scores, get_global_rating, get_user_completed_sessions
from keyboards import main_menu, show_errors_keyboard
from database import async_session
from models import TestSession, Test, Question

router = Router()


@router.message(F.text == "🏆 Reyting")
async def show_rating(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Avval ro'yxatdan o'ting. /start")
        return

    results = await get_rating(user.faculty, user.group_name)
    global_btn = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌐 Umumiy reyting (Barcha talabalar)", callback_data="show_global_rating")]
        ]
    )

    if not results:
        await message.answer(
            f"📊 <b>{user.faculty} — {user.group_name}</b>\n\n"
            "Guruhingizda hozircha reyting ma'lumoti yo'q.\n"
            "Umumiy reytingni ko'rish uchun pastdagi tugmani bosing 👇",
            reply_markup=global_btn
        )
        return

    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    text = f"🏆 <b>Reyting: {user.faculty} — {user.group_name}</b>\n\n"

    for i, (u, score) in enumerate(results, 1):
        medal = medals.get(i, f"{i}.")
        you = " 👈 <b>Sen</b>" if u.telegram_id == message.from_user.id else ""
        text += f"{medal} {u.full_name} — <b>{score or 0}</b> ball{you}\n"

    await message.answer(text, reply_markup=global_btn)


@router.callback_query(F.data == "show_global_rating")
async def show_global_rating_callback(callback: CallbackQuery):
    ratings = await get_global_rating(limit=30)
    if not ratings:
        await callback.answer("Hozircha reyting ma'lumoti yo'q.", show_alert=True)
        return

    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    text = "🌐 <b>Umumiy reyting (Barcha talabalar):</b>\n\n"
    for i, (u, score) in enumerate(ratings, 1):
        medal = medals.get(i, f"{i}.")
        you = " 👈 <b>Sen</b>" if u.telegram_id == callback.from_user.id else ""
        text += f"{medal} {u.full_name} ({u.faculty}, {u.group_name}) — <b>{score or 0}</b> ball{you}\n"

    await callback.message.answer(text)
    await callback.answer()


@router.message(F.text == "👤 Profil")
async def show_profile(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Avval ro'yxatdan o'ting. /start")
        return

    total_score = await get_user_scores(user.id)

    # Guruh reytingida o'rin aniqlash
    results = await get_rating(user.faculty, user.group_name)
    rank = "—"
    for i, (u, _) in enumerate(results, 1):
        if u.telegram_id == message.from_user.id:
            rank = f"{i}-o'rin"
            break

    registered_date = user.created_at.strftime("%d.%m.%Y") if user.created_at else "—"

    history_btn = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📜 Ishlagan testlarim tarixi", callback_data="my_test_history")]
        ]
    )

    await message.answer(
        f"👤 <b>Mening profilim</b>\n\n"
        f"📛 Ism: <b>{user.full_name}</b>\n"
        f"🏛️ Fakultet: <b>{user.faculty}</b>\n"
        f"👥 Guruh: <b>{user.group_name}</b>\n\n"
        f"🎯 Jami to'plangan ball: <b>{total_score}</b>\n"
        f"🏆 Guruh reytingida: <b>{rank}</b>\n"
        f"📅 Ro'yxatdan o'tgan: <b>{registered_date}</b>\n\n"
        "<i>Ishlagan testlaringiz va har birining to'liq javoblarini ko'rish uchun pastdagi tugmani bosing 👇</i>",
        reply_markup=history_btn
    )


@router.callback_query(F.data == "my_test_history")
async def show_test_history(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    if not user:
        await callback.answer("❌ Avval ro'yxatdan o'ting!", show_alert=True)
        return

    sessions = await get_user_completed_sessions(user.id)
    if not sessions:
        await callback.message.answer("📭 Siz hali birorta ham test ishlamagansiz.")
        await callback.answer()
        return

    btns = []
    for ts, t in sessions:
        date_str = ts.completed_at.strftime("%d.%m %H:%M") if ts.completed_at else "—"
        pct = round(ts.score / ts.total * 100) if ts.total else 0
        btns.append([
            InlineKeyboardButton(
                text=f"📋 {t.title} | {ts.score}/{ts.total} ({pct}%) | ⏱ {date_str}",
                callback_data=f"user_history_view_{ts.id}"
            )
        ])

    await callback.message.answer(
        "📜 <b>Ishlagan testlaringiz tarixi:</b>\n\n"
        "To'g'ri va xato javoblaringizni batafsil ko'rish uchun testni tanlang 👇",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("user_history_view_"))
async def view_user_history_session(callback: CallbackQuery):
    session_id = int(callback.data.split("_")[-1])

    async with async_session() as db:
        ts = await db.get(TestSession, session_id)
        if not ts:
            await callback.answer("❌ Test natijasi topilmadi!", show_alert=True)
            return

        test = await db.get(Test, ts.test_id)
        test_title = test.title if test else "Test"

        answered_count = len(ts.answers) if ts.answers else 0
        total = ts.total
        score = ts.score or 0
        wrong_count = answered_count - score
        pct = round(score / answered_count * 100) if answered_count else 0
        emoji = "🏆" if pct >= 80 else "✅" if pct >= 60 else "📊"

        items = []
        if ts.answers:
            for idx_str, user_ans in sorted(ts.answers.items(), key=lambda x: int(x[0])):
                idx = int(idx_str)
                if 0 <= idx < len(ts.questions_order):
                    q = await db.get(Question, ts.questions_order[idx])
                    if q:
                        items.append((idx + 1, q, user_ans))

    summary_header = (
        f"{emoji} <b>Test natijalari (Tarixdan):</b>\n\n"
        f"📋 Test: <b>{test_title}</b>\n"
        f"📝 Ishlangan savollar: <b>{answered_count} ta</b> (jami {total} tadan)\n"
        f"✅ To'g'ri javoblar: <b>{score} ta</b>\n"
        f"❌ Noto'g'ri javoblar: <b>{wrong_count} ta</b>\n"
        f"📊 Natija: <b>{score}/{answered_count}</b> ({pct}%)\n\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📑 <b>Ishlangan savollar va to'g'ri javoblar:</b>"
    )

    chunks = []
    current_chunk = summary_header

    for num, q, user_ans in items:
        variants = {
            "A": q.variant_a,
            "B": q.variant_b,
            "C": q.variant_c,
            "D": q.variant_d
        }
        user_var_text = variants.get(user_ans, "")
        correct_var_text = variants.get(q.correct_answer, "")
        is_correct = (user_ans == q.correct_answer)

        if is_correct:
            block = (
                f"\n\n📌 <b>{num}-savol:</b> {q.text}\n"
                f"👉 Sizning javobingiz: <b>{user_ans}) {user_var_text}</b>\n"
                f"✅ To'g'ri javob: <b>{q.correct_answer}) {correct_var_text}</b>\n"
                f"<i>Holat: To'g'ri ✅</i>"
            )
        else:
            block = (
                f"\n\n📌 <b>{num}-savol:</b> {q.text}\n"
                f"👉 Sizning javobingiz: <b>{user_ans}) {user_var_text}</b> ❌\n"
                f"✅ To'g'ri javob: <b>{q.correct_answer}) {correct_var_text}</b>\n"
                f"<i>Holat: Noto'g'ri ❌</i>"
            )

        if len(current_chunk) + len(block) > 3800:
            chunks.append(current_chunk)
            current_chunk = block
        else:
            current_chunk += block

    if current_chunk:
        chunks.append(current_chunk)

    first_markup = show_errors_keyboard(session_id) if (len(chunks) == 1 and wrong_count > 0) else None
    await callback.message.answer(chunks[0], reply_markup=first_markup)

    for i, chunk in enumerate(chunks[1:], 1):
        is_last = (i == len(chunks) - 1)
        markup = show_errors_keyboard(session_id) if (is_last and wrong_count > 0) else None
        await callback.message.answer(chunk, reply_markup=markup)

    await callback.answer()

