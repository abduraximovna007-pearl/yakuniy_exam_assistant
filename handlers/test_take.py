from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from states import TestState
from crud import (
    get_user, get_approved_tests, get_test_questions,
    create_session, update_session_answer, complete_session, get_pending_test
)
from keyboards import start_test_keyboard, answer_keyboard, show_errors_keyboard, main_menu
from ai_helper import explain_wrong_answer
from database import async_session
from models import TestSession, Question

router = Router()


def format_question_text(q_num: int, total: int, q_text: str, variants: dict, is_start: bool = False) -> str:
    prefix = "🎯 <b>Test boshlandi! Omad! 💪</b>\n\n" if is_start else ""
    vars_lines = []
    for letter in ["A", "B", "C", "D"]:
        if letter in variants and variants[letter]:
            vars_lines.append(f"<b>{letter})</b> {variants[letter]}")
    variants_block = "\n\n".join(vars_lines)
    return (
        f"{prefix}📌 <b>Savol {q_num} / {total}:</b>\n\n"
        f"<b>{q_text}</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"<b>Variantlar:</b>\n\n"
        f"{variants_block}\n\n"
        f"<i>To'g'ri javobni tanlash uchun pastdagi mos harfni bosing 👇</i>"
    )


@router.message(F.text == "📝 Test ishlash")
async def show_tests(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Avval ro'yxatdan o'ting. /start")
        return

    tests = await get_approved_tests()
    if not tests:
        await message.answer(
            "📭 Hozircha tasdiqlangan testlar mavjud emas.\n\n"
            "📤 '📤 Test yuklash' tugmasi orqali test yuklab, "
            "to'lov qilsangiz, admin tasdiqlaydi."
        )
        return

    btns = []
    for t in tests:
        btns.append([InlineKeyboardButton(
            text=f"📋 {t.title}  ({t.question_count} ta savol)",
            callback_data=f"select_test_{t.id}"
        )])

    await message.answer(
        "📚 <b>Mavjud testlar:</b>\n\nBitta testni tanlang 👇",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )


@router.callback_query(F.data.startswith("select_test_"))
async def select_test(callback: CallbackQuery):
    test_id = int(callback.data.split("_")[-1])
    test = await get_pending_test(test_id)
    if not test:
        await callback.answer("❌ Test topilmadi!", show_alert=True)
        return

    await callback.message.edit_text(
        f"📋 <b>{test.title}</b>\n\n"
        f"❓ Jami savollar: <b>{test.question_count} ta</b>\n"
        f"🎯 Test 25 ta random savol beradi\n\n"
        "Testni boshlashga tayyormisiz?",
        reply_markup=start_test_keyboard(test_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("start_test_"))
async def start_test(callback: CallbackQuery, state: FSMContext):
    test_id = int(callback.data.split("_")[-1])
    user = await get_user(callback.from_user.id)
    if not user:
        await callback.answer("❌ Avval ro'yxatdan o'ting!", show_alert=True)
        return

    questions = await get_test_questions(test_id, count=25)
    if not questions:
        await callback.answer("❌ Testda savollar topilmadi!", show_alert=True)
        return

    questions_order = [q.id for q in questions]
    session = await create_session(user.id, test_id, questions_order)

    await state.set_state(TestState.answering)
    await state.update_data(session_id=session.id)

    q = questions[0]
    variants = {
        "A": q.variant_a,
        "B": q.variant_b,
        "C": q.variant_c,
        "D": q.variant_d
    }

    await callback.message.edit_text(
        format_question_text(1, len(questions_order), q.text, variants, is_start=True),
        reply_markup=answer_keyboard(session.id, 0, variants)
    )
    await callback.answer("✅ Test boshlandi!")


@router.callback_query(TestState.answering, F.data.startswith("answer_"))
async def handle_answer(callback: CallbackQuery, state: FSMContext):
    # Format: answer_{session_id}_{q_index}_{letter}
    parts = callback.data.split("_")
    session_id = int(parts[1])
    q_index = int(parts[2])
    letter = parts[3]

    await update_session_answer(session_id, q_index, letter)

    async with async_session() as db:
        ts = await db.get(TestSession, session_id)
        if not ts:
            await callback.answer("❌ Sessiya topilmadi!")
            return

        total = ts.total
        next_index = q_index + 1

        # All questions answered — auto finish
        if next_index >= total:
            score, total_q = await complete_session(session_id)
            await state.clear()
            pct = round(score / total_q * 100) if total_q else 0
            emoji = "🏆" if pct >= 80 else "✅" if pct >= 60 else "📊"
            await callback.message.edit_text(
                f"{emoji} <b>Test yakunlandi!</b>\n\n"
                f"✅ To'g'ri: <b>{score}</b>\n"
                f"❌ Xato: <b>{total_q - score}</b>\n"
                f"📊 Natija: <b>{score}/{total_q}</b> ({pct}%)\n\n"
                "Xatolaringizni ko'rish uchun quyidagi tugmani bosing 👇",
                reply_markup=show_errors_keyboard(session_id)
            )
            await callback.answer("🏁 Test yakunlandi!")
            return

        # Show next question
        q_id = ts.questions_order[next_index]
        q = await db.get(Question, q_id)
        if not q:
            await callback.answer("❌ Savol topilmadi!")
            return

        variants = {
            "A": q.variant_a,
            "B": q.variant_b,
            "C": q.variant_c,
            "D": q.variant_d
        }

        answered = len(ts.answers) + 1  # Current count after this answer
        await callback.message.edit_text(
            format_question_text(next_index + 1, total, q.text, variants),
            reply_markup=answer_keyboard(session_id, next_index, variants)
        )
        await callback.answer(f"✅ Javob qabul qilindi ({answered}/{total})")


@router.callback_query(F.data.startswith("stop_test_"))
async def stop_test(callback: CallbackQuery, state: FSMContext):
    session_id = int(callback.data.split("_")[-1])
    score, total = await complete_session(session_id)
    await state.clear()

    if total == 0:
        await callback.message.edit_text("❌ Test ma'lumotlari topilmadi.")
        return

    pct = round(score / total * 100) if total else 0
    emoji = "🏆" if pct >= 80 else "✅" if pct >= 60 else "📊"

    await callback.message.edit_text(
        f"{emoji} <b>Test yakunlandi!</b>\n\n"
        f"✅ To'g'ri: <b>{score}</b>\n"
        f"❌ Xato: <b>{total - score}</b>\n"
        f"📊 Natija: <b>{score}/{total}</b> ({pct}%)\n\n"
        "Xatolaringizni ko'rish uchun quyidagi tugmani bosing 👇",
        reply_markup=show_errors_keyboard(session_id)
    )
    await callback.answer("🏁 Test yakunlandi!")


@router.callback_query(F.data.startswith("errors_"))
async def show_errors(callback: CallbackQuery):
    session_id = int(callback.data.split("_")[-1])

    await callback.message.edit_text(
        "⏳ Xatolar tahlil qilinmoqda...\n"
        "🤖 AI tushuntirish tayyorlanmoqda (bir oz kuting)..."
    )
    await callback.answer()

    async with async_session() as db:
        ts = await db.get(TestSession, session_id)
        if not ts:
            await callback.message.edit_text("❌ Sessiya ma'lumoti topilmadi.")
            return

        if not ts.answers:
            await callback.message.edit_text(
                "📋 Birorta savolga javob bermagansiz."
            )
            return

        # Find wrong answers
        wrong_answers = []
        for idx_str, user_ans in ts.answers.items():
            idx = int(idx_str)
            if 0 <= idx < len(ts.questions_order):
                q = await db.get(Question, ts.questions_order[idx])
                if q and user_ans != q.correct_answer:
                    wrong_answers.append((q, user_ans))

    if not wrong_answers:
        await callback.message.edit_text(
            "🎉 <b>Ajoyib!</b> Barcha savollarga to'g'ri javob berdingiz!\n"
            "Xato yo'q! 🏆"
        )
        return

    header = (
        f"📋 <b>Xatolar tahlili</b> — {len(wrong_answers)} ta xato\n"
        f"🤖 Har bir xato uchun AI tushuntirish berilgan\n"
    )
    await callback.message.edit_text(header + "\n⏳ Tushuntirishlar yuklanmoqda...")

    # Process each wrong answer with AI explanation
    messages_to_send = []
    current_chunk = header

    for i, (q, user_ans) in enumerate(wrong_answers, 1):
        variants = {
            "A": q.variant_a,
            "B": q.variant_b,
            "C": q.variant_c,
            "D": q.variant_d
        }

        # Get AI explanation from Gemini
        try:
            explanation = await explain_wrong_answer(
                question_text=q.text,
                variants=variants,
                user_answer=user_ans,
                correct_answer=q.correct_answer
            )
        except Exception:
            explanation = "Tushuntirish yuklanmadi"

        block = (
            f"\n━━━━━━━━━━━━━━━━━━━\n"
            f"<b>❌ Xato {i}:</b>\n"
            f"{q.text}\n\n"
            f"Siz tanladingiz: <b>{user_ans}</b>) {variants.get(user_ans, '')}\n"
            f"✅ To'g'ri javob: <b>{q.correct_answer}</b>) {variants.get(q.correct_answer, '')}\n\n"
            f"🤖 <b>AI tushuntirish:</b>\n"
            f"<i>{explanation}</i>\n"
        )

        # Telegram 4096 char limit — split into chunks
        if len(current_chunk) + len(block) > 3800:
            messages_to_send.append(current_chunk)
            current_chunk = block
        else:
            current_chunk += block

    current_chunk += "\n━━━━━━━━━━━━━━━━━━━"
    messages_to_send.append(current_chunk)

    # Send all chunks
    await callback.message.delete()
    for chunk in messages_to_send:
        await callback.message.answer(chunk)
