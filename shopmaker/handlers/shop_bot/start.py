"""
Shop bot — /start va asosiy menyu handlerlari.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from config import config
from keyboards.shop_kb import ShopKeyboard

logger = logging.getLogger(__name__)
router = Router()


def _is_admin(user_id: int, bot_data: dict) -> bool:
    """Foydalanuvchi shop admini ekanligini tekshiradi."""
    return user_id == bot_data.get("owner_id")


def _get_footer(bot_data: dict) -> str:
    """Footer matnini qaytaradi."""
    if bot_data.get("footer_enabled", 1):
        return "\n\n<i>Powered by @ShopMakerUzBot</i>"
    return ""


@router.message(CommandStart())
async def shop_start(
    message: Message,
    bot_id: int,
    bot_data: dict,
    shop_user: dict,
    state: FSMContext
):
    """Shop bot /start komandasi."""
    await state.clear()

    is_admin = _is_admin(message.from_user.id, bot_data)
    bot_name = bot_data.get("bot_name", "Do'konim")

    # Xush kelibsiz matn
    welcome = bot_data.get("welcome_text") or (
        f"🛍 <b>{bot_name}</b> ga xush kelibsiz!\n\n"
        f"Bu yerda siz mahsulotlarimizni ko'rib, buyurtma berishingiz mumkin."
    )

    footer = _get_footer(bot_data)
    await message.answer(
        welcome + footer,
        reply_markup=ShopKeyboard.main_menu(is_admin=is_admin)
    )


@router.message(F.text == "🏠 Asosiy menyu")
async def shop_main_menu(
    message: Message,
    bot_id: int,
    bot_data: dict,
    state: FSMContext
):
    """Asosiy menyuga qaytish."""
    await state.clear()
    is_admin = _is_admin(message.from_user.id, bot_data)
    await message.answer(
        "🏠 Asosiy menyu",
        reply_markup=ShopKeyboard.main_menu(is_admin=is_admin)
    )


@router.message(F.text == "ℹ️ Bot haqida")
async def shop_about(message: Message, bot_data: dict):
    """Bot haqida ma'lumot."""
    bot_name = bot_data.get("bot_name", "Do'konim")
    about = bot_data.get("about_text") or (
        f"🛍 <b>{bot_name}</b>\n\n"
        "Bu Telegram do'koni bot orqali qulay xarid qilishingiz mumkin.\n\n"
        "✅ Mahsulotlarni ko'ring\n"
        "✅ Savatga qo'shing\n"
        "✅ Buyurtma bering"
    )
    footer = _get_footer(bot_data)
    await message.answer(about + footer)


@router.message(F.text == "📞 Admin bilan bog'lanish")
async def shop_contact(message: Message, bot_data: dict):
    """Admin bilan bog'lanish."""
    contact = bot_data.get("contact_info")
    footer = _get_footer(bot_data)

    if contact:
        text = f"📞 <b>Aloqa</b>\n\n{contact}"
    else:
        # Owner ga forward qiladi
        owner_id = bot_data.get("owner_id")
        text = (
            f"📞 <b>Admin bilan bog'lanish</b>\n\n"
            f"Savollaringizni quyida yozing, admin ko'radi."
        )

    await message.answer(text + footer)
