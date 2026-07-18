"""
Shop bot — mahsulotlar ro'yxati va ko'rish handlerlari.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.queries import get_products, get_product, get_categories, get_cart, add_to_cart, set_cart_qty
from keyboards.shop_kb import ShopKeyboard
from utils.helpers import format_price, paginate

logger = logging.getLogger(__name__)
router = Router()


def _get_footer(bot_data: dict) -> str:
    if bot_data.get("footer_enabled", 1):
        return "\n\n<i>Powered by @ShopMakerUzBot</i>"
    return ""


async def _get_cart_qty(bot_id: int, user_id: int, product_id: int) -> int:
    """Savatdagi mahsulot miqdorini qaytaradi."""
    cart = await get_cart(bot_id, user_id)
    for item in cart:
        if item["product_id"] == product_id:
            return item["quantity"]
    return 0


# ── Mahsulotlar ro'yxati ─────────────────────────────────────────────────────

@router.message(F.text == "🛍 Mahsulotlar")
async def shop_products(message: Message, bot_id: int, bot_data: dict, state: FSMContext):
    """Barcha mahsulotlarni ko'rsatadi."""
    await state.clear()
    cats = await get_categories(bot_id)

    if cats:
        footer = _get_footer(bot_data)
        await message.answer(
            "📂 Kategoriyani tanlang:" + footer,
            reply_markup=ShopKeyboard.categories_inline(cats)
        )
    else:
        products = await get_products(bot_id)
        if not products:
            await message.answer("📦 Hozircha mahsulotlar yo'q.")
            return
        await state.update_data(products=products, page=1)
        await _show_product(message, products, 1, bot_id, bot_data)


@router.callback_query(F.data.startswith("shop_cat:"))
async def shop_cat_cb(call: CallbackQuery, bot_id: int, bot_data: dict, state: FSMContext):
    """Kategoriya bo'yicha mahsulotlar."""
    cat_id = call.data.split(":")[1]

    if cat_id == "all":
        products = await get_products(bot_id)
    else:
        products = await get_products(bot_id, category_id=int(cat_id))

    if not products:
        await call.answer("📦 Bu kategoriyada mahsulotlar yo'q.", show_alert=True)
        return

    await state.update_data(products=products, page=1)
    await call.message.delete()
    await _show_product(call.message, products, 1, bot_id, bot_data)
    await call.answer()


@router.callback_query(F.data.startswith("shop_prod:"))
async def shop_prod_page_cb(call: CallbackQuery, bot_id: int, bot_data: dict, state: FSMContext):
    """Mahsulot sahifasini o'zgartiradi."""
    page = int(call.data.split(":")[1])
    data = await state.get_data()
    products = data.get("products", [])

    if not products:
        products = await get_products(bot_id)
        await state.update_data(products=products)

    if not products:
        await call.answer("Mahsulotlar yo'q.", show_alert=True)
        return

    try:
        await call.message.delete()
    except Exception:
        pass
    await _show_product(call.message, products, page, bot_id, bot_data)
    await call.answer()


@router.callback_query(F.data == "shop_products_back")
async def shop_products_back_cb(call: CallbackQuery, bot_id: int, bot_data: dict, state: FSMContext):
    """Mahsulotlar ro'yxatiga qaytish."""
    cats = await get_categories(bot_id)
    footer = _get_footer(bot_data)
    if cats:
        try:
            await call.message.edit_text(
                "📂 Kategoriyani tanlang:" + footer,
                reply_markup=ShopKeyboard.categories_inline(cats)
            )
        except Exception:
            await call.message.answer(
                "📂 Kategoriyani tanlang:" + footer,
                reply_markup=ShopKeyboard.categories_inline(cats)
            )
    else:
        products = await get_products(bot_id)
        if products:
            await state.update_data(products=products)
            try:
                await call.message.delete()
            except Exception:
                pass
            await _show_product(call.message, products, 1, bot_id, bot_data)
    await call.answer()


async def _show_product(
    message: Message,
    products: list,
    page: int,
    bot_id: int,
    bot_data: dict
):
    """Bir mahsulotni ko'rsatadi."""
    total = len(products)
    if page < 1:
        page = 1
    if page > total:
        page = total

    prod = products[page - 1]
    in_cart = await _get_cart_qty(bot_id, message.chat.id, prod["id"])
    footer = _get_footer(bot_data)

    text = (
        f"📦 <b>{prod['name']}</b>\n\n"
        f"💰 Narx: <b>{format_price(prod['price'])}</b>\n"
    )
    if prod.get("description"):
        text += f"\n📄 {prod['description']}"
    text += footer

    kb = ShopKeyboard.product_page(prod["id"], page, total, in_cart)

    if prod.get("photo_id"):
        await message.answer_photo(
            prod["photo_id"],
            caption=text,
            reply_markup=kb
        )
    else:
        await message.answer(text, reply_markup=kb)


# ── Savatga qo'shish ─────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("cart_add:"))
async def cart_add_cb(call: CallbackQuery, bot_id: int, bot_data: dict):
    """Savatga mahsulot qo'shadi."""
    product_id = int(call.data.split(":")[1])
    prod = await get_product(product_id)

    if not prod or not prod["is_available"]:
        await call.answer("❌ Mahsulot mavjud emas.", show_alert=True)
        return

    await add_to_cart(bot_id, call.from_user.id, product_id, 1)
    in_cart = await _get_cart_qty(bot_id, call.from_user.id, product_id)
    await call.answer("✅ Savatga qo'shildi!", show_alert=False)

    try:
        # Sahifani topib olamiz: state dan emas, joriy mahsulot id bo'yicha
        data_parts = call.message.caption or call.message.text or ""
        kb = ShopKeyboard.product_page(product_id, 1, 1, in_cart)
        if call.message.photo:
            await call.message.edit_caption(
                caption=call.message.caption,
                reply_markup=kb
            )
        else:
            await call.message.edit_reply_markup(reply_markup=kb)
    except Exception:
        pass


@router.callback_query(F.data.startswith("cart_inc:"))
async def cart_inc_cb(call: CallbackQuery, bot_id: int):
    """Savatda mahsulot miqdorini oshiradi."""
    product_id = int(call.data.split(":")[1])
    in_cart = await _get_cart_qty(bot_id, call.from_user.id, product_id)
    new_qty = in_cart + 1

    await set_cart_qty(bot_id, call.from_user.id, product_id, new_qty)
    await call.answer(f"🛒 {new_qty} ta")

    try:
        kb = ShopKeyboard.product_page(product_id, 1, 1, new_qty)
        if call.message.photo:
            await call.message.edit_caption(caption=call.message.caption, reply_markup=kb)
        else:
            await call.message.edit_reply_markup(reply_markup=kb)
    except Exception:
        pass


@router.callback_query(F.data.startswith("cart_dec:"))
async def cart_dec_cb(call: CallbackQuery, bot_id: int):
    """Savatda mahsulot miqdorini kamaytiradi."""
    product_id = int(call.data.split(":")[1])
    in_cart = await _get_cart_qty(bot_id, call.from_user.id, product_id)
    new_qty = max(0, in_cart - 1)

    await set_cart_qty(bot_id, call.from_user.id, product_id, new_qty)

    if new_qty == 0:
        await call.answer("🗑 Savatdan olib tashlandi")
    else:
        await call.answer(f"🛒 {new_qty} ta")

    try:
        kb = ShopKeyboard.product_page(product_id, 1, 1, new_qty)
        if call.message.photo:
            await call.message.edit_caption(caption=call.message.caption, reply_markup=kb)
        else:
            await call.message.edit_reply_markup(reply_markup=kb)
    except Exception:
        pass


@router.callback_query(F.data.startswith("cart_count:"))
async def cart_count_cb(call: CallbackQuery, bot_id: int):
    """Savatdagi miqdorni ko'rsatadi."""
    product_id = int(call.data.split(":")[1])
    in_cart = await _get_cart_qty(bot_id, call.from_user.id, product_id)
    await call.answer(f"Savatda: {in_cart} ta", show_alert=True)


@router.callback_query(F.data == "noop")
async def noop_cb(call: CallbackQuery):
    """Hech narsa qilmaydi (sahifa ko'rsatkichi uchun)."""
    await call.answer()
