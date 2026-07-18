"""
Shop bot — admin panel handlerlari.
Faqat bot egasi (owner) kirishi mumkin.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.queries import (
    get_products, get_product, update_product, delete_product,
    create_product, get_categories, create_category, delete_category,
    get_bot_orders, update_order_status, get_bot_stats, count_orders,
    get_shop_users, get_bot, update_bot
)
from keyboards.shop_kb import ShopKeyboard
from utils.helpers import format_price, build_order_text, get_order_status_label, paginate
from utils.validators import validate_price
from utils.bot_manager import broadcast_to_shop_users

logger = logging.getLogger(__name__)
router = Router()


def _is_admin(user_id: int, bot_data: dict) -> bool:
    return user_id == bot_data.get("owner_id")


def _get_footer(bot_data: dict) -> str:
    if bot_data.get("footer_enabled", 1):
        return "\n\n<i>Powered by @ShopMakerUzBot</i>"
    return ""


class AdminAddProductState(StatesGroup):
    name = State()
    price = State()
    description = State()
    photo = State()
    category = State()


class AdminEditProductState(StatesGroup):
    field = State()
    value = State()


class AdminAddCategoryState(StatesGroup):
    name = State()
    icon = State()


class AdminBroadcastState(StatesGroup):
    message_text = State()
    confirm = State()


class AdminSettingsState(StatesGroup):
    welcome = State()
    about = State()
    contact = State()


class AdminEditProdFieldState(StatesGroup):
    name = State()
    price = State()
    description = State()
    photo = State()
    category = State()


# ── Admin menyusiga kirish ───────────────────────────────────────────────────

@router.message(F.text == "👑 Admin panel")
async def shop_admin_panel(message: Message, bot_id: int, bot_data: dict, state: FSMContext):
    """Shop admin panelini ochadi."""
    if not _is_admin(message.from_user.id, bot_data):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return

    await state.clear()
    stats = await get_bot_stats(bot_id)
    bot_name = bot_data.get("bot_name", "Do'konim")
    footer = _get_footer(bot_data)

    await message.answer(
        f"👑 <b>Admin Panel</b> — {bot_name}\n\n"
        f"👥 Xaridorlar: {stats['total_users']}\n"
        f"📦 Mahsulotlar: {stats['total_products']}\n"
        f"📂 Kategoriyalar: {stats['total_categories']}\n"
        f"📋 Buyurtmalar: {stats['total_orders']}\n"
        f"🆕 Yangi: {stats['new_orders']}\n"
        f"💰 Daromad: {format_price(stats['revenue'])}" + footer,
        reply_markup=ShopKeyboard.admin_main(bot_id)
    )


# ── Mahsulotlar ──────────────────────────────────────────────────────────────

@router.message(F.text == "📦 Mahsulotlar")
async def admin_products_list(message: Message, bot_id: int, bot_data: dict):
    """Admin mahsulotlar ro'yxati."""
    if not _is_admin(message.from_user.id, bot_data):
        return

    products = await get_products(bot_id, available_only=False)
    if not products:
        await message.answer("📦 Mahsulotlar yo'q.")
        return

    page_prods, total_pages, _ = paginate(products, 1, 8)
    await message.answer(
        f"📦 <b>Mahsulotlar</b> ({len(products)} ta):",
        reply_markup=ShopKeyboard.admin_products(page_prods, 1, total_pages)
    )


@router.callback_query(F.data.startswith("admin_prods_page:"))
async def admin_prods_page_cb(call: CallbackQuery, bot_id: int, bot_data: dict):
    if not _is_admin(call.from_user.id, bot_data):
        return

    page = int(call.data.split(":")[1])
    products = await get_products(bot_id, available_only=False)
    page_prods, total_pages, page = paginate(products, page, 8)

    await call.message.edit_text(
        f"📦 <b>Mahsulotlar</b> ({len(products)} ta):",
        reply_markup=ShopKeyboard.admin_products(page_prods, page, total_pages)
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin_product:"))
async def admin_product_detail(call: CallbackQuery, bot_id: int, bot_data: dict):
    """Admin mahsulot tafsilotlari."""
    if not _is_admin(call.from_user.id, bot_data):
        return

    product_id = int(call.data.split(":")[1])
    prod = await get_product(product_id)
    if not prod:
        await call.answer("❌ Mahsulot topilmadi.", show_alert=True)
        return

    avail = "✅ Mavjud" if prod["is_available"] else "❌ Yashirin"
    text = (
        f"📦 <b>{prod['name']}</b>\n"
        f"💰 Narx: {format_price(prod['price'])}\n"
        f"📊 Holat: {avail}\n"
    )
    if prod["description"]:
        text += f"📄 Tavsif: {prod['description'][:100]}\n"

    await call.message.edit_text(
        text,
        reply_markup=ShopKeyboard.admin_product_actions(product_id, bool(prod["is_available"]))
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin_toggle_prod:"))
async def admin_toggle_prod(call: CallbackQuery, bot_id: int, bot_data: dict):
    """Mahsulot mavjudligini o'zgartiradi."""
    if not _is_admin(call.from_user.id, bot_data):
        return

    product_id = int(call.data.split(":")[1])
    prod = await get_product(product_id)
    if not prod:
        await call.answer("❌ Topilmadi.", show_alert=True)
        return

    new_avail = not bool(prod["is_available"])
    await update_product(product_id, is_available=int(new_avail))
    status = "ko'rsatildi ✅" if new_avail else "yashirildi ❌"
    await call.answer(f"Mahsulot {status}", show_alert=True)
    await admin_product_detail(call, bot_id, bot_data)


@router.callback_query(F.data.startswith("admin_del_prod:"))
async def admin_del_prod_confirm(call: CallbackQuery, bot_id: int, bot_data: dict):
    """Mahsulot o'chirish tasdiqlash."""
    if not _is_admin(call.from_user.id, bot_data):
        return

    product_id = int(call.data.split(":")[1])
    await call.message.edit_text(
        "⚠️ Mahsulotni o'chirishni tasdiqlaysizmi?",
        reply_markup=ShopKeyboard.admin_del_prod_confirm(product_id)
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin_del_prod_ok:"))
async def admin_del_prod_ok(call: CallbackQuery, bot_id: int, bot_data: dict):
    """Mahsulotni o'chiradi."""
    if not _is_admin(call.from_user.id, bot_data):
        return

    product_id = int(call.data.split(":")[1])
    await delete_product(product_id)
    await call.message.edit_text("✅ Mahsulot o'chirildi.")
    await call.answer("✅ O'chirildi!", show_alert=True)


# ── Mahsulot tahrirlash ──────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("admin_edit_prod:"))
async def admin_edit_prod_menu(call: CallbackQuery, bot_id: int, bot_data: dict):
    if not _is_admin(call.from_user.id, bot_data):
        return

    product_id = int(call.data.split(":")[1])
    await call.message.edit_text(
        "✏️ Qaysi ma'lumotni o'zgartirmoqchisiz?",
        reply_markup=ShopKeyboard.admin_edit_product_fields(product_id)
    )
    await call.answer()


@router.callback_query(F.data.startswith("aep_name:"))
async def aep_name_cb(call: CallbackQuery, bot_id: int, bot_data: dict, state: FSMContext):
    if not _is_admin(call.from_user.id, bot_data):
        return
    product_id = int(call.data.split(":")[1])
    await state.set_state(AdminEditProdFieldState.name)
    await state.update_data(product_id=product_id)
    await call.message.answer("📝 Yangi nomni kiriting:", reply_markup=ShopKeyboard.cancel())
    await call.answer()


@router.message(AdminEditProdFieldState.name)
async def aep_name_save(message: Message, bot_id: int, bot_data: dict, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return
    if not _is_admin(message.from_user.id, bot_data):
        await state.clear()
        return
    data = await state.get_data()
    await update_product(data["product_id"], name=message.text)
    await state.clear()
    await message.answer("✅ Nomi yangilandi!", reply_markup=ShopKeyboard.admin_main(bot_id))


@router.callback_query(F.data.startswith("aep_price:"))
async def aep_price_cb(call: CallbackQuery, bot_id: int, bot_data: dict, state: FSMContext):
    if not _is_admin(call.from_user.id, bot_data):
        return
    product_id = int(call.data.split(":")[1])
    await state.set_state(AdminEditProdFieldState.price)
    await state.update_data(product_id=product_id)
    await call.message.answer("💰 Yangi narxni kiriting (so'mda):", reply_markup=ShopKeyboard.cancel())
    await call.answer()


@router.message(AdminEditProdFieldState.price)
async def aep_price_save(message: Message, bot_id: int, bot_data: dict, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return
    if not _is_admin(message.from_user.id, bot_data):
        await state.clear()
        return
    price = validate_price(message.text)
    if price is None:
        await message.answer("❌ Noto'g'ri narx! Raqam kiriting:")
        return
    data = await state.get_data()
    await update_product(data["product_id"], price=price)
    await state.clear()
    await message.answer(f"✅ Narx {format_price(price)} ga yangilandi!", reply_markup=ShopKeyboard.admin_main(bot_id))


@router.callback_query(F.data.startswith("aep_desc:"))
async def aep_desc_cb(call: CallbackQuery, bot_id: int, bot_data: dict, state: FSMContext):
    if not _is_admin(call.from_user.id, bot_data):
        return
    product_id = int(call.data.split(":")[1])
    await state.set_state(AdminEditProdFieldState.description)
    await state.update_data(product_id=product_id)
    await call.message.answer("📄 Yangi tavsifni kiriting:", reply_markup=ShopKeyboard.skip_cancel())
    await call.answer()


@router.message(AdminEditProdFieldState.description)
async def aep_desc_save(message: Message, bot_id: int, bot_data: dict, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return
    if not _is_admin(message.from_user.id, bot_data):
        await state.clear()
        return
    desc = None if message.text == "⏩ O'tkazib yuborish" else message.text
    data = await state.get_data()
    await update_product(data["product_id"], description=desc)
    await state.clear()
    await message.answer("✅ Tavsif yangilandi!", reply_markup=ShopKeyboard.admin_main(bot_id))


@router.callback_query(F.data.startswith("aep_photo:"))
async def aep_photo_cb(call: CallbackQuery, bot_id: int, bot_data: dict, state: FSMContext):
    if not _is_admin(call.from_user.id, bot_data):
        return
    product_id = int(call.data.split(":")[1])
    await state.set_state(AdminEditProdFieldState.photo)
    await state.update_data(product_id=product_id)
    await call.message.answer("🖼 Yangi rasmni yuboring:", reply_markup=ShopKeyboard.skip_cancel())
    await call.answer()


@router.message(AdminEditProdFieldState.photo, F.photo)
async def aep_photo_save(message: Message, bot_id: int, bot_data: dict, state: FSMContext):
    if not _is_admin(message.from_user.id, bot_data):
        await state.clear()
        return
    photo_id = message.photo[-1].file_id
    data = await state.get_data()
    await update_product(data["product_id"], photo_id=photo_id)
    await state.clear()
    await message.answer("✅ Rasm yangilandi!", reply_markup=ShopKeyboard.admin_main(bot_id))


@router.message(AdminEditProdFieldState.photo)
async def aep_photo_skip(message: Message, bot_id: int, bot_data: dict, state: FSMContext):
    if message.text == "❌ Bekor qilish" or message.text == "⏩ O'tkazib yuborish":
        await state.clear()
        return


@router.callback_query(F.data.startswith("aep_cat:"))
async def aep_cat_cb(call: CallbackQuery, bot_id: int, bot_data: dict, state: FSMContext):
    if not _is_admin(call.from_user.id, bot_data):
        return
    product_id = int(call.data.split(":")[1])
    cats = await get_categories(bot_id)
    await state.set_state(AdminEditProdFieldState.category)
    await state.update_data(product_id=product_id)
    await call.message.answer(
        "📂 Kategoriya tanlang:",
        reply_markup=ShopKeyboard.admin_cats_for_product(cats)
    )
    await call.answer()


@router.callback_query(AdminEditProdFieldState.category, F.data.startswith("aep_set_cat:"))
async def aep_cat_save(call: CallbackQuery, bot_id: int, bot_data: dict, state: FSMContext):
    cat_id = call.data.split(":")[1]
    cat_id_val = int(cat_id) if cat_id != "0" else None
    data = await state.get_data()
    await update_product(data["product_id"], category_id=cat_id_val)
    await state.clear()
    await call.message.answer("✅ Kategoriya yangilandi!", reply_markup=ShopKeyboard.admin_main(bot_id))
    await call.answer()


# ── Mahsulot qo'shish (admin bot dan) ───────────────────────────────────────

@router.message(F.text == "➕ Mahsulot qo'shish")
async def admin_add_product_start(message: Message, bot_id: int, bot_data: dict, state: FSMContext):
    if not _is_admin(message.from_user.id, bot_data):
        return
    await state.set_state(AdminAddProductState.name)
    await message.answer("📝 Mahsulot nomini kiriting:", reply_markup=ShopKeyboard.cancel())


@router.message(AdminAddProductState.name)
async def admin_add_prod_name(message: Message, bot_id: int, bot_data: dict, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=ShopKeyboard.admin_main(bot_id))
        return
    await state.update_data(name=message.text)
    await state.set_state(AdminAddProductState.price)
    await message.answer("💰 Narxini kiriting (so'mda):", reply_markup=ShopKeyboard.cancel())


@router.message(AdminAddProductState.price)
async def admin_add_prod_price(message: Message, bot_id: int, bot_data: dict, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=ShopKeyboard.admin_main(bot_id))
        return
    price = validate_price(message.text)
    if price is None:
        await message.answer("❌ Noto'g'ri narx! Raqam kiriting:")
        return
    await state.update_data(price=price)
    await state.set_state(AdminAddProductState.description)
    await message.answer("📄 Tavsif kiriting (ixtiyoriy):", reply_markup=ShopKeyboard.skip_cancel())


@router.message(AdminAddProductState.description)
async def admin_add_prod_desc(message: Message, bot_id: int, bot_data: dict, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=ShopKeyboard.admin_main(bot_id))
        return
    desc = None if message.text == "⏩ O'tkazib yuborish" else message.text
    await state.update_data(description=desc)
    await state.set_state(AdminAddProductState.photo)
    await message.answer("🖼 Rasmini yuboring (ixtiyoriy):", reply_markup=ShopKeyboard.skip_cancel())


@router.message(AdminAddProductState.photo, F.photo)
async def admin_add_prod_photo(message: Message, bot_id: int, bot_data: dict, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    await _admin_ask_category(message, bot_id, state)


@router.message(AdminAddProductState.photo)
async def admin_add_prod_skip_photo(message: Message, bot_id: int, bot_data: dict, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=ShopKeyboard.admin_main(bot_id))
        return
    await state.update_data(photo_id=None)
    await _admin_ask_category(message, bot_id, state)


async def _admin_ask_category(message: Message, bot_id: int, state: FSMContext):
    cats = await get_categories(bot_id)
    if cats:
        await state.set_state(AdminAddProductState.category)
        await message.answer("📂 Kategoriya tanlang:", reply_markup=ShopKeyboard.admin_cats_for_product(cats))
    else:
        await state.update_data(category_id=None)
        await _admin_save_product(message, bot_id, state)


@router.callback_query(AdminAddProductState.category, F.data.startswith("aep_set_cat:"))
async def admin_add_prod_cat(call: CallbackQuery, bot_id: int, bot_data: dict, state: FSMContext):
    cat_id = call.data.split(":")[1]
    cat_id_val = int(cat_id) if cat_id != "0" else None
    await state.update_data(category_id=cat_id_val)
    await _admin_save_product(call.message, bot_id, state)
    await call.answer()


async def _admin_save_product(message: Message, bot_id: int, state: FSMContext):
    data = await state.get_data()
    prod_id = await create_product(
        bot_id=bot_id,
        name=data["name"],
        price=data["price"],
        description=data.get("description"),
        category_id=data.get("category_id"),
        photo_id=data.get("photo_id")
    )
    await state.clear()
    await message.answer(
        f"✅ Mahsulot qo'shildi!\n{data['name']} — {format_price(data['price'])}",
        reply_markup=ShopKeyboard.admin_main(bot_id)
    )


# ── Kategoriyalar ─────────────────────────────────────────────────────────────

@router.message(F.text == "📂 Kategoriyalar")
async def admin_cats_list(message: Message, bot_id: int, bot_data: dict):
    """Admin kategoriyalar ro'yxati."""
    if not _is_admin(message.from_user.id, bot_data):
        # Agar admin emas, oddiy kategoriyalar ko'rsatamiz
        from handlers.shop_bot.categories import shop_categories
        await shop_categories(message, bot_id, bot_data)
        return

    cats = await get_categories(bot_id)
    if not cats:
        await message.answer("📂 Kategoriyalar yo'q.", reply_markup=ShopKeyboard.admin_main(bot_id))
        return

    await message.answer(
        f"📂 <b>Kategoriyalar</b> ({len(cats)} ta)\nO'chirish uchun bosing:",
        reply_markup=ShopKeyboard.admin_cats(cats)
    )


@router.callback_query(F.data == "admin_cats_list")
async def admin_cats_list_cb(call: CallbackQuery, bot_id: int, bot_data: dict):
    if not _is_admin(call.from_user.id, bot_data):
        return
    cats = await get_categories(bot_id)
    if not cats:
        await call.message.edit_text("📂 Kategoriyalar yo'q.")
        return
    await call.message.edit_text(
        f"📂 Kategoriyalar ({len(cats)} ta):",
        reply_markup=ShopKeyboard.admin_cats(cats)
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin_del_cat:"))
async def admin_del_cat_confirm(call: CallbackQuery, bot_id: int, bot_data: dict):
    if not _is_admin(call.from_user.id, bot_data):
        return
    cat_id = int(call.data.split(":")[1])
    await call.message.edit_text(
        "⚠️ Kategoriyani o'chirishni tasdiqlaysizmi?",
        reply_markup=ShopKeyboard.admin_del_cat_confirm(cat_id)
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin_del_cat_ok:"))
async def admin_del_cat_ok(call: CallbackQuery, bot_id: int, bot_data: dict):
    if not _is_admin(call.from_user.id, bot_data):
        return
    cat_id = int(call.data.split(":")[1])
    await delete_category(cat_id)
    await call.message.edit_text("✅ Kategoriya o'chirildi.")
    await call.answer("✅ O'chirildi!", show_alert=True)


# Kategoriya qo'shish (admin) — alohida trigger yo'q, main bot orqali qilinadi
# Shop bot admin uchun ham qo'shishni qo'shaylik:
# (Oddiy matn trigger emas, inline orqali)


# ── Buyurtmalar ───────────────────────────────────────────────────────────────

@router.message(F.text == "📋 Buyurtmalar")
async def admin_orders_menu(message: Message, bot_id: int, bot_data: dict):
    """Admin buyurtmalar filtri."""
    if not _is_admin(message.from_user.id, bot_data):
        from handlers.shop_bot.orders import my_orders
        await my_orders(message, bot_id, bot_data)
        return

    total = await count_orders(bot_id)
    new_count = await count_orders(bot_id, status="new")
    footer = _get_footer(bot_data)

    await message.answer(
        f"📋 <b>Buyurtmalar</b>\n\nJami: {total} ta\n🆕 Yangi: {new_count} ta\n\nFiltrni tanlang:" + footer,
        reply_markup=ShopKeyboard.admin_orders_filter()
    )


@router.callback_query(F.data.startswith("admin_orders:"))
async def admin_orders_filter_cb(call: CallbackQuery, bot_id: int, bot_data: dict):
    """Filtrlangan buyurtmalar."""
    if not _is_admin(call.from_user.id, bot_data):
        return

    status = call.data.split(":")[1]
    status_filter = None if status == "all" else status
    orders = await get_bot_orders(bot_id, status=status_filter, limit=10)

    if not orders:
        await call.answer("📋 Buyurtmalar topilmadi.", show_alert=True)
        return

    for order in orders:
        text = build_order_text(order)
        await call.message.answer(
            text,
            reply_markup=ShopKeyboard.admin_order_actions(order["id"])
        )

    await call.answer()


@router.callback_query(F.data.startswith("ao_status:"))
async def admin_order_status_cb(call: CallbackQuery, bot_id: int, bot_data: dict):
    """Buyurtma holatini o'zgartiradi."""
    if not _is_admin(call.from_user.id, bot_data):
        return

    parts = call.data.split(":")
    order_id = int(parts[1])
    new_status = parts[2]

    await update_order_status(order_id, new_status)
    status_label = get_order_status_label(new_status)
    await call.answer(f"✅ Holat: {status_label}", show_alert=True)

    # Xaridorga xabar yuborish
    from database.queries import get_order
    order = await get_order(order_id)
    if order:
        try:
            await call.bot.send_message(
                order["customer_id"],
                f"📦 <b>Buyurtmangiz holati yangilandi!</b>\n\n"
                f"Buyurtma #{order_id}\n"
                f"Yangi holat: <b>{status_label}</b>",
                parse_mode="HTML"
            )
        except Exception:
            pass


# ── Statistika ────────────────────────────────────────────────────────────────

@router.message(F.text == "📊 Statistika")
async def admin_statistics(message: Message, bot_id: int, bot_data: dict):
    """Admin statistika."""
    if not _is_admin(message.from_user.id, bot_data):
        return

    stats = await get_bot_stats(bot_id)
    footer = _get_footer(bot_data)
    bot_name = bot_data.get("bot_name", "Do'konim")

    await message.answer(
        f"📊 <b>Statistika</b> — {bot_name}\n\n"
        f"👥 Xaridorlar: <b>{stats['total_users']}</b>\n"
        f"📦 Mahsulotlar: <b>{stats['total_products']}</b>\n"
        f"📂 Kategoriyalar: <b>{stats['total_categories']}</b>\n"
        f"📋 Jami buyurtmalar: <b>{stats['total_orders']}</b>\n"
        f"🆕 Yangi buyurtmalar: <b>{stats['new_orders']}</b>\n"
        f"💰 Daromad: <b>{format_price(stats['revenue'])}</b>" + footer,
        reply_markup=ShopKeyboard.admin_main(bot_id)
    )


# ── Broadcast ─────────────────────────────────────────────────────────────────

@router.message(F.text == "📣 Xabar yuborish")
async def admin_broadcast_start(message: Message, bot_id: int, bot_data: dict, state: FSMContext):
    """Broadcast boshlash."""
    if not _is_admin(message.from_user.id, bot_data):
        return
    await state.set_state(AdminBroadcastState.message_text)
    await message.answer(
        "📣 Barcha xaridorlarga yuboriladigan xabarni kiriting:",
        reply_markup=ShopKeyboard.cancel()
    )


@router.message(AdminBroadcastState.message_text)
async def admin_broadcast_msg(message: Message, bot_id: int, bot_data: dict, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=ShopKeyboard.admin_main(bot_id))
        return
    await state.update_data(broadcast_text=message.text)
    await state.set_state(AdminBroadcastState.confirm)
    await message.answer(
        f"📣 Quyidagi xabar barcha xaridorlarga yuboriladi:\n\n{message.text}\n\nTasdiqlaysizmi?",
        reply_markup=ShopKeyboard.broadcast_confirm()
    )


@router.callback_query(AdminBroadcastState.confirm, F.data == "admin_broadcast_send")
async def admin_broadcast_send(call: CallbackQuery, bot_id: int, bot_data: dict, state: FSMContext):
    data = await state.get_data()
    text = data.get("broadcast_text", "")
    await state.clear()

    users = await get_shop_users(bot_id)
    user_ids = [u["user_id"] for u in users]

    sent, failed = await broadcast_to_shop_users(bot_id, user_ids, text, parse_mode="HTML")
    footer = _get_footer(bot_data)

    await call.message.answer(
        f"✅ <b>Xabar yuborildi!</b>\n\n"
        f"✅ Yuborildi: {sent}\n"
        f"❌ Xato: {failed}" + footer,
        reply_markup=ShopKeyboard.admin_main(bot_id)
    )
    await call.answer()


@router.callback_query(AdminBroadcastState.confirm, F.data == "admin_broadcast_cancel")
async def admin_broadcast_cancel(call: CallbackQuery, bot_id: int, bot_data: dict, state: FSMContext):
    await state.clear()
    await call.message.answer("❌ Bekor qilindi.", reply_markup=ShopKeyboard.admin_main(bot_id))
    await call.answer()
