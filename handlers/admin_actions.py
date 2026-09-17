from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from crud import approve_test, reject_test, get_pending_test
from config import ADMIN_ID, TEST_PRICE
from database import async_session
from models import Question
from sqlalchemy import select, func
from states import AdminCardState

router = Router()


async def _count_questions(test_id: int) -> int:
    async with async_session() as db:
        count = await db.scalar(
            select(func.count(Question.id)).where(Question.test_id == test_id)
        )
        return count or 0


# ── Karta raqami yuborish ──────────────────────────────────────────────────

@router.callback_query(F.data.startswith("send_card_"))
async def request_card_number(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
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
    if message.from_user.id != ADMIN_ID:
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
    if callback.from_user.id != ADMIN_ID:
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
    if callback.from_user.id != ADMIN_ID:
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
