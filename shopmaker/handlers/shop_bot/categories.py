"""
Shop bot — kategoriyalar handlerlari.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from database.queries import get_categories, get_products
from keyboards.shop_kb import ShopKeyboard

logger = logging.getLogger(__name__)
router = Router()


def _get_footer(bot_data: dict) -> str:
    if bot_data.get("footer_enabled", 1):
        return "\n\n<i>Powered by @ShopMakerUzBot</i>"
    return ""


@router.message(F.text == "📂 Kategoriyalar")
async def shop_categories(message: Message, bot_id: int, bot_data: dict):
    """Kategoriyalar ro'yxatini ko'rsatadi."""
    cats = await get_categories(bot_id)
    footer = _get_footer(bot_data)

    if not cats:
        await message.answer("📂 Kategoriyalar hali yo'q." + footer)
        return

    await message.answer(
        "📂 <b>Kategoriyalar</b>\n\nKategoriyani tanlang:" + footer,
        reply_markup=ShopKeyboard.categories_inline(cats)
    )
