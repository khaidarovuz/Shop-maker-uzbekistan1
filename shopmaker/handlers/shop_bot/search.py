"""
Shop bot — mahsulot qidirish handlerlari.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.queries import search_products
from keyboards.shop_kb import ShopKeyboard
from utils.helpers import format_price

logger = logging.getLogger(__name__)
router = Router()


class SearchState(StatesGroup):
    waiting_query = State()


def _get_footer(bot_data: dict) -> str:
    if bot_data.get("footer_enabled", 1):
        return "\n\n<i>Powered by @ShopMakerUzBot</i>"
    return ""


@router.message(F.text == "🔍 Qidirish")
async def shop_search_start(message: Message, bot_data: dict, state: FSMContext):
    """Qidirish rejiminii boshlaydi."""
    await state.set_state(SearchState.waiting_query)
    await message.answer(
        "🔍 <b>Mahsulot qidirish</b>\n\n"
        "Qidirmoqchi bo'lgan mahsulot nomini kiriting:",
        reply_markup=ShopKeyboard.cancel()
    )


@router.message(SearchState.waiting_query)
async def shop_search_query(message: Message, bot_id: int, bot_data: dict, state: FSMContext):
    """Qidiruv so'rovini bajaradi."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        is_admin = message.from_user.id == bot_data.get("owner_id")
        await message.answer("❌ Qidirish bekor qilindi.", reply_markup=ShopKeyboard.main_menu(is_admin=is_admin))
        return

    query = message.text.strip()
    if len(query) < 2:
        await message.answer("❌ Kamida 2 ta harf kiriting:")
        return

    await state.clear()
    results = await search_products(bot_id, query)
    footer = _get_footer(bot_data)
    is_admin = message.from_user.id == bot_data.get("owner_id")

    if not results:
        await message.answer(
            f"🔍 «{query}» bo'yicha hech narsa topilmadi." + footer,
            reply_markup=ShopKeyboard.main_menu(is_admin=is_admin)
        )
        return

    text = f"🔍 «{query}» bo'yicha topildi: {len(results)} ta mahsulot\n\n"
    for prod in results[:10]:
        text += f"• <b>{prod['name']}</b> — {format_price(prod['price'])}\n"
        if prod["description"]:
            desc = prod["description"][:60] + "..." if len(prod["description"]) > 60 else prod["description"]
            text += f"  <i>{desc}</i>\n"
        text += "\n"

    if len(results) > 10:
        text += f"... va yana {len(results) - 10} ta\n"

    text += footer
    await message.answer(text, reply_markup=ShopKeyboard.main_menu(is_admin=is_admin))
