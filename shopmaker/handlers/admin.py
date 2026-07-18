"""
Super Admin panel handlerlari.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import config
from database.queries import (
    get_user, get_all_users, count_users_by_plan, get_global_stats,
    set_user_plan, reset_user_plan, update_user, get_user_bots,
    delete_bot, get_payment, get_pending_payments, update_payment,
    get_setting, set_setting, get_all_promos, create_promo,
    get_logs, add_log, get_all_active_bots, get_bot, get_bot_stats
)
from filters.admin import IsSuperAdmin
from keyboards.admin_kb import AdminKeyboard
from keyboards.main_kb import MainKeyboard
from utils.helpers import format_price, format_date, get_plan_label, paginate, mention_user
from utils.bot_manager import stop_shop_bot, is_bot_running, get_active_bot_count

logger = logging.getLogger(__name__)
router = Router()
router.message.filter(IsSuperAdmin())
router.callback_query.filter(IsSuperAdmin())


class AdminState(StatesGroup):
    # Foydalanuvchi qidirish
    search_user = State()
    # Reja berish
    give_plan_days = State()
    give_plan_user = State()
    # Bloklash
    block_user_id = State()
    unblock_user_id = State()
    # Bot o'chirish
    delete_bot_id = State()
    # Broadcast
    broadcast_msg = State()
    broadcast_confirm = State()
    # Narx o'zgartirish
    set_price = State()
    set_days = State()
    # Promo kod
    promo_code_text = State()
    promo_days_input = State()
    promo_max_uses = State()
    # Foydalanuvchi ID
    user_id_input = State()


# ── Admin panel kirish ───────────────────────────────────────────────────────

@router.message(F.text == "👑 Admin panel")
async def admin_panel(message: Message, state: FSMContext):
    """Super admin panelini ochadi."""
    await state.clear()
    stats = await get_global_stats()
    active_bots = get_active_bot_count()

    text = (
        f"👑 <b>Super Admin Panel</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{stats['total_users']}</b>\n"
        f"🆓 Bepul: <b>{stats['free_users']}</b>\n"
        f"🌟 Comfort: <b>{stats['comfort_users']}</b>\n"
        f"💎 Premium: <b>{stats['premium_users']}</b>\n\n"
        f"🤖 Jami botlar: <b>{stats['total_bots']}</b>\n"
        f"▶️ Faol botlar: <b>{active_bots}</b>\n"
        f"📋 Jami buyurtmalar: <b>{stats['total_orders']}</b>"
    )
    await message.answer(text, reply_markup=AdminKeyboard.main_panel())


@router.callback_query(F.data == "sa_main")
async def sa_main_cb(call: CallbackQuery, state: FSMContext):
    """Admin panelga qaytish."""
    await state.clear()
    stats = await get_global_stats()
    active_bots = get_active_bot_count()

    text = (
        f"👑 <b>Super Admin Panel</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{stats['total_users']}</b>\n"
        f"🆓 Bepul: <b>{stats['free_users']}</b> | "
        f"🌟 Comfort: <b>{stats['comfort_users']}</b> | "
        f"💎 Premium: <b>{stats['premium_users']}</b>\n\n"
        f"🤖 Jami botlar: <b>{stats['total_bots']}</b> | "
        f"▶️ Faol: <b>{active_bots}</b>"
    )
    await call.message.edit_text(text, reply_markup=AdminKeyboard.main_panel())
    await call.answer()


# ── Statistika ────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "sa_stats")
async def sa_stats_cb(call: CallbackQuery):
    """Batafsil statistika."""
    stats = await get_global_stats()
    active_bots = get_active_bot_count()

    text = (
        f"📊 <b>Tizim statistikasi</b>\n\n"
        f"👥 <b>Foydalanuvchilar:</b>\n"
        f"  Jami: {stats['total_users']}\n"
        f"  🆓 Bepul: {stats['free_users']}\n"
        f"  🌟 Comfort: {stats['comfort_users']}\n"
        f"  💎 Premium: {stats['premium_users']}\n\n"
        f"🤖 <b>Botlar:</b>\n"
        f"  Jami: {stats['total_bots']}\n"
        f"  Faol: {active_bots}\n\n"
        f"📋 <b>Buyurtmalar:</b> {stats['total_orders']}\n"
        f"💳 <b>To'lovlar:</b> {stats['total_payments']}"
    )
    await call.message.edit_text(text, reply_markup=AdminKeyboard.back_to_admin())
    await call.answer()


# ── Foydalanuvchilar ─────────────────────────────────────────────────────────

@router.callback_query(F.data == "sa_users")
@router.callback_query(F.data.startswith("sa_users_page:"))
async def sa_users_cb(call: CallbackQuery):
    """Foydalanuvchilar ro'yxati."""
    page = 1
    if "page:" in call.data:
        page = int(call.data.split(":")[1])

    users = await get_all_users(limit=10, offset=(page - 1) * 10)
    from database.queries import get_total_users
    total = await get_total_users()
    total_pages = max(1, (total + 9) // 10)

    await call.message.edit_text(
        f"👥 <b>Foydalanuvchilar</b> ({total} ta) — Sahifa {page}/{total_pages}",
        reply_markup=AdminKeyboard.users_list(users, page, total_pages)
    )
    await call.answer()


@router.callback_query(F.data.startswith("sa_user:"))
async def sa_user_detail(call: CallbackQuery):
    """Foydalanuvchi ma'lumotlari."""
    user_id = int(call.data.split(":")[1])
    user = await get_user(user_id)

    if not user:
        await call.answer("❌ Foydalanuvchi topilmadi.", show_alert=True)
        return

    bots = await get_user_bots(user_id)
    plan = get_plan_label(user["plan"])
    expires = format_date(user.get("plan_expires_at"))
    blocked = "🚫 Bloklangan" if user["is_blocked"] else "✅ Faol"

    text = (
        f"👤 <b>Foydalanuvchi ma'lumotlari</b>\n\n"
        f"Ismi: {user['full_name']}\n"
        f"Username: @{user['username'] or '—'}\n"
        f"ID: <code>{user['id']}</code>\n"
        f"Holat: {blocked}\n"
        f"Reja: {plan}\n"
    )
    if user["plan"] != "free":
        text += f"Tugash: {expires}\n"
    text += f"Botlar: {len(bots)} ta\n"
    text += f"Ro'yxat sanasi: {format_date(user['created_at'])}"

    await call.message.edit_text(
        text,
        reply_markup=AdminKeyboard.user_actions(user_id, bool(user["is_blocked"]), user["plan"])
    )
    await call.answer()


@router.callback_query(F.data.startswith("sa_block:"))
async def sa_block_user_cb(call: CallbackQuery):
    """Foydalanuvchini bloklaydi."""
    user_id = int(call.data.split(":")[1])
    await update_user(user_id, is_blocked=1)
    await add_log("user_blocked", user_id=call.from_user.id, detail=f"target={user_id}")
    await call.answer(f"🚫 Foydalanuvchi #{user_id} bloklandi.", show_alert=True)
    await sa_user_detail(call)


@router.callback_query(F.data.startswith("sa_unblock:"))
async def sa_unblock_user_cb(call: CallbackQuery):
    """Foydalanuvchini blokdan chiqaradi."""
    user_id = int(call.data.split(":")[1])
    await update_user(user_id, is_blocked=0)
    await add_log("user_unblocked", user_id=call.from_user.id, detail=f"target={user_id}")
    await call.answer(f"✅ Foydalanuvchi #{user_id} blokdan chiqarildi.", show_alert=True)
    await sa_user_detail(call)


# ── Reja berish / olib tashlash ───────────────────────────────────────────────

@router.callback_query(F.data.startswith("sa_give_prem:"))
async def sa_give_premium_cb(call: CallbackQuery, state: FSMContext):
    """Foydalanuvchiga premium beradi."""
    user_id = int(call.data.split(":")[1])
    days = int(await get_setting("premium_days", "30"))
    await set_user_plan(user_id, "premium", days, given_by=call.from_user.id)
    await call.answer(f"✅ Premium berildi ({days} kun)!", show_alert=True)

    # Foydalanuvchiga xabar yuboradi
    try:
        await call.bot.send_message(
            user_id,
            f"🎉 <b>Tabriklaymiz!</b>\n\n"
            f"💎 Premium reja {days} kunlik berildi!\n"
            f"Barcha premium funksiyalar faollashdi.",
            parse_mode="HTML"
        )
    except Exception:
        pass

    await sa_user_detail(call)


@router.callback_query(F.data.startswith("sa_give_comf:"))
async def sa_give_comfort_cb(call: CallbackQuery):
    """Foydalanuvchiga comfort beradi."""
    user_id = int(call.data.split(":")[1])
    days = int(await get_setting("comfort_days", "90"))
    await set_user_plan(user_id, "comfort", days, given_by=call.from_user.id)
    await call.answer(f"✅ Comfort berildi ({days} kun)!", show_alert=True)

    try:
        await call.bot.send_message(
            user_id,
            f"🎉 <b>Tabriklaymiz!</b>\n\n"
            f"🌟 Comfort reja {days} kunlik berildi!",
            parse_mode="HTML"
        )
    except Exception:
        pass

    await sa_user_detail(call)


@router.callback_query(F.data.startswith("sa_rm_plan:"))
async def sa_remove_plan_cb(call: CallbackQuery):
    """Foydalanuvchi rejasini olib tashlaydi."""
    user_id = int(call.data.split(":")[1])
    await reset_user_plan(user_id)
    await add_log("plan_removed", user_id=call.from_user.id, detail=f"target={user_id}")
    await call.answer(f"✅ Reja olib tashlandi.", show_alert=True)

    try:
        await call.bot.send_message(
            user_id,
            "📢 Rejangiz bekor qilindi. Bepul rejaga o'tdingiz.",
            parse_mode="HTML"
        )
    except Exception:
        pass

    await sa_user_detail(call)


# ── Admin paneldan reja berish (ID bo'yicha) ──────────────────────────────────

@router.callback_query(F.data == "sa_give_premium")
async def sa_give_premium_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.user_id_input)
    await state.update_data(action="give_premium")
    await call.message.answer(
        "💎 Premium berish\n\nFoydalanuvchi IDini kiriting:",
        reply_markup=MainKeyboard.cancel()
    )
    await call.answer()


@router.callback_query(F.data == "sa_give_comfort")
async def sa_give_comfort_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.user_id_input)
    await state.update_data(action="give_comfort")
    await call.message.answer(
        "🌟 Comfort berish\n\nFoydalanuvchi IDini kiriting:",
        reply_markup=MainKeyboard.cancel()
    )
    await call.answer()


@router.callback_query(F.data == "sa_remove_plan")
async def sa_remove_plan_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.user_id_input)
    await state.update_data(action="remove_plan")
    await call.message.answer(
        "❌ Rejani olib tashlash\n\nFoydalanuvchi IDini kiriting:",
        reply_markup=MainKeyboard.cancel()
    )
    await call.answer()


@router.callback_query(F.data == "sa_block_user")
async def sa_block_user_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.user_id_input)
    await state.update_data(action="block")
    await call.message.answer(
        "🚫 Foydalanuvchini bloklash\n\nFoydalanuvchi IDini kiriting:",
        reply_markup=MainKeyboard.cancel()
    )
    await call.answer()


@router.callback_query(F.data == "sa_unblock_user")
async def sa_unblock_user_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.user_id_input)
    await state.update_data(action="unblock")
    await call.message.answer(
        "✅ Foydalanuvchini blokdan chiqarish\n\nFoydalanuvchi IDini kiriting:",
        reply_markup=MainKeyboard.cancel()
    )
    await call.answer()


@router.callback_query(F.data == "sa_delete_bot")
async def sa_delete_bot_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.user_id_input)
    await state.update_data(action="delete_bot")
    await call.message.answer(
        "🗑 Bot o'chirish\n\nBot IDini kiriting:",
        reply_markup=MainKeyboard.cancel()
    )
    await call.answer()


@router.message(AdminState.user_id_input)
async def sa_user_id_input(message: Message, state: FSMContext):
    """Foydalanuvchi ID bo'yicha amalni bajaradi."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        is_admin = config.is_super_admin(message.from_user.id)
        await message.answer("❌ Bekor qilindi.", reply_markup=MainKeyboard.main_menu(is_admin=is_admin))
        return

    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Noto'g'ri ID! Raqam kiriting:")
        return

    data = await state.get_data()
    action = data.get("action")
    is_admin = config.is_super_admin(message.from_user.id)

    if action == "give_premium":
        user = await get_user(target_id)
        if not user:
            await message.answer("❌ Foydalanuvchi topilmadi.")
            return
        days = int(await get_setting("premium_days", "30"))
        await set_user_plan(target_id, "premium", days, given_by=message.from_user.id)
        await message.answer(
            f"✅ {user['full_name']} ga Premium berildi ({days} kun)!",
            reply_markup=MainKeyboard.main_menu(is_admin=is_admin)
        )
        try:
            await message.bot.send_message(target_id, f"🎉 Premium reja {days} kun berildi!")
        except Exception:
            pass

    elif action == "give_comfort":
        user = await get_user(target_id)
        if not user:
            await message.answer("❌ Foydalanuvchi topilmadi.")
            return
        days = int(await get_setting("comfort_days", "90"))
        await set_user_plan(target_id, "comfort", days, given_by=message.from_user.id)
        await message.answer(
            f"✅ {user['full_name']} ga Comfort berildi ({days} kun)!",
            reply_markup=MainKeyboard.main_menu(is_admin=is_admin)
        )

    elif action == "remove_plan":
        await reset_user_plan(target_id)
        await message.answer(f"✅ ID {target_id} ning rejasi olib tashlandi.", reply_markup=MainKeyboard.main_menu(is_admin=is_admin))

    elif action == "block":
        await update_user(target_id, is_blocked=1)
        await message.answer(f"🚫 ID {target_id} bloklandi.", reply_markup=MainKeyboard.main_menu(is_admin=is_admin))

    elif action == "unblock":
        await update_user(target_id, is_blocked=0)
        await message.answer(f"✅ ID {target_id} blokdan chiqarildi.", reply_markup=MainKeyboard.main_menu(is_admin=is_admin))

    elif action == "delete_bot":
        bot = await get_bot(target_id)
        if not bot:
            await message.answer("❌ Bot topilmadi.")
            return
        await stop_shop_bot(target_id)
        await delete_bot(target_id)
        await message.answer(f"✅ Bot #{target_id} o'chirildi.", reply_markup=MainKeyboard.main_menu(is_admin=is_admin))

    await state.clear()
    await add_log(action, user_id=message.from_user.id, detail=f"target={target_id}")


# ── Foydalanuvchi botlari ─────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("sa_user_bots:"))
async def sa_user_bots_cb(call: CallbackQuery):
    """Foydalanuvchi botlari ro'yxati."""
    user_id = int(call.data.split(":")[1])
    bots = await get_user_bots(user_id)

    if not bots:
        await call.answer("Bu foydalanuvchining boti yo'q.", show_alert=True)
        return

    await call.message.edit_text(
        f"🤖 Foydalanuvchi #{user_id} botlari:",
        reply_markup=AdminKeyboard.user_bots_list(bots, user_id)
    )
    await call.answer()


@router.callback_query(F.data.startswith("sa_del_bot:"))
async def sa_del_bot_confirm_cb(call: CallbackQuery):
    """Bot o'chirish tasdiqlash."""
    parts = call.data.split(":")
    bot_id = int(parts[1])
    user_id = int(parts[2])
    bot = await get_bot(bot_id)

    if not bot:
        await call.answer("❌ Bot topilmadi.", show_alert=True)
        return

    await call.message.edit_text(
        f"⚠️ @{bot['bot_username'] or bot['bot_name']} botini o'chirmoqchimisiz?",
        reply_markup=AdminKeyboard.del_bot_confirm(bot_id, user_id)
    )
    await call.answer()


@router.callback_query(F.data.startswith("sa_del_bot_ok:"))
async def sa_del_bot_ok_cb(call: CallbackQuery):
    """Admin tomonidan bot o'chirish."""
    parts = call.data.split(":")
    bot_id = int(parts[1])
    user_id = int(parts[2])

    await stop_shop_bot(bot_id)
    await delete_bot(bot_id)
    await add_log("admin_delete_bot", user_id=call.from_user.id, detail=f"bot_id={bot_id}")
    await call.answer("✅ Bot o'chirildi!", show_alert=True)
    await call.message.edit_text(f"✅ Bot #{bot_id} o'chirildi.")


# ── To'lovlar ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "sa_payments")
async def sa_payments_cb(call: CallbackQuery):
    """Kutilayotgan to'lovlar."""
    payments = await get_pending_payments()

    if not payments:
        await call.message.edit_text(
            "💳 Kutilayotgan to'lovlar yo'q.",
            reply_markup=AdminKeyboard.back_to_admin()
        )
        return

    await call.message.edit_text(
        f"💳 <b>Kutilayotgan to'lovlar</b> ({len(payments)} ta):",
        reply_markup=AdminKeyboard.payments_list(payments)
    )
    await call.answer()


@router.callback_query(F.data.startswith("sa_pay:"))
async def sa_pay_detail_cb(call: CallbackQuery):
    """To'lov tafsilotlari."""
    pay_id = int(call.data.split(":")[1])
    pay = await get_payment(pay_id)

    if not pay:
        await call.answer("❌ To'lov topilmadi.", show_alert=True)
        return

    user = await get_user(pay["user_id"])
    text = (
        f"💳 <b>To'lov #{pay_id}</b>\n\n"
        f"👤 Foydalanuvchi: {user['full_name'] if user else '—'} "
        f"(ID: {pay['user_id']})\n"
        f"📦 Reja: {pay['plan'].capitalize()}\n"
        f"💰 Summa: {format_price(pay['amount'])}\n"
        f"💳 Usul: {pay['method']}\n"
        f"📊 Holat: {pay['status']}\n"
        f"📅 Sana: {format_date(pay['created_at'])}"
    )
    if pay.get("admin_note"):
        text += f"\n📝 Izoh: {pay['admin_note']}"

    await call.message.edit_text(text, reply_markup=AdminKeyboard.payment_actions(pay_id))
    await call.answer()


@router.callback_query(F.data.startswith("sa_pay_approve:"))
async def sa_pay_approve_cb(call: CallbackQuery):
    """To'lovni tasdiqlaydi va rejani beradi."""
    pay_id = int(call.data.split(":")[1])
    pay = await get_payment(pay_id)

    if not pay:
        await call.answer("❌ To'lov topilmadi.", show_alert=True)
        return

    # To'lovni tasdiqlaydi
    await update_payment(pay_id, status="paid", admin_note="Admin tomonidan tasdiqlandi")

    # Rejani beradi
    days = int(await get_setting(f"{pay['plan']}_days", "30"))
    await set_user_plan(
        pay["user_id"], pay["plan"], days,
        given_by=call.from_user.id,
        note=f"payment:{pay_id}"
    )

    await add_log("payment_approved", user_id=call.from_user.id, detail=f"pay_id={pay_id}")
    await call.answer("✅ To'lov tasdiqlandi!", show_alert=True)

    # Foydalanuvchiga xabar
    try:
        await call.bot.send_message(
            pay["user_id"],
            f"✅ <b>To'lovingiz tasdiqlandi!</b>\n\n"
            f"💎 Reja: {get_plan_label(pay['plan'])}\n"
            f"📅 Muddat: {days} kun\n\n"
            f"Barcha funksiyalar faollashtirildi!",
            parse_mode="HTML"
        )
    except Exception:
        pass

    await call.message.edit_text(f"✅ To'lov #{pay_id} tasdiqlandi!")


@router.callback_query(F.data.startswith("sa_pay_reject:"))
async def sa_pay_reject_cb(call: CallbackQuery):
    """To'lovni rad etadi."""
    pay_id = int(call.data.split(":")[1])
    pay = await get_payment(pay_id)

    if not pay:
        await call.answer("❌ To'lov topilmadi.", show_alert=True)
        return

    await update_payment(pay_id, status="failed", admin_note="Admin tomonidan rad etildi")
    await call.answer("❌ To'lov rad etildi.", show_alert=True)

    try:
        await call.bot.send_message(
            pay["user_id"],
            f"❌ Afsuski, to'lovingiz tasdiqlanmadi.\n"
            f"Muammo uchun @ShopMakerUzBot ga murojaat qiling.",
            parse_mode="HTML"
        )
    except Exception:
        pass

    await call.message.edit_text(f"❌ To'lov #{pay_id} rad etildi.")


# ── Narxlar ───────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "sa_prices")
async def sa_prices_cb(call: CallbackQuery):
    """Narxlar boshqaruvi."""
    pp = await get_setting("premium_price", "10000")
    pd = await get_setting("premium_days", "30")
    cp = await get_setting("comfort_price", "5000")
    cd = await get_setting("comfort_days", "90")

    text = (
        f"💰 <b>Joriy narxlar</b>\n\n"
        f"💎 Premium: {format_price(float(pp))} / {pd} kun\n"
        f"🌟 Comfort: {format_price(float(cp))} / {cd} kun"
    )
    await call.message.edit_text(text, reply_markup=AdminKeyboard.prices_menu())
    await call.answer()


@router.callback_query(F.data.startswith("sa_set_"))
async def sa_set_price_start(call: CallbackQuery, state: FSMContext):
    """Narx/kun o'zgartirish."""
    action = call.data.replace("sa_set_", "")
    labels = {
        "premium_price": "💎 Premium narxi (so'mda)",
        "premium_days": "💎 Premium muddati (kunlarda)",
        "comfort_price": "🌟 Comfort narxi (so'mda)",
        "comfort_days": "🌟 Comfort muddati (kunlarda)",
    }
    label = labels.get(action, action)
    await state.set_state(AdminState.set_price)
    await state.update_data(setting_key=action)
    await call.message.answer(
        f"✏️ {label}\n\nYangi qiymatni kiriting:",
        reply_markup=MainKeyboard.cancel()
    )
    await call.answer()


@router.message(AdminState.set_price)
async def sa_set_price_save(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        is_admin = config.is_super_admin(message.from_user.id)
        await message.answer("❌ Bekor qilindi.", reply_markup=MainKeyboard.main_menu(is_admin=is_admin))
        return

    try:
        val = int(message.text.strip())
        if val <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Noto'g'ri qiymat! Musbat son kiriting:")
        return

    data = await state.get_data()
    key = data.get("setting_key")
    await set_setting(key, str(val))
    await state.clear()

    is_admin = config.is_super_admin(message.from_user.id)
    await message.answer(f"✅ {key} = {val} ga o'zgartirildi.", reply_markup=MainKeyboard.main_menu(is_admin=is_admin))
    await add_log("setting_changed", user_id=message.from_user.id, detail=f"{key}={val}")


# ── Ro'yxatdan o'tish ─────────────────────────────────────────────────────────

@router.callback_query(F.data == "sa_registration")
async def sa_registration_cb(call: CallbackQuery):
    """Ro'yxatdan o'tishni boshqarish."""
    enabled = await get_setting("registration_enabled", "1") == "1"
    status = "🟢 Yoqilgan" if enabled else "🔴 O'chirilgan"
    await call.message.edit_text(
        f"🔒 <b>Ro'yxatdan o'tish</b>\n\nHolat: {status}",
        reply_markup=AdminKeyboard.registration_toggle(enabled)
    )
    await call.answer()


@router.callback_query(F.data == "sa_reg_enable")
async def sa_reg_enable(call: CallbackQuery):
    await set_setting("registration_enabled", "1")
    await call.answer("✅ Ro'yxatdan o'tish yoqildi!", show_alert=True)
    await sa_registration_cb(call)


@router.callback_query(F.data == "sa_reg_disable")
async def sa_reg_disable(call: CallbackQuery):
    await set_setting("registration_enabled", "0")
    await call.answer("🔒 Ro'yxatdan o'tish o'chirildi!", show_alert=True)
    await sa_registration_cb(call)


# ── Promo kodlar ──────────────────────────────────────────────────────────────

@router.callback_query(F.data == "sa_promo")
async def sa_promo_cb(call: CallbackQuery):
    """Promo kodlar menyusi."""
    await call.message.edit_text(
        "🎁 <b>Promo kodlar</b>",
        reply_markup=AdminKeyboard.promo_menu()
    )
    await call.answer()


@router.callback_query(F.data == "sa_list_promos")
async def sa_list_promos_cb(call: CallbackQuery):
    """Barcha promo kodlar."""
    promos = await get_all_promos()
    if not promos:
        await call.answer("Promo kodlar yo'q.", show_alert=True)
        return

    text = "🎁 <b>Promo kodlar:</b>\n\n"
    for p in promos[:20]:
        status = "✅" if p["is_active"] else "❌"
        expires = format_date(p["expires_at"]) if p["expires_at"] else "Muddatsiz"
        text += (
            f"{status} <code>{p['code']}</code> — {get_plan_label(p['plan'])} "
            f"{p['days']} kun | {p['used_count']}/{p['max_uses']} marta | {expires}\n"
        )

    await call.message.edit_text(text, reply_markup=AdminKeyboard.back_to_admin())
    await call.answer()


@router.callback_query(F.data == "sa_create_promo")
async def sa_create_promo_cb(call: CallbackQuery, state: FSMContext):
    """Yangi promo kod yaratish."""
    await state.set_state(AdminState.promo_code_text)
    await call.message.answer(
        "🎁 <b>Yangi promo kod</b>\n\nPromo kod matnini kiriting (masalan: FREE30):",
        reply_markup=MainKeyboard.cancel()
    )
    await call.answer()


@router.message(AdminState.promo_code_text)
async def promo_code_text_input(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        is_admin = config.is_super_admin(message.from_user.id)
        await message.answer("❌ Bekor qilindi.", reply_markup=MainKeyboard.main_menu(is_admin=is_admin))
        return
    code = message.text.strip().upper()
    await state.update_data(promo_code=code)
    await message.answer(
        "📦 Qaysi reja uchun?",
        reply_markup=AdminKeyboard.promo_plan_select()
    )


@router.callback_query(F.data.startswith("promo_plan:"), AdminState.promo_code_text)
async def promo_plan_select(call: CallbackQuery, state: FSMContext):
    plan = call.data.split(":")[1]
    await state.update_data(promo_plan=plan)
    await state.set_state(AdminState.promo_days_input)
    await call.message.answer(
        "📅 Necha kunlik? (raqam kiriting):",
        reply_markup=MainKeyboard.cancel()
    )
    await call.answer()


@router.message(AdminState.promo_days_input)
async def promo_days_input(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        is_admin = config.is_super_admin(message.from_user.id)
        await message.answer("❌ Bekor qilindi.", reply_markup=MainKeyboard.main_menu(is_admin=is_admin))
        return
    try:
        days = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Raqam kiriting:")
        return
    await state.update_data(promo_days=days)
    await state.set_state(AdminState.promo_max_uses)
    await message.answer(
        "🔢 Necha marta ishlatish mumkin?",
        reply_markup=MainKeyboard.cancel()
    )


@router.message(AdminState.promo_max_uses)
async def promo_max_uses_input(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        is_admin = config.is_super_admin(message.from_user.id)
        await message.answer("❌ Bekor qilindi.", reply_markup=MainKeyboard.main_menu(is_admin=is_admin))
        return
    try:
        max_uses = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Raqam kiriting:")
        return

    data = await state.get_data()
    promo_id = await create_promo(
        code=data["promo_code"],
        plan=data["promo_plan"],
        days=data["promo_days"],
        max_uses=max_uses,
        created_by=message.from_user.id
    )
    await state.clear()
    is_admin = config.is_super_admin(message.from_user.id)
    await message.answer(
        f"✅ Promo kod yaratildi!\n\n"
        f"Kod: <code>{data['promo_code']}</code>\n"
        f"Reja: {get_plan_label(data['promo_plan'])}\n"
        f"Muddat: {data['promo_days']} kun\n"
        f"Ishlatish: {max_uses} marta",
        reply_markup=MainKeyboard.main_menu(is_admin=is_admin)
    )


# ── Global Broadcast ──────────────────────────────────────────────────────────

@router.callback_query(F.data == "sa_broadcast")
async def sa_broadcast_cb(call: CallbackQuery, state: FSMContext):
    """Global broadcast."""
    await state.set_state(AdminState.broadcast_msg)
    await call.message.answer(
        "📣 <b>Global Broadcast</b>\n\n"
        "Barcha foydalanuvchilarga yuboriladigan xabarni kiriting:",
        reply_markup=MainKeyboard.cancel()
    )
    await call.answer()


@router.message(AdminState.broadcast_msg)
async def sa_broadcast_msg(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        is_admin = config.is_super_admin(message.from_user.id)
        await message.answer("❌ Bekor qilindi.", reply_markup=MainKeyboard.main_menu(is_admin=is_admin))
        return

    await state.update_data(broadcast_text=message.text)
    await state.set_state(AdminState.broadcast_confirm)
    await message.answer(
        f"📣 Quyidagi xabar barcha foydalanuvchilarga yuboriladi:\n\n"
        f"{message.text}\n\n"
        "Tasdiqlaysizmi?",
        reply_markup=MainKeyboard.confirm_cancel()
    )


@router.callback_query(AdminState.broadcast_confirm, F.data == "confirm")
async def sa_broadcast_send(call: CallbackQuery, state: FSMContext):
    """Broadcastni yuboradi."""
    data = await state.get_data()
    text = data.get("broadcast_text", "")
    await state.clear()

    users = await get_all_users(limit=10000)
    sent = 0
    failed = 0

    progress_msg = await call.message.answer(f"⏳ Yuborilmoqda... 0/{len(users)}")

    import asyncio
    for i, user in enumerate(users):
        try:
            await call.bot.send_message(user["id"], text, parse_mode="HTML")
            sent += 1
        except Exception:
            failed += 1

        if (i + 1) % 50 == 0:
            try:
                await progress_msg.edit_text(f"⏳ Yuborilmoqda... {i+1}/{len(users)}")
            except Exception:
                pass

        await asyncio.sleep(0.05)

    await progress_msg.edit_text(
        f"✅ <b>Broadcast yakunlandi!</b>\n\n"
        f"✅ Yuborildi: {sent}\n"
        f"❌ Xato: {failed}"
    )
    await add_log("global_broadcast", user_id=call.from_user.id, detail=f"sent={sent},failed={failed}")
    await call.answer()


@router.callback_query(AdminState.broadcast_confirm, F.data == "cancel")
async def sa_broadcast_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer("❌ Broadcast bekor qilindi.")
    await call.answer()


# ── Tizim loglari ────────────────────────────────────────────────────────────

@router.callback_query(F.data == "sa_logs")
async def sa_logs_cb(call: CallbackQuery):
    """Tizim loglarini ko'rsatadi."""
    logs = await get_logs(limit=50)
    if not logs:
        await call.answer("Log yozuvlari yo'q.", show_alert=True)
        return

    text = "📋 <b>Oxirgi loglar:</b>\n\n"
    for log in logs[:20]:
        text += (
            f"[{format_date(log['created_at'])}] {log['level']}: "
            f"{log['action']}"
        )
        if log["user_id"]:
            text += f" (user:{log['user_id']})"
        text += "\n"

    await call.message.edit_text(text[:4000], reply_markup=AdminKeyboard.back_to_admin())
    await call.answer()


# ── Zaxira nusxa ──────────────────────────────────────────────────────────────

@router.callback_query(F.data == "sa_backup")
async def sa_backup_cb(call: CallbackQuery):
    """Ma'lumotlar bazasini zaxiralaydi."""
    import aiofiles
    from aiogram.types import FSInputFile

    db_path = config.DB_PATH
    try:
        backup_path = f"/tmp/shopmaker_backup_{int(__import__('time').time())}.db"
        async with aiofiles.open(db_path, "rb") as src:
            content = await src.read()
        async with aiofiles.open(backup_path, "wb") as dst:
            await dst.write(content)

        file = FSInputFile(backup_path, filename="shopmaker_backup.db")
        await call.message.answer_document(
            file,
            caption=f"💾 Ma'lumotlar bazasi zaxira nusxasi\n📅 {format_date(None) or 'hozir'}"
        )
        await add_log("backup_created", user_id=call.from_user.id)
        await call.answer("✅ Zaxira nusxa yuborildi!", show_alert=True)
    except Exception as e:
        logger.error("Backup xatosi: %s", e)
        await call.answer("❌ Zaxira qilishda xato yuz berdi.", show_alert=True)
