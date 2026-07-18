"""
Asosiy bot — /start, yordam, sozlamalar handlerlari.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import config, texts
from database.queries import get_user, get_setting, add_log, get_bot_stats
from keyboards.main_kb import MainKeyboard
from utils.helpers import get_plan_label, format_date

logger = logging.getLogger(__name__)
router = Router()


class SettingsState(StatesGroup):
    """Sozlamalar holatlari."""
    waiting_for_language = State()


# ── /start ──────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, user_data: dict, is_new_user: bool, state: FSMContext):
    """Botni boshlash."""
    await state.clear()

    # Ro'yxatdan o'tish yoqilgan ekanligini tekshiradi
    reg_enabled = await get_setting("registration_enabled", "1")
    if is_new_user and reg_enabled != "1":
        await message.answer(
            "❌ Hozirda ro'yxatdan o'tish mavjud emas.\n"
            "Iltimos, keyinroq urinib ko'ring."
        )
        return

    is_admin = config.is_super_admin(message.from_user.id)

    if is_new_user:
        await message.answer(
            f"👋 Xush kelibsiz, <b>{message.from_user.first_name}</b>!\n\n"
            f"🤖 <b>ShopMakerUzBot</b> — o'z do'kon botingizni yarating!\n\n"
            f"Bu bot yordamida siz:\n"
            f"✅ @BotFather orqali bot yaratasiz\n"
            f"✅ Token orqali shop sistemasini ulaysiz\n"
            f"✅ Mahsulotlar, kategoriyalar, buyurtmalar boshqarasiz\n\n"
            f"Boshlash uchun quyidagi menyudan foydalaning 👇",
            reply_markup=MainKeyboard.main_menu(is_admin=is_admin)
        )
        await add_log("new_user_registered", user_id=message.from_user.id)
    else:
        plan = get_plan_label(user_data.get("plan", "free"))
        await message.answer(
            f"👋 Xush kelibsiz, <b>{message.from_user.first_name}</b>!\n"
            f"📦 Reja: {plan}",
            reply_markup=MainKeyboard.main_menu(is_admin=is_admin)
        )


@router.message(F.text == "❓ Yordam")
async def cmd_help(message: Message):
    """Yordam."""
    await message.answer(
        "❓ <b>Yordam</b>\n\n"
        "ShopMakerUzBot — o'z do'kon botingizni yarating!\n\n"
        "<b>Qanday ishlaydi?</b>\n"
        "1️⃣ @BotFather dan yangi bot yaratasiz\n"
        "2️⃣ Bot tokenini olasiz\n"
        "3️⃣ «➕ Bot qo'shish» tugmasini bosasiz\n"
        "4️⃣ Tokenni yuborasiz\n"
        "5️⃣ Botingiz darhol ishlay boshlaydi! ✅\n\n"
        "<b>Rejalar:</b>\n"
        "🆓 Bepul — 1 ta bot, barcha asosiy funksiyalar\n"
        "🌟 Comfort — 5 000 so'm/3 oy, kengaytirilgan\n"
        "💎 Premium — 10 000 so'm/30 kun, barcha funksiyalar\n\n"
        "📞 Muammo yuzasida: @ShopMakerUzBot"
    )


@router.message(F.text == "⚙️ Sozlamalar")
async def cmd_settings(message: Message, user_data: dict, state: FSMContext):
    """Foydalanuvchi sozlamalari."""
    await state.clear()
    plan = get_plan_label(user_data.get("plan", "free"))
    expires = format_date(user_data.get("plan_expires_at"))

    text = (
        f"⚙️ <b>Sozlamalar</b>\n\n"
        f"👤 Ismi: <b>{user_data.get('full_name', '—')}</b>\n"
        f"🆔 ID: <code>{user_data.get('id', '—')}</code>\n"
        f"📦 Reja: <b>{plan}</b>\n"
    )
    if user_data.get("plan") != "free":
        text += f"📅 Tugash sanasi: <b>{expires}</b>\n"

    await message.answer(text)


@router.message(F.text == "📊 Statistika")
async def cmd_statistics(message: Message, user_data: dict):
    """Foydalanuvchi statistikasi."""
    from database.queries import get_user_bots, count_orders, count_shop_users

    bots = await get_user_bots(message.from_user.id)

    if not bots:
        await message.answer(
            "📊 <b>Statistika</b>\n\n"
            "Sizda hali bot mavjud emas.\n"
            "«➕ Bot qo'shish» tugmasidan boshlang."
        )
        return

    text = f"📊 <b>Statistika</b>\n\n"
    for bot in bots:
        stats = await get_bot_stats(bot["id"])
        text += (
            f"🤖 <b>@{bot['bot_username'] or bot['bot_name']}</b>\n"
            f"  👥 Xaridorlar: {stats['total_users']}\n"
            f"  📦 Mahsulotlar: {stats['total_products']}\n"
            f"  📋 Buyurtmalar: {stats['total_orders']}\n"
            f"  🆕 Yangi buyurtmalar: {stats['new_orders']}\n"
            f"  💰 Daromad: {stats['revenue']:,.0f} so'm\n\n"
        )

    await message.answer(text)
