from aiogram import Router, F
from aiogram.types import Message
from crud import get_user, get_rating, get_user_scores
from keyboards import main_menu

router = Router()


@router.message(F.text == "🏆 Reyting")
async def show_rating(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Avval ro'yxatdan o'ting. /start")
        return

    results = await get_rating(user.faculty, user.group_name)

    if not results:
        await message.answer(
            f"📊 <b>{user.faculty} — {user.group_name}</b>\n\n"
            "Hozircha reyting ma'lumoti yo'q.\n"
            "Test ishlaganingizdan so'ng reyting paydo bo'ladi."
        )
        return

    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    text = f"🏆 <b>Reyting: {user.faculty} — {user.group_name}</b>\n\n"

    for i, (u, score) in enumerate(results, 1):
        medal = medals.get(i, f"{i}.")
        you = " 👈 <b>Sen</b>" if u.telegram_id == message.from_user.id else ""
        text += f"{medal} {u.full_name} — <b>{score or 0}</b> ball{you}\n"

    await message.answer(text)


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

    await message.answer(
        f"👤 <b>Mening profilim</b>\n\n"
        f"📛 Ism: <b>{user.full_name}</b>\n"
        f"🏛️ Fakultet: <b>{user.faculty}</b>\n"
        f"👥 Guruh: <b>{user.group_name}</b>\n\n"
        f"🎯 Jami to'plangan ball: <b>{total_score}</b>\n"
        f"🏆 Guruh reytingida: <b>{rank}</b>\n"
        f"📅 Ro'yxatdan o'tgan: <b>{registered_date}</b>"
    )
