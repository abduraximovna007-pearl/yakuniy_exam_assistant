from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from states import RegisterState
from crud import get_user, create_user
from keyboards import main_menu, admin_menu
from config import ADMIN_ID, is_admin

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = await get_user(message.from_user.id)

    # Agar foydalanuvchi Admin bo'lsa — faqat Admin Panel chiqadi!
    is_admin_flag = is_admin(message.from_user.id) or (user and (user.role == "admin" or "durdona" in user.full_name.lower()))
    if is_admin_flag:
        admin_name = user.full_name if user else "Admin"
        await message.answer(
            f"👋 Assalomu alaykum, <b>{admin_name}</b> (Boshqaruvchi)!\n\n"
            "👨‍💼 <b>Admin boshqaruv paneli</b>\n"
            "Quyidagi menyudan kerakli bo'limni tanlang 👇",
            reply_markup=admin_menu()
        )
        return

    if user:
        await message.answer(
            f"👋 Xush kelibsiz, <b>{user.full_name}</b>!\n"
            f"🏛️ Fakultet: {user.faculty}\n"
            f"👥 Guruh: {user.group_name}\n\n"
            "Quyidagi menyudan birini tanlang:",
            reply_markup=main_menu()
        )
    else:
        await message.answer(
            "👋 Salom! Botga xush kelibsiz!\n\n"
            "Davom etish uchun avval ro'yxatdan o'ting.\n"
            "To'liq ismingizni kiriting (Familiya Ism):"
        )
        await state.set_state(RegisterState.full_name)


@router.message(RegisterState.full_name)
async def get_full_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 3:
        await message.answer("❌ Ism juda qisqa. Iltimos, to'liq ismingizni kiriting (masalan: Aliyev Ali):")
        return
    await state.update_data(full_name=name)
    await message.answer(f"✅ Ism saqlandi: <b>{name}</b>\n\n🏛️ Fakultetingizni kiriting:")
    await state.set_state(RegisterState.faculty)


@router.message(RegisterState.faculty)
async def get_faculty(message: Message, state: FSMContext):
    faculty = message.text.strip()
    if len(faculty) < 2:
        await message.answer("❌ Fakultet nomi juda qisqa. Iltimos, qayta kiriting:")
        return
    await state.update_data(faculty=faculty)
    await message.answer(f"✅ Fakultet: <b>{faculty}</b>\n\n👥 Guruhingizni kiriting (masalan: 22-01):")
    await state.set_state(RegisterState.group_name)


@router.message(RegisterState.group_name)
async def get_group(message: Message, state: FSMContext):
    group = message.text.strip()
    if len(group) < 2:
        await message.answer("❌ Guruh nomi juda qisqa. Iltimos, qayta kiriting:")
        return
    data = await state.get_data()
    user = await create_user(
        telegram_id=message.from_user.id,
        full_name=data["full_name"],
        faculty=data["faculty"],
        group_name=group
    )
    await state.clear()
    is_admin = (message.from_user.id == ADMIN_ID)
    await message.answer(
        f"🎉 Ro'yxatdan muvaffaqiyatli o'tdingiz!\n\n"
        f"👤 Ism: <b>{user.full_name}</b>\n"
        f"🏛️ Fakultet: <b>{user.faculty}</b>\n"
        f"👥 Guruh: <b>{user.group_name}</b>\n\n"
        "Endi testlardan foydalanishingiz mumkin! ⬇️",
        reply_markup=main_menu(is_admin=is_admin)
    )
