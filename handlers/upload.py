import os
from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from states import UploadState
from crud import get_user, create_test, save_questions, create_payment, get_pending_test, check_test_exists
from keyboards import cancel, main_menu, admin_confirm_keyboard
from parser import parse_docx, parse_txt, parse_questions
from config import ADMIN_ID, TEST_PRICE
from payment_sessions import set_pending, get_pending, clear_pending

router = Router()


@router.message(F.text == "📤 Test yuklash")
async def start_upload(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Avval ro'yxatdan o'ting. /start")
        return
    await state.clear()
    await message.answer(
        f"📤 <b>Test yuklash</b>\n\n"
        f"💰 To'lov miqdori: <b>{TEST_PRICE:,} so'm</b>\n\n"
        "📎 Test faylini yuboring (<b>.docx</b> yoki <b>.txt</b> formatda)\n\n"
        "📌 <b>Fayl formati qoidalari:</b>\n"
        "• Savollar <code>===</code> yoki bo'sh qator bilan ajratilsin\n"
        "• To'g'ri javob oldiga <code>#</code> belgisi qo'yilsin\n"
        "  Masalan: <code>#C. To'g'ri javob matni</code>\n"
        "• Kamida 5 ta savol bo'lishi kerak",
        reply_markup=cancel()
    )
    await state.set_state(UploadState.waiting_for_file)


@router.message(UploadState.waiting_for_file, F.text == "❌ Bekor qilish")
async def cancel_upload(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=main_menu())


@router.message(UploadState.waiting_for_file, F.document)
async def handle_file(message: Message, state: FSMContext, bot: Bot):
    document = message.document
    file_name = document.file_name or "test.txt"

    if not (file_name.endswith(".docx") or file_name.endswith(".txt")):
        await message.answer("❌ Faqat <b>.docx</b> yoki <b>.txt</b> fayl yuboring!")
        return

    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/{message.from_user.id}_{file_name}"

    status_msg = await message.answer("⏳ Fayl yuklanmoqda va tekshirilmoqda...")

    try:
        await bot.download(document, destination=file_path)
    except Exception as e:
        await status_msg.edit_text(f"❌ Fayl yuklab bo'lmadi: {e}")
        return

    try:
        if file_name.endswith(".docx"):
            text = parse_docx(file_path)
        else:
            text = parse_txt(file_path)
        questions = parse_questions(text)
    except Exception as e:
        await status_msg.edit_text(f"❌ Fayl o'qishda xato: {e}")
        return

    if len(questions) < 5:
        await status_msg.edit_text(
            f"❌ Faylda juda kam savol topildi: <b>{len(questions)} ta</b>\n\n"
            "Kamida <b>5 ta</b> savol bo'lishi kerak.\n"
            "Fayl formatini tekshiring va qayta yuboring."
        )
        return

    user = await get_user(message.from_user.id)
    title = file_name.rsplit(".", 1)[0]

    # Bazada mavjudligini tekshirish
    existing_test = await check_test_exists(title)
    if existing_test:
        await status_msg.delete()
        await message.answer(
            f"⚠️ Bu test allaqachon bazada mavjud!\n\n"
            f"📋 Test: <b>{existing_test.title}</b>\n"
            f"❓ Savollar: <b>{existing_test.question_count} ta</b>\n"
            f"✅ Status: <b>Tasdiqlangan</b>\n\n"
            "Bu testni '📝 Test ishlash' bo'limida topa olasiz.",
            reply_markup=main_menu()
        )
        await state.clear()
        return

    test = await create_test(
        title=title,
        price=TEST_PRICE,
        uploaded_by=user.id,
        file_path=file_path
    )
    q_count = await save_questions(test.id, questions)

    # Pending to'lovda saqlaymiz
    set_pending(
        telegram_id=message.from_user.id,
        test_id=test.id,
        user_db_id=user.id,
        title=title,
        q_count=q_count
    )

    await state.clear()

    await status_msg.edit_text(
        f"✅ <b>Fayl qabul qilindi!</b>\n\n"
        f"📋 Test: <b>{title}</b>\n"
        f"❓ Savollar soni: <b>{q_count} ta</b>\n\n"
        "⏳ Admin testingizni ko'rib, to'lov kartasini yuboradi.\n"
        "Xabar kutib turing... 🔔"
    )

    # Admin ga xabar yuborish
    try:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"🔔 <b>Yangi test yuklandi!</b>\n\n"
                f"👤 Foydalanuvchi: {user.full_name}\n"
                f"🆔 Telegram ID: <code>{message.from_user.id}</code>\n"
                f"🏛️ Fakultet: {user.faculty}\n"
                f"👥 Guruh: {user.group_name}\n\n"
                f"📋 Test nomi: <b>{title}</b>\n"
                f"❓ Savollar soni: <b>{q_count} ta</b>\n"
                f"💰 To'lov: <b>{TEST_PRICE:,} so'm</b>\n\n"
                "💳 Foydalanuvchiga karta raqamini yuborish uchun tugmani bosing:"
            ),
            reply_markup=admin_confirm_keyboard(test.id, message.from_user.id)
        )
    except Exception:
        pass


@router.message(UploadState.waiting_for_file)
async def wrong_file_type(message: Message):
    await message.answer(
        "❌ Iltimos, <b>.docx</b> yoki <b>.txt</b> formatdagi fayl yuboring!\n"
        "Yoki bekor qilish uchun tugmani bosing.",
        reply_markup=cancel()
    )


# --- To'lov skrinshoti qabul qilish ---
@router.message(F.photo)
async def handle_payment_screenshot(message: Message, bot: Bot):
    """Admin karta raqami yuborgandan keyin user skrinshot yuboradi."""
    pending = get_pending(message.from_user.id)
    if not pending:
        return  # Bu handler boshqa fotolarga aralashmaydi

    test_id = pending["test_id"]
    user_db_id = pending["user_db_id"]
    title = pending["title"]

    screenshot_file_id = message.photo[-1].file_id

    payment = await create_payment(
        user_id=user_db_id,
        test_id=test_id,
        screenshot=screenshot_file_id,
        amount=TEST_PRICE
    )

    clear_pending(message.from_user.id)

    # Admin ga skrinshot va tasdiqlash tugmasini yuborish
    try:
        await bot.send_photo(
            chat_id=ADMIN_ID,
            photo=screenshot_file_id,
            caption=(
                f"📸 <b>To'lov skrinshoti keldi!</b>\n\n"
                f"📋 Test: <b>{title}</b>\n"
                f"💰 Summa: <b>{TEST_PRICE:,} so'm</b>\n"
                f"📌 To'lov #{payment.id}"
            ),
            reply_markup=admin_confirm_keyboard(test_id, message.from_user.id)
        )
    except Exception:
        pass

    await message.answer(
        "✅ <b>To'lov skrinshoti qabul qilindi!</b>\n\n"
        "⏳ Admin tekshirib, testni tasdiqlaydi.\n"
        "Tasdiqlanganidan so'ng xabar olasiz. 🔔",
        reply_markup=main_menu()
    )
