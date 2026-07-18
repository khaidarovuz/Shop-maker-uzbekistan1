"""
Shop bot — savat va buyurtma handlerlari.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.queries import (
    get_cart, clear_cart, create_order, get_bot,
    get_or_create_shop_user, set_shop_user_phone, get_shop_user
)
from keyboards.shop_kb import ShopKeyboard
from utils.helpers import format_price
from utils.bot_manager import send_to_shop_bot

logger = logging.getLogger(__name__)
router = Router()


class CheckoutState(StatesGroup):
    phone = State()
    address = State()
    note = State()
    confirm = State()


def _get_footer(bot_data: dict) -> str:
    if bot_data.get("footer_enabled", 1):
        return "\n\n<i>Powered by @ShopMakerUzBot</i>"
    return ""


async def _build_cart_text(cart: list, footer: str = "") -> str:
    """Savat matnini yaratadi."""
    if not cart:
        return "🛒 Savat bo'm-bo'sh." + footer

    text = "🛒 <b>Savatingiz:</b>\n\n"
    total = 0
    for item in cart:
        subtotal = item["price"] * item["quantity"]
        total += subtotal
        text += (
            f"• {item['name']}\n"
            f"  {format_price(item['price'])} × {item['quantity']} = {format_price(subtotal)}\n"
        )
    text += f"\n💰 <b>Jami: {format_price(total)}</b>"
    text += footer
    return text


# ── Savat ko'rish ─────────────────────────────────────────────────────────────

@router.message(F.text == "🛒 Savat")
async def shop_cart(message: Message, bot_id: int, bot_data: dict, state: FSMContext):
    """Savatni ko'rsatadi."""
    await state.clear()
    cart = await get_cart(bot_id, message.from_user.id)
    footer = _get_footer(bot_data)

    if not cart:
        is_admin = message.from_user.id == bot_data.get("owner_id")
        await message.answer(
            "🛒 Savat bo'm-bo'sh.\n\n🛍 Mahsulotlar bo'limiga o'ting." + footer,
            reply_markup=ShopKeyboard.main_menu(is_admin=is_admin)
        )
        return

    text = await _build_cart_text(cart, footer)
    await message.answer(text, reply_markup=ShopKeyboard.cart_view(cart))


# ── Savatni tozalash ──────────────────────────────────────────────────────────

@router.callback_query(F.data == "cart_clear")
async def cart_clear_cb(call: CallbackQuery, bot_id: int, bot_data: dict):
    """Savatni tozalaydi."""
    await clear_cart(bot_id, call.from_user.id)
    footer = _get_footer(bot_data)
    await call.message.edit_text("🗑 Savat tozalandi." + footer)
    await call.answer("✅ Savat tozalandi!")


# ── Buyurtma berish ───────────────────────────────────────────────────────────

@router.callback_query(F.data == "order_checkout")
async def order_checkout_cb(call: CallbackQuery, bot_id: int, bot_data: dict, state: FSMContext):
    """Buyurtma berish jarayonini boshlaydi."""
    cart = await get_cart(bot_id, call.from_user.id)

    if not cart:
        await call.answer("🛒 Savat bo'm-bo'sh!", show_alert=True)
        return

    # Foydalanuvchi telefon raqami mavjudligini tekshiradi
    shop_user = await get_shop_user(bot_id, call.from_user.id)

    if shop_user and shop_user.get("phone"):
        # Telefon raqami bor, manzilga o'tamiz
        await state.set_state(CheckoutState.address)
        await state.update_data(phone=shop_user["phone"])
        await call.message.answer(
            f"📍 Yetkazish manzilingizni kiriting:\n"
            f"(Telefon: {shop_user['phone']})",
            reply_markup=ShopKeyboard.skip_cancel()
        )
    else:
        # Telefon raqami yo'q
        await state.set_state(CheckoutState.phone)
        await call.message.answer(
            "📱 Telefon raqamingizni yuboring:",
            reply_markup=ShopKeyboard.share_contact()
        )
    await call.answer()


@router.message(CheckoutState.phone, F.contact)
async def checkout_phone_contact(message: Message, bot_id: int, bot_data: dict, state: FSMContext):
    """Telefon raqamini kontakt orqali oladi."""
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = f"+{phone}"
    await set_shop_user_phone(bot_id, message.from_user.id, phone)
    await state.update_data(phone=phone)
    await state.set_state(CheckoutState.address)
    await message.answer(
        f"✅ Telefon raqam: {phone}\n\n"
        "📍 Yetkazish manzilingizni kiriting:",
        reply_markup=ShopKeyboard.skip_cancel()
    )


@router.message(CheckoutState.phone, F.text)
async def checkout_phone_text(message: Message, bot_id: int, bot_data: dict, state: FSMContext):
    """Telefon raqamini matn orqali oladi."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        is_admin = message.from_user.id == bot_data.get("owner_id")
        await message.answer("❌ Buyurtma bekor qilindi.", reply_markup=ShopKeyboard.main_menu(is_admin=is_admin))
        return

    from utils.validators import validate_phone
    phone = validate_phone(message.text)
    if not phone:
        await message.answer("❌ Noto'g'ri raqam! Masalan: +998901234567 yoki kontakt yuboring:")
        return

    await set_shop_user_phone(bot_id, message.from_user.id, phone)
    await state.update_data(phone=phone)
    await state.set_state(CheckoutState.address)
    await message.answer(
        "📍 Yetkazish manzilingizni kiriting:",
        reply_markup=ShopKeyboard.skip_cancel()
    )


@router.message(CheckoutState.address)
async def checkout_address(message: Message, bot_id: int, bot_data: dict, state: FSMContext):
    """Manzilni oladi."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        is_admin = message.from_user.id == bot_data.get("owner_id")
        await message.answer("❌ Buyurtma bekor qilindi.", reply_markup=ShopKeyboard.main_menu(is_admin=is_admin))
        return

    address = None if message.text == "⏩ O'tkazib yuborish" else message.text
    await state.update_data(address=address)
    await state.set_state(CheckoutState.note)
    await message.answer(
        "📝 Izoh (ixtiyoriy):",
        reply_markup=ShopKeyboard.skip_cancel()
    )


@router.message(CheckoutState.note)
async def checkout_note(message: Message, bot_id: int, bot_data: dict, state: FSMContext):
    """Izohni oladi va tasdiqlash so'raydi."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        is_admin = message.from_user.id == bot_data.get("owner_id")
        await message.answer("❌ Buyurtma bekor qilindi.", reply_markup=ShopKeyboard.main_menu(is_admin=is_admin))
        return

    note = None if message.text == "⏩ O'tkazib yuborish" else message.text
    await state.update_data(note=note)

    # Buyurtmani tasdiqlash
    cart = await get_cart(bot_id, message.from_user.id)
    data = await state.get_data()

    total = sum(item["price"] * item["quantity"] for item in cart)
    footer = _get_footer(bot_data)

    cart_text = await _build_cart_text(cart)
    text = (
        f"📋 <b>Buyurtmani tasdiqlash</b>\n\n"
        f"{cart_text}\n\n"
        f"📱 Telefon: {data.get('phone', '—')}\n"
        f"📍 Manzil: {data.get('address') or '—'}\n"
        f"📝 Izoh: {note or '—'}\n"
    )
    text += footer

    await state.set_state(CheckoutState.confirm)
    await message.answer(text, reply_markup=ShopKeyboard.order_confirm())


@router.callback_query(CheckoutState.confirm, F.data == "order_confirm")
async def order_confirm_cb(call: CallbackQuery, bot_id: int, bot_data: dict, state: FSMContext):
    """Buyurtmani tasdiqlaydi va bazaga saqlaydi."""
    cart = await get_cart(bot_id, call.from_user.id)
    if not cart:
        await call.answer("🛒 Savat bo'm-bo'sh!", show_alert=True)
        await state.clear()
        return

    data = await state.get_data()
    total = sum(item["price"] * item["quantity"] for item in cart)

    items = [
        {
            "product_id": item["product_id"],
            "name": item["name"],
            "price": item["price"],
            "qty": item["quantity"],
        }
        for item in cart
    ]

    # Buyurtmani saqlaydi
    order_id = await create_order(
        bot_id=bot_id,
        customer_id=call.from_user.id,
        customer_name=call.from_user.full_name,
        items=items,
        total_price=total,
        customer_phone=data.get("phone"),
        customer_address=data.get("address"),
        note=data.get("note")
    )

    # Savatni tozalaydi
    await clear_cart(bot_id, call.from_user.id)
    await state.clear()

    footer = _get_footer(bot_data)
    is_admin = call.from_user.id == bot_data.get("owner_id")

    await call.message.answer(
        f"✅ <b>Buyurtmangiz qabul qilindi!</b>\n\n"
        f"🧾 Buyurtma #{order_id}\n"
        f"💰 Jami: {format_price(total)}\n\n"
        f"Admin tez orada siz bilan bog'lanadi." + footer,
        reply_markup=ShopKeyboard.main_menu(is_admin=is_admin)
    )

    # Adminga xabar yuborish
    owner_id = bot_data.get("owner_id")
    if owner_id:
        items_text = "\n".join(
            f"• {item['name']} × {item['qty']} = {format_price(item['price'] * item['qty'])}"
            for item in items
        )
        admin_text = (
            f"🆕 <b>Yangi buyurtma #{order_id}!</b>\n\n"
            f"👤 Xaridor: {call.from_user.full_name}\n"
            f"📱 Telefon: {data.get('phone', '—')}\n"
            f"📍 Manzil: {data.get('address') or '—'}\n\n"
            f"📦 Mahsulotlar:\n{items_text}\n\n"
            f"💰 Jami: {format_price(total)}"
        )
        if data.get("note"):
            admin_text += f"\n📝 Izoh: {data['note']}"

        # Admin ga main bot orqali yoki shop bot orqali xabar yuboramiz
        try:
            await call.bot.send_message(owner_id, admin_text, parse_mode="HTML")
        except Exception as e:
            logger.warning("Adminga xabar yuborishda xato: %s", e)

    await call.answer()


@router.callback_query(CheckoutState.confirm, F.data == "order_cancel")
async def order_cancel_cb(call: CallbackQuery, bot_id: int, bot_data: dict, state: FSMContext):
    """Buyurtmani bekor qiladi."""
    await state.clear()
    is_admin = call.from_user.id == bot_data.get("owner_id")
    footer = _get_footer(bot_data)
    await call.message.answer(
        "❌ Buyurtma bekor qilindi." + footer,
        reply_markup=ShopKeyboard.main_menu(is_admin=is_admin)
    )
    await call.answer()
