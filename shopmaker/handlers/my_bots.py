"""
Bot boshqaruv handlerlari — yaratish, o'chirish, sozlash.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import config, texts
from database.queries import (
    get_user_bots, get_bot, create_bot, delete_bot, update_bot,
    count_user_bots, get_bot_by_token, get_categories, get_products,
    get_bot_orders, count_orders, get_bot_stats, add_log,
    get_all_active_bots
)
from keyboards.main_kb import MainKeyboard
from utils.validators import validate_bot_token
from utils.helpers import format_price, get_plan_label, format_date, paginate
from utils.bot_manager import start_shop_bot, stop_shop_bot, is_bot_running

logger = logging.getLogger(__name__)
router = Router()

# Bot limitleri
PLAN_LIMITS = {"free": 1, "comfort": 1, "premium": 3}


class AddBotState(StatesGroup):
    waiting_for_token = State()


class BotSettingsState(StatesGroup):
    welcome = State()
    about = State()
    contact = State()


class BroadcastState(StatesGroup):
    waiting_message = State()
    confirm = State()


# ── Botlar ro'yxati ──────────────────────────────────────────────────────────

@router.message(F.text == "🤖 Mening botlarim")
async def show_my_bots(message: Message, user_data: dict, state: FSMContext):
    """Foydalanuvchi botlari ro'yxatini ko'rsatadi."""
    await state.clear()
    bots = await get_user_bots(message.from_user.id)

    if not bots:
        await message.answer(
            "🤖 <b>Mening botlarim</b>\n\n"
            "Sizda hali bot mavjud emas.\n"
            "«➕ Bot qo'shish» tugmasini bosib yangi bot qo'shing.",
        )
        return

    plan = user_data.get("plan", "free")
    limit = PLAN_LIMITS.get(plan, 1)
    text = (
        f"🤖 <b>Mening botlarim</b>\n"
        f"📦 Reja: {get_plan_label(plan)} ({len(bots)}/{limit} ta bot)\n\n"
        "Botni boshqarish uchun bosing:"
    )

    page_bots, total_pages, page = paginate(bots, 1, 8)
    await message.answer(text, reply_markup=MainKeyboard.bot_list(page_bots, 1, total_pages))


@router.callback_query(F.data.startswith("bots_page:"))
async def bots_page_cb(call: CallbackQuery, user_data: dict):
    """Botlar sahifasini o'zgartiradi."""
    page = int(call.data.split(":")[1])
    bots = await get_user_bots(call.from_user.id)
    page_bots, total_pages, page = paginate(bots, page, 8)

    await call.message.edit_reply_markup(
        reply_markup=MainKeyboard.bot_list(page_bots, page, total_pages)
    )
    await call.answer()


@router.callback_query(F.data == "my_bots")
async def my_bots_cb(call: CallbackQuery, user_data: dict):
    """Botlar ro'yxatiga qaytish."""
    bots = await get_user_bots(call.from_user.id)
    if not bots:
        await call.message.edit_text("Botlar mavjud emas.")
        return

    page_bots, total_pages, _ = paginate(bots, 1, 8)
    await call.message.edit_text(
        "🤖 <b>Mening botlarim</b>\n\nBotni boshqarish uchun bosing:",
        reply_markup=MainKeyboard.bot_list(page_bots, 1, total_pages)
    )
    await call.answer()


# ── Bot qo'shish ─────────────────────────────────────────────────────────────

@router.message(F.text == "➕ Bot qo'shish")
async def add_bot_start(message: Message, user_data: dict, state: FSMContext):
    """Bot qo'shish jarayonini boshlaydi."""
    plan = user_data.get("plan", "free")
    limit = PLAN_LIMITS.get(plan, 1)
    current_count = await count_user_bots(message.from_user.id)

    if current_count >= limit:
        await message.answer(
            f"❌ <b>Bot limiti to'ldi!</b>\n\n"
            f"Joriy reja: {get_plan_label(plan)}\n"
            f"Bot limiti: {limit} ta\n\n"
            f"Ko'proq bot yaratish uchun rejangizni yangilang:\n"
            f"💎 Premium — 3 ta bot\n\n"
            f"«💎 Rejalar» bo'limiga o'ting."
        )
        return

    await state.set_state(AddBotState.waiting_for_token)
    await message.answer(
        "➕ <b>Yangi bot qo'shish</b>\n\n"
        "Quyidagi qadamlarni bajaring:\n"
        "1️⃣ @BotFather ga o'ting\n"
        "2️⃣ /newbot buyrug'ini yuboring\n"
        "3️⃣ Bot nomini kiriting\n"
        "4️⃣ Bot tokenini nusxalab oling\n\n"
        "✉️ <b>Endi bot tokenini shu yerga yuboring:</b>",
        reply_markup=MainKeyboard.cancel()
    )


@router.message(AddBotState.waiting_for_token)
async def process_bot_token(message: Message, user_data: dict, state: FSMContext):
    """Foydalanuvchi yuborgan tokenni tekshiradi va botni qo'shadi."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        is_admin = config.is_super_admin(message.from_user.id)
        await message.answer("❌ Bekor qilindi.", reply_markup=MainKeyboard.main_menu(is_admin=is_admin))
        return

    token = message.text.strip() if message.text else ""
    wait_msg = await message.answer("⏳ Token tekshirilmoqda...")

    # Oldindan bazada bor ekanligini tekshiradi
    existing = await get_bot_by_token(token)
    if existing:
        await wait_msg.edit_text(texts.ERR_TOKEN_USED)
        return

    # Telegram API orqali tekshiradi
    bot_info = await validate_bot_token(token)
    if not bot_info:
        await wait_msg.edit_text(
            texts.ERR_INVALID_TOKEN + "\n\nToken formati: <code>1234567890:ABC...XYZ</code>"
        )
        return

    # Botni bazaga qo'shadi
    bot_id = await create_bot(
        owner_id=message.from_user.id,
        token=token,
        bot_username=bot_info["username"],
        bot_name=bot_info["first_name"]
    )

    # Bot data ni tayyorlaymiz
    bot_data = {
        "id": bot_id,
        "owner_id": message.from_user.id,
        "token": token,
        "bot_username": bot_info["username"],
        "bot_name": bot_info["first_name"],
        "is_active": 1,
        "is_locked": 0,
        "theme": "default",
        "welcome_text": None,
        "about_text": None,
        "contact_info": None,
        "footer_enabled": 1,
    }

    # Shop botini ishga tushiradi
    success = await start_shop_bot(bot_id, token, bot_data)

    is_admin = config.is_super_admin(message.from_user.id)
    await state.clear()

    status_text = "✅ Bot ulandi va ishga tushdi!" if success else "✅ Bot ulandi! (Qayta ishga tushirishda faollashadi)"

    await wait_msg.edit_text(
        f"🎉 <b>Bot muvaffaqiyatli qo'shildi!</b>\n\n"
        f"🤖 Bot: @{bot_info['username']}\n"
        f"📛 Nomi: {bot_info['first_name']}\n\n"
        f"{status_text}\n\n"
        f"Botni boshqarish uchun «🤖 Mening botlarim» ga o'ting."
    )
    await message.answer("Asosiy menyu:", reply_markup=MainKeyboard.main_menu(is_admin=is_admin))
    await add_log("bot_created", user_id=message.from_user.id, detail=f"bot_id={bot_id}")


# ── Bot menyusi ──────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("bot:"))
async def bot_menu_cb(call: CallbackQuery, user_data: dict):
    """Bot boshqaruv menyusini ko'rsatadi."""
    bot_id = int(call.data.split(":")[1])
    bot = await get_bot(bot_id)

    if not bot or bot["owner_id"] != call.from_user.id:
        await call.answer("❌ Bot topilmadi.", show_alert=True)
        return

    running = is_bot_running(bot_id)
    status = "🟢 Ishlayapti" if (running and bot["is_active"]) else "🔴 To'xtatilgan"
    locked = "🔒 Qulflangan" if bot["is_locked"] else ""

    text = (
        f"🤖 <b>@{bot['bot_username'] or bot['bot_name']}</b>\n\n"
        f"📊 Holat: {status} {locked}\n"
    )
    if bot["is_locked"]:
        text += "\n⚠️ Bu bot Premium reja tugaganligi sababli qulflangan.\nRejani yangilang."

    await call.message.edit_text(
        text,
        reply_markup=MainKeyboard.bot_menu(bot_id, bool(bot["is_active"]), bool(bot["is_locked"]))
    )
    await call.answer()


@router.callback_query(F.data.startswith("bot_toggle:"))
async def bot_toggle_cb(call: CallbackQuery):
    """Botni yoqadi/o'chiradi."""
    bot_id = int(call.data.split(":")[1])
    bot = await get_bot(bot_id)

    if not bot or bot["owner_id"] != call.from_user.id:
        await call.answer("❌ Ruxsat yo'q.", show_alert=True)
        return

    if bot["is_locked"]:
        await call.answer("🔒 Bot qulflangan. Premium rejaga o'ting.", show_alert=True)
        return

    new_active = not bool(bot["is_active"])
    await update_bot(bot_id, is_active=int(new_active))

    if new_active:
        bot_data = dict(bot)
        bot_data["is_active"] = 1
        await start_shop_bot(bot_id, bot["token"], bot_data)
        await call.answer("✅ Bot yoqildi!", show_alert=True)
    else:
        await stop_shop_bot(bot_id)
        await call.answer("⏹ Bot o'chirildi!", show_alert=True)

    # Menyuni yangilaydi
    await bot_menu_cb(call, {})


@router.callback_query(F.data == "locked_info")
async def locked_info_cb(call: CallbackQuery):
    await call.answer(
        "🔒 Bu bot qulflangan. Premium rejani yangilang.",
        show_alert=True
    )


# ── Bot o'chirish ────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("bot_delete:"))
async def bot_delete_cb(call: CallbackQuery):
    """Bot o'chirish tasdiqlash."""
    bot_id = int(call.data.split(":")[1])
    bot = await get_bot(bot_id)

    if not bot or bot["owner_id"] != call.from_user.id:
        await call.answer("❌ Ruxsat yo'q.", show_alert=True)
        return

    await call.message.edit_text(
        f"🗑 <b>Botni o'chirish</b>\n\n"
        f"@{bot['bot_username'] or bot['bot_name']} botini o'chirmoqchimisiz?\n\n"
        f"⚠️ Barcha mahsulotlar, kategoriyalar va buyurtmalar ham o'chiriladi!",
        reply_markup=MainKeyboard.delete_confirm(bot_id)
    )
    await call.answer()


@router.callback_query(F.data.startswith("bot_delete_confirm:"))
async def bot_delete_confirm_cb(call: CallbackQuery):
    """Botni bazadan o'chiradi."""
    bot_id = int(call.data.split(":")[1])
    bot = await get_bot(bot_id)

    if not bot or bot["owner_id"] != call.from_user.id:
        await call.answer("❌ Ruxsat yo'q.", show_alert=True)
        return

    # Botni to'xtatib o'chiradi
    await stop_shop_bot(bot_id)
    await delete_bot(bot_id)

    await call.message.edit_text(
        f"✅ Bot @{bot['bot_username'] or bot['bot_name']} o'chirildi."
    )
    await add_log("bot_deleted", user_id=call.from_user.id, detail=f"bot_id={bot_id}")
    await call.answer("✅ Bot o'chirildi!", show_alert=True)


# ── Bot sozlamalari ──────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("bot_settings:"))
async def bot_settings_cb(call: CallbackQuery):
    """Bot sozlamalari menyusi."""
    bot_id = int(call.data.split(":")[1])
    bot = await get_bot(bot_id)

    if not bot or bot["owner_id"] != call.from_user.id:
        await call.answer("❌ Ruxsat yo'q.", show_alert=True)
        return

    await call.message.edit_text(
        f"⚙️ <b>Bot sozlamalari</b>\n\n"
        f"🤖 @{bot['bot_username'] or bot['bot_name']}\n\n"
        "Nimani o'zgartirmoqchisiz?",
        reply_markup=MainKeyboard.bot_settings(bot_id)
    )
    await call.answer()


@router.callback_query(F.data.startswith("bs_welcome:"))
async def bs_welcome_cb(call: CallbackQuery, state: FSMContext):
    bot_id = int(call.data.split(":")[1])
    await state.set_state(BotSettingsState.welcome)
    await state.update_data(bot_id=bot_id)
    await call.message.answer(
        "👋 Xush kelibsiz matnini kiriting:\n"
        "(Kiruvchi foydalanuvchilarga ko'rsatiladi)",
        reply_markup=MainKeyboard.cancel()
    )
    await call.answer()


@router.message(BotSettingsState.welcome)
async def bs_welcome_save(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return
    data = await state.get_data()
    bot_id = data.get("bot_id")
    await update_bot(bot_id, welcome_text=message.text)
    await state.clear()
    is_admin = config.is_super_admin(message.from_user.id)
    await message.answer("✅ Xush kelibsiz matni saqlandi!", reply_markup=MainKeyboard.main_menu(is_admin=is_admin))


@router.callback_query(F.data.startswith("bs_about:"))
async def bs_about_cb(call: CallbackQuery, state: FSMContext):
    bot_id = int(call.data.split(":")[1])
    await state.set_state(BotSettingsState.about)
    await state.update_data(bot_id=bot_id)
    await call.message.answer(
        "ℹ️ Bot haqida ma'lumot kiriting:",
        reply_markup=MainKeyboard.cancel()
    )
    await call.answer()


@router.message(BotSettingsState.about)
async def bs_about_save(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return
    data = await state.get_data()
    bot_id = data.get("bot_id")
    await update_bot(bot_id, about_text=message.text)
    await state.clear()
    is_admin = config.is_super_admin(message.from_user.id)
    await message.answer("✅ Bot haqida ma'lumot saqlandi!", reply_markup=MainKeyboard.main_menu(is_admin=is_admin))


@router.callback_query(F.data.startswith("bs_contact:"))
async def bs_contact_cb(call: CallbackQuery, state: FSMContext):
    bot_id = int(call.data.split(":")[1])
    await state.set_state(BotSettingsState.contact)
    await state.update_data(bot_id=bot_id)
    await call.message.answer(
        "📞 Aloqa ma'lumotini kiriting:\n"
        "(Masalan: @username yoki +998901234567)",
        reply_markup=MainKeyboard.cancel()
    )
    await call.answer()


@router.message(BotSettingsState.contact)
async def bs_contact_save(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return
    data = await state.get_data()
    bot_id = data.get("bot_id")
    await update_bot(bot_id, contact_info=message.text)
    await state.clear()
    is_admin = config.is_super_admin(message.from_user.id)
    await message.answer("✅ Aloqa ma'lumoti saqlandi!", reply_markup=MainKeyboard.main_menu(is_admin=is_admin))


# ── Mahsulotlar boshqaruvi (main bot dan) ───────────────────────────────────

@router.callback_query(F.data.startswith("bot_products:"))
async def bot_products_cb(call: CallbackQuery):
    """Mahsulotlar boshqaruv menyusi."""
    bot_id = int(call.data.split(":")[1])
    bot = await get_bot(bot_id)

    if not bot or bot["owner_id"] != call.from_user.id:
        await call.answer("❌ Ruxsat yo'q.", show_alert=True)
        return

    await call.message.edit_text(
        f"📦 <b>Mahsulotlar boshqaruvi</b>\n"
        f"🤖 @{bot['bot_username'] or bot['bot_name']}",
        reply_markup=MainKeyboard.products_menu(bot_id)
    )
    await call.answer()


@router.callback_query(F.data.startswith("product_list:"))
async def product_list_cb(call: CallbackQuery):
    """Mahsulotlar ro'yxati."""
    parts = call.data.split(":")
    bot_id = int(parts[1])
    page = int(parts[2]) if len(parts) > 2 else 1

    products = await get_products(bot_id, available_only=False)
    page_prods, total_pages, page = paginate(products, page, 8)

    await call.message.edit_text(
        f"📦 <b>Mahsulotlar ro'yxati</b> ({len(products)} ta)",
        reply_markup=MainKeyboard.product_list(page_prods, bot_id, page, total_pages)
    )
    await call.answer()


@router.callback_query(F.data.startswith("product:"))
async def product_detail_cb(call: CallbackQuery):
    """Mahsulot ma'lumotlari."""
    parts = call.data.split(":")
    product_id = int(parts[1])
    bot_id = int(parts[2])

    from database.queries import get_product, get_category
    prod = await get_product(product_id)

    if not prod:
        await call.answer("❌ Mahsulot topilmadi.", show_alert=True)
        return

    cat_name = "—"
    if prod["category_id"]:
        cat = await get_category(prod["category_id"])
        if cat:
            cat_name = f"{cat['icon']} {cat['name']}"

    avail = "✅ Mavjud" if prod["is_available"] else "❌ Mavjud emas"
    text = (
        f"📦 <b>{prod['name']}</b>\n\n"
        f"💰 Narx: <b>{prod['price']:,.0f} so'm</b>\n"
        f"📂 Kategoriya: {cat_name}\n"
        f"📊 Holat: {avail}\n"
    )
    if prod["description"]:
        text += f"\n📄 Tavsif:\n{prod['description']}"

    await call.message.edit_text(
        text,
        reply_markup=MainKeyboard.product_actions(product_id, bot_id, bool(prod["is_available"]))
    )
    await call.answer()


@router.callback_query(F.data.startswith("toggle_product:"))
async def toggle_product_cb(call: CallbackQuery):
    """Mahsulot mavjudligini o'zgartiradi."""
    parts = call.data.split(":")
    product_id = int(parts[1])
    bot_id = int(parts[2])

    from database.queries import get_product, update_product
    prod = await get_product(product_id)
    if not prod:
        await call.answer("❌ Mahsulot topilmadi.", show_alert=True)
        return

    new_avail = not bool(prod["is_available"])
    await update_product(product_id, is_available=int(new_avail))
    status = "ko'rsatildi ✅" if new_avail else "yashirildi ❌"
    await call.answer(f"Mahsulot {status}", show_alert=True)
    await product_detail_cb(call)


@router.callback_query(F.data.startswith("delete_product:"))
async def delete_product_cb(call: CallbackQuery):
    """Mahsulot o'chirish tasdiqlash."""
    parts = call.data.split(":")
    product_id = int(parts[1])
    bot_id = int(parts[2])

    await call.message.edit_text(
        "⚠️ Mahsulotni o'chirishni tasdiqlaysizmi?",
        reply_markup=MainKeyboard.delete_product_confirm(product_id, bot_id)
    )
    await call.answer()


@router.callback_query(F.data.startswith("del_product_ok:"))
async def del_product_ok_cb(call: CallbackQuery):
    """Mahsulotni o'chiradi."""
    parts = call.data.split(":")
    product_id = int(parts[1])
    bot_id = int(parts[2])

    from database.queries import delete_product
    await delete_product(product_id)
    await call.message.edit_text(
        "✅ Mahsulot o'chirildi.",
        reply_markup=MainKeyboard.products_menu(bot_id)
    )
    await call.answer("✅ O'chirildi!", show_alert=True)


# ── Kategoriyalar boshqaruvi ─────────────────────────────────────────────────

@router.callback_query(F.data.startswith("bot_cats:"))
async def bot_cats_cb(call: CallbackQuery):
    """Kategoriyalar boshqaruv menyusi."""
    bot_id = int(call.data.split(":")[1])
    bot = await get_bot(bot_id)

    if not bot or bot["owner_id"] != call.from_user.id:
        await call.answer("❌ Ruxsat yo'q.", show_alert=True)
        return

    await call.message.edit_text(
        f"📂 <b>Kategoriyalar boshqaruvi</b>\n"
        f"🤖 @{bot['bot_username'] or bot['bot_name']}",
        reply_markup=MainKeyboard.categories_menu(bot_id)
    )
    await call.answer()


@router.callback_query(F.data.startswith("cat_list:"))
async def cat_list_cb(call: CallbackQuery):
    """Kategoriyalar ro'yxatini ko'rsatadi."""
    bot_id = int(call.data.split(":")[1])
    cats = await get_categories(bot_id)

    if not cats:
        await call.message.edit_text(
            "📂 Kategoriyalar yo'q.\n«➕ Kategoriya qo'shish» tugmasini bosing.",
            reply_markup=MainKeyboard.categories_menu(bot_id)
        )
        return

    await call.message.edit_text(
        f"📂 <b>Kategoriyalar</b> ({len(cats)} ta):",
        reply_markup=MainKeyboard.cat_list(cats, bot_id)
    )
    await call.answer()


@router.callback_query(F.data.startswith("cat_action:"))
async def cat_action_cb(call: CallbackQuery):
    """Kategoriya amallari."""
    parts = call.data.split(":")
    cat_id = int(parts[1])
    bot_id = int(parts[2])

    from database.queries import get_category
    cat = await get_category(cat_id)
    if not cat:
        await call.answer("❌ Kategoriya topilmadi.", show_alert=True)
        return

    await call.message.edit_text(
        f"📂 <b>{cat['icon']} {cat['name']}</b>\n\nNima qilmoqchisiz?",
        reply_markup=MainKeyboard.cat_actions(cat_id, bot_id)
    )
    await call.answer()


@router.callback_query(F.data.startswith("del_cat:"))
async def del_cat_cb(call: CallbackQuery):
    """Kategoriya o'chirish tasdiqlash."""
    parts = call.data.split(":")
    cat_id = int(parts[1])
    bot_id = int(parts[2])

    await call.message.edit_text(
        "⚠️ Kategoriyani o'chirishni tasdiqlaysizmi?\n"
        "(Mahsulotlardan kategoriya ma'lumoti o'chiriladi)",
        reply_markup=MainKeyboard.del_cat_confirm(cat_id, bot_id)
    )
    await call.answer()


@router.callback_query(F.data.startswith("del_cat_ok:"))
async def del_cat_ok_cb(call: CallbackQuery):
    """Kategoriyani o'chiradi."""
    parts = call.data.split(":")
    cat_id = int(parts[1])
    bot_id = int(parts[2])

    from database.queries import delete_category
    await delete_category(cat_id)
    await call.message.edit_text(
        "✅ Kategoriya o'chirildi.",
        reply_markup=MainKeyboard.categories_menu(bot_id)
    )
    await call.answer("✅ O'chirildi!", show_alert=True)


# ── Buyurtmalar ko'rish ───────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("bot_orders:"))
async def bot_orders_cb(call: CallbackQuery):
    """Bot buyurtmalar filtri."""
    bot_id = int(call.data.split(":")[1])
    bot = await get_bot(bot_id)

    if not bot or bot["owner_id"] != call.from_user.id:
        await call.answer("❌ Ruxsat yo'q.", show_alert=True)
        return

    total = await count_orders(bot_id)
    new_count = await count_orders(bot_id, status="new")

    await call.message.edit_text(
        f"📋 <b>Buyurtmalar</b>\n\n"
        f"Jami: {total} ta\n"
        f"🆕 Yangi: {new_count} ta\n\n"
        "Filtrni tanlang:",
        reply_markup=MainKeyboard.orders_filter(bot_id)
    )
    await call.answer()


@router.callback_query(F.data.startswith("orders_filter:"))
async def orders_filter_cb(call: CallbackQuery):
    """Filtrlangan buyurtmalarni ko'rsatadi."""
    parts = call.data.split(":")
    bot_id = int(parts[1])
    status = parts[2] if parts[2] != "all" else None

    orders = await get_bot_orders(bot_id, status=status, limit=10)

    if not orders:
        await call.answer("📋 Buyurtmalar topilmadi.", show_alert=True)
        return

    from utils.helpers import build_order_text, get_order_status_label
    from keyboards.main_kb import MainKeyboard

    for order in orders:
        text = build_order_text(order)
        await call.message.answer(
            text,
            reply_markup=MainKeyboard.order_status_change(order["id"], bot_id)
        )

    await call.answer()


@router.callback_query(F.data.startswith("ord_status:"))
async def order_status_cb(call: CallbackQuery):
    """Buyurtma holatini o'zgartiradi."""
    parts = call.data.split(":")
    order_id = int(parts[1])
    new_status = parts[2]
    bot_id = int(parts[3])

    from database.queries import update_order_status, get_order
    await update_order_status(order_id, new_status)

    from utils.helpers import get_order_status_label
    status_label = get_order_status_label(new_status)
    await call.answer(f"✅ Holat: {status_label}", show_alert=True)

    # Xaridorga xabar yuborish
    order = await get_order(order_id)
    if order:
        from utils.bot_manager import send_to_shop_bot
        msg = (
            f"📦 <b>Buyurtmangiz holati o'zgardi!</b>\n\n"
            f"Buyurtma #{order_id}\n"
            f"Yangi holat: <b>{status_label}</b>"
        )
        await send_to_shop_bot(bot_id, order["customer_id"], msg)


# ── Statistika ────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("bot_stats:"))
async def bot_stats_cb(call: CallbackQuery):
    """Bot statistikasi."""
    bot_id = int(call.data.split(":")[1])
    bot = await get_bot(bot_id)

    if not bot or bot["owner_id"] != call.from_user.id:
        await call.answer("❌ Ruxsat yo'q.", show_alert=True)
        return

    stats = await get_bot_stats(bot_id)
    text = (
        f"📊 <b>Statistika</b>\n"
        f"🤖 @{bot['bot_username'] or bot['bot_name']}\n\n"
        f"👥 Xaridorlar: <b>{stats['total_users']}</b>\n"
        f"📦 Mahsulotlar: <b>{stats['total_products']}</b>\n"
        f"📂 Kategoriyalar: <b>{stats['total_categories']}</b>\n"
        f"📋 Jami buyurtmalar: <b>{stats['total_orders']}</b>\n"
        f"🆕 Yangi buyurtmalar: <b>{stats['new_orders']}</b>\n"
        f"💰 Daromad: <b>{stats['revenue']:,.0f} so'm</b>"
    )
    await call.message.edit_text(text, reply_markup=MainKeyboard.stats_menu(bot_id))
    await call.answer()


@router.callback_query(F.data.startswith("export_orders:"))
async def export_orders_cb(call: CallbackQuery, user_data: dict):
    """Buyurtmalarni Excel ga eksport qiladi (faqat Premium)."""
    bot_id = int(call.data.split(":")[1])
    plan = user_data.get("plan", "free")

    if plan not in ("premium",):
        await call.answer(
            "❌ Bu funksiya faqat Premium foydalanuvchilar uchun!\n"
            "Rejangizni yangilang.",
            show_alert=True
        )
        return

    orders = await get_bot_orders(bot_id, limit=1000)
    if not orders:
        await call.answer("📋 Eksport qilish uchun buyurtmalar yo'q.", show_alert=True)
        return

    from utils.helpers import export_orders_to_excel
    from aiogram.types import BufferedInputFile

    try:
        buffer = await export_orders_to_excel(orders)
        file = BufferedInputFile(buffer.read(), filename="buyurtmalar.xlsx")
        await call.message.answer_document(file, caption="📊 Buyurtmalar hisoboti")
        await call.answer("✅ Eksport tayyor!", show_alert=True)
    except Exception as e:
        logger.error("Excel eksport xatosi: %s", e)
        await call.answer("❌ Eksport qilishda xato yuz berdi.", show_alert=True)


# ── Mahsulot qo'shish (main bot dan) ────────────────────────────────────────

class AddProductState(StatesGroup):
    name = State()
    price = State()
    description = State()
    photo = State()
    category = State()


@router.callback_query(F.data.startswith("add_product:"))
async def add_product_start_cb(call: CallbackQuery, state: FSMContext):
    """Mahsulot qo'shishni boshlaydi."""
    bot_id = int(call.data.split(":")[1])
    await state.set_state(AddProductState.name)
    await state.update_data(bot_id=bot_id)
    await call.message.answer(
        "➕ <b>Yangi mahsulot qo'shish</b>\n\n"
        "Mahsulot nomini kiriting:",
        reply_markup=MainKeyboard.cancel()
    )
    await call.answer()


@router.message(AddProductState.name)
async def add_product_name(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        data = await state.get_data()
        await state.clear()
        is_admin = config.is_super_admin(message.from_user.id)
        await message.answer("❌ Bekor qilindi.", reply_markup=MainKeyboard.main_menu(is_admin=is_admin))
        return
    await state.update_data(name=message.text)
    await state.set_state(AddProductState.price)
    await message.answer("💰 Mahsulot narxini kiriting (so'mda):", reply_markup=MainKeyboard.cancel())


@router.message(AddProductState.price)
async def add_product_price(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        is_admin = config.is_super_admin(message.from_user.id)
        await message.answer("❌ Bekor qilindi.", reply_markup=MainKeyboard.main_menu(is_admin=is_admin))
        return

    from utils.validators import validate_price
    price = validate_price(message.text)
    if price is None:
        await message.answer("❌ Noto'g'ri narx! Raqam kiriting:")
        return

    await state.update_data(price=price)
    await state.set_state(AddProductState.description)
    await message.answer(
        "📄 Mahsulot tavsifini kiriting (ixtiyoriy):",
        reply_markup=MainKeyboard.skip_cancel()
    )


@router.message(AddProductState.description)
async def add_product_desc(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        is_admin = config.is_super_admin(message.from_user.id)
        await message.answer("❌ Bekor qilindi.", reply_markup=MainKeyboard.main_menu(is_admin=is_admin))
        return

    desc = None if message.text == "⏩ O'tkazib yuborish" else message.text
    await state.update_data(description=desc)
    await state.set_state(AddProductState.photo)
    await message.answer(
        "🖼 Mahsulot rasmini yuboring (ixtiyoriy):",
        reply_markup=MainKeyboard.skip_cancel()
    )


@router.message(AddProductState.photo, F.photo)
async def add_product_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    await _add_product_ask_category(message, state)


@router.message(AddProductState.photo)
async def add_product_skip_photo(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        is_admin = config.is_super_admin(message.from_user.id)
        await message.answer("❌ Bekor qilindi.", reply_markup=MainKeyboard.main_menu(is_admin=is_admin))
        return
    await state.update_data(photo_id=None)
    await _add_product_ask_category(message, state)


async def _add_product_ask_category(message: Message, state: FSMContext):
    """Kategoriya tanlash yoki o'tkazib yuborish."""
    data = await state.get_data()
    bot_id = data.get("bot_id")
    cats = await get_categories(bot_id)

    if cats:
        await state.set_state(AddProductState.category)
        await message.answer(
            "📂 Kategoriya tanlang:",
            reply_markup=MainKeyboard.categories_list_for_product(cats, bot_id, 0)
        )
    else:
        await state.update_data(category_id=None)
        await _save_product(message, state)


@router.callback_query(AddProductState.category, F.data.startswith("set_cat:"))
async def add_product_cat_cb(call: CallbackQuery, state: FSMContext):
    parts = call.data.split(":")
    product_id_placeholder = int(parts[1])  # 0 for new product
    cat_id = int(parts[2]) if parts[2] != "0" else None
    bot_id = int(parts[3])
    await state.update_data(category_id=cat_id)
    await _save_product(call.message, state)
    await call.answer()


async def _save_product(message: Message, state: FSMContext):
    """Mahsulotni bazaga saqlaydi."""
    data = await state.get_data()
    from database.queries import create_product
    prod_id = await create_product(
        bot_id=data["bot_id"],
        name=data["name"],
        price=data["price"],
        description=data.get("description"),
        category_id=data.get("category_id"),
        photo_id=data.get("photo_id")
    )
    await state.clear()
    is_admin = config.is_super_admin(message.chat.id)
    await message.answer(
        f"✅ <b>Mahsulot qo'shildi!</b>\n\n"
        f"📦 {data['name']}\n"
        f"💰 {data['price']:,.0f} so'm",
        reply_markup=MainKeyboard.main_menu(is_admin=is_admin)
    )


# ── Kategoriya qo'shish ──────────────────────────────────────────────────────

class AddCategoryState(StatesGroup):
    name = State()
    icon = State()


@router.callback_query(F.data.startswith("add_cat:"))
async def add_cat_start_cb(call: CallbackQuery, state: FSMContext):
    bot_id = int(call.data.split(":")[1])
    await state.set_state(AddCategoryState.name)
    await state.update_data(bot_id=bot_id)
    await call.message.answer(
        "📂 <b>Yangi kategoriya qo'shish</b>\n\n"
        "Kategoriya nomini kiriting:",
        reply_markup=MainKeyboard.cancel()
    )
    await call.answer()


@router.message(AddCategoryState.name)
async def add_cat_name(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        is_admin = config.is_super_admin(message.from_user.id)
        await message.answer("❌ Bekor qilindi.", reply_markup=MainKeyboard.main_menu(is_admin=is_admin))
        return
    await state.update_data(name=message.text)
    await state.set_state(AddCategoryState.icon)
    await message.answer(
        "📌 Kategoriya ikonkasini kiriting (masalan: 🍎 🥗 👗 📱)\n"
        "Yoki o'tkazib yuborish:",
        reply_markup=MainKeyboard.skip_cancel()
    )


@router.message(AddCategoryState.icon)
async def add_cat_icon(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        is_admin = config.is_super_admin(message.from_user.id)
        await message.answer("❌ Bekor qilindi.", reply_markup=MainKeyboard.main_menu(is_admin=is_admin))
        return

    icon = "📦" if message.text == "⏩ O'tkazib yuborish" else message.text
    data = await state.get_data()
    bot_id = data.get("bot_id")

    from database.queries import create_category
    await create_category(bot_id, data["name"], icon)
    await state.clear()
    is_admin = config.is_super_admin(message.from_user.id)
    await message.answer(
        f"✅ Kategoriya qo'shildi: {icon} {data['name']}",
        reply_markup=MainKeyboard.main_menu(is_admin=is_admin)
    )
