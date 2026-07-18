"""
Shop bot — foydalanuvchi buyurtmalari handlerlari.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from database.queries import get_user_orders, get_order
from keyboards.shop_kb import ShopKeyboard
from utils.helpers import build_order_text, format_price

logger = logging.getLogger(__name__)
router = Router()


def _get_footer(bot_data: dict) -> str:
    if bot_data.get("footer_enabled", 1):
        return "\n\n<i>Powered by @ShopMakerUzBot</i>"
    return ""


@router.message(F.text == "📋 Buyurtmalarim")
async def my_orders(message: Message, bot_id: int, bot_data: dict):
    """Foydalanuvchi buyurtmalarini ko'rsatadi."""
    orders = await get_user_orders(bot_id, message.from_user.id)
    footer = _get_footer(bot_data)
    is_admin = message.from_user.id == bot_data.get("owner_id")

    if not orders:
        await message.answer(
            "📋 Sizda hali buyurtmalar yo'q.\n\n"
            "🛍 Mahsulotlar bo'limiga o'ting va buyurtma bering!" + footer,
            reply_markup=ShopKeyboard.main_menu(is_admin=is_admin)
        )
        return

    await message.answer(
        f"📋 <b>Buyurtmalarim</b> ({len(orders)} ta)\n\nBuyurtmani ko'rish uchun bosing:",
        reply_markup=ShopKeyboard.my_orders(orders)
    )


@router.callback_query(F.data.startswith("my_order:"))
async def my_order_detail(call: CallbackQuery, bot_id: int, bot_data: dict):
    """Buyurtma tafsilotlarini ko'rsatadi."""
    order_id = int(call.data.split(":")[1])
    order = await get_order(order_id)

    if not order or order["customer_id"] != call.from_user.id:
        await call.answer("❌ Buyurtma topilmadi.", show_alert=True)
        return

    footer = _get_footer(bot_data)
    text = build_order_text(order) + footer
    await call.message.answer(text)
    await call.answer()
