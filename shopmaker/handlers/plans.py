"""
Rejalar va promo kod handlerlari.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import config
from database.queries import (
    get_user, get_setting, get_promo, has_used_promo, use_promo, set_user_plan
)
from keyboards.main_kb import MainKeyboard
from utils.helpers import format_price, format_date, get_plan_label

logger = logging.getLogger(__name__)
router = Router()


class PromoState(StatesGroup):
    waiting_code = State()


# ── Rejalar menyusi ───────────────────────────────────────────────────────────

@router.message(F.text == "💎 Rejalar")
async def show_plans(message: Message, user_data: dict, state: FSMContext):
    """Rejalar menyusini ko'rsatadi."""
    await state.clear()

    premium_price = int(await get_setting("premium_price", "10000"))
    premium_days = int(await get_setting("premium_days", "30"))
    comfort_price = int(await get_setting("comfort_price", "5000"))
    comfort_days = int(await get_setting("comfort_days", "90"))

    current_plan = get_plan_label(user_data.get("plan", "free"))
    expires = format_date(user_data.get("plan_expires_at"))

    text = (
        f"💎 <b>Rejalar</b>\n\n"
        f"📦 Joriy reja: <b>{current_plan}</b>\n"
    )
    if user_data.get("plan") != "free":
        text += f"📅 Tugash sanasi: <b>{expires}</b>\n"

    text += (
        f"\n━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆓 <b>Bepul reja:</b>\n"
        f"  ✅ 1 ta bot\n"
        f"  ✅ Cheksiz mahsulotlar\n"
        f"  ✅ Cheksiz kategoriyalar\n"
        f"  ✅ Cheksiz buyurtmalar\n"
        f"  ✅ Savat tizimi\n"
        f"  ✅ Mahsulot qidirish\n"
        f"  ✅ Rasm, tavsif, narx\n"
        f"  ❌ «Powered by ShopMaker» mавжуд\n\n"

        f"🌟 <b>Comfort reja — {format_price(comfort_price)}/{comfort_days} kun:</b>\n"
        f"  ✅ Bepul rejanidagi barcha narsalar\n"
        f"  ✅ 1 ta bot\n"
        f"  ✅ Ko'proq mavzular\n"
        f"  ✅ Kengaytirilgan limitlar\n\n"

        f"💎 <b>Premium reja — {format_price(premium_price)}/{premium_days} kun:</b>\n"
        f"  ✅ 3 ta bot\n"
        f"  ✅ «Powered by ShopMaker» olib tashlanadi\n"
        f"  ✅ Premium mavzular\n"
        f"  ✅ Kengaytirilgan statistika\n"
        f"  ✅ Excel eksport\n"
        f"  ✅ Broadcast\n"
        f"  ✅ Premium nishon 💎\n"
    )

    await message.answer(text, reply_markup=MainKeyboard.plans_menu())


@router.callback_query(F.data == "plans")
async def plans_cb(call: CallbackQuery, user_data: dict):
    """Rejalar menyusiga qaytish."""
    premium_price = int(await get_setting("premium_price", "10000"))
    premium_days = int(await get_setting("premium_days", "30"))
    comfort_price = int(await get_setting("comfort_price", "5000"))
    comfort_days = int(await get_setting("comfort_days", "90"))

    text = (
        f"💎 <b>Rejalar</b>\n\n"
        f"🌟 Comfort: {format_price(comfort_price)}/{comfort_days} kun\n"
        f"💎 Premium: {format_price(premium_price)}/{premium_days} kun\n\n"
        "Rejani tanlang:"
    )
    await call.message.edit_text(text, reply_markup=MainKeyboard.plans_menu())
    await call.answer()


# ── To'lov usullari ──────────────────────────────────────────────────────────

@router.callback_query(F.data == "buy_premium")
async def buy_premium_cb(call: CallbackQuery):
    premium_price = int(await get_setting("premium_price", "10000"))
    premium_days = int(await get_setting("premium_days", "30"))
    await call.message.edit_text(
        f"💎 <b>Premium reja</b>\n\n"
        f"Narx: <b>{format_price(premium_price)}</b>\n"
        f"Muddat: <b>{premium_days} kun</b>\n\n"
        "To'lov usulini tanlang:",
        reply_markup=MainKeyboard.payment_methods("premium")
    )
    await call.answer()


@router.callback_query(F.data == "buy_comfort")
async def buy_comfort_cb(call: CallbackQuery):
    comfort_price = int(await get_setting("comfort_price", "5000"))
    comfort_days = int(await get_setting("comfort_days", "90"))
    await call.message.edit_text(
        f"🌟 <b>Comfort reja</b>\n\n"
        f"Narx: <b>{format_price(comfort_price)}</b>\n"
        f"Muddat: <b>{comfort_days} kun</b>\n\n"
        "To'lov usulini tanlang:",
        reply_markup=MainKeyboard.payment_methods("comfort")
    )
    await call.answer()


@router.callback_query(F.data.startswith("pay_click:"))
async def pay_click_cb(call: CallbackQuery):
    plan = call.data.split(":")[1]
    price = int(await get_setting(f"{plan}_price", "10000"))
    # Click merchant ID ni tekshiradi
    merchant_id = config.CLICK_MERCHANT_ID
    if not merchant_id:
        await call.answer("❌ Click to'lov hozirda mavjud emas.", show_alert=True)
        return

    # To'lov linkini yaratadi
    from database.queries import create_payment
    pay_id = await create_payment(call.from_user.id, plan, price, "click")
    click_url = (
        f"https://my.click.uz/services/pay"
        f"?service_id={config.CLICK_SERVICE_ID}"
        f"&merchant_id={merchant_id}"
        f"&amount={price}"
        f"&transaction_param={pay_id}"
    )

    await call.message.edit_text(
        f"💳 <b>Click orqali to'lov</b>\n\n"
        f"Reja: {plan.capitalize()}\n"
        f"Summa: {format_price(price)}\n\n"
        f"To'lov linkiga o'ting:\n{click_url}\n\n"
        f"To'lov #: <code>{pay_id}</code>\n"
        f"To'lovdan so'ng «Tekshirish» ni bosing:",
        reply_markup=MainKeyboard.check_payment(pay_id)
    )
    await call.answer()


@router.callback_query(F.data.startswith("pay_payme:"))
async def pay_payme_cb(call: CallbackQuery):
    plan = call.data.split(":")[1]
    price = int(await get_setting(f"{plan}_price", "10000"))
    merchant_id = config.PAYME_MERCHANT_ID
    if not merchant_id:
        await call.answer("❌ Payme to'lov hozirda mavjud emas.", show_alert=True)
        return

    from database.queries import create_payment
    pay_id = await create_payment(call.from_user.id, plan, price, "payme")
    import base64
    params_str = f"m={merchant_id};ac.order_id={pay_id};a={price * 100}"
    encoded = base64.b64encode(params_str.encode()).decode()
    payme_url = f"https://checkout.paycom.uz/{encoded}"

    await call.message.edit_text(
        f"💳 <b>Payme orqali to'lov</b>\n\n"
        f"Reja: {plan.capitalize()}\n"
        f"Summa: {format_price(price)}\n\n"
        f"To'lov linkiga o'ting:\n{payme_url}\n\n"
        f"To'lovdan so'ng «Tekshirish» ni bosing:",
        reply_markup=MainKeyboard.check_payment(pay_id)
    )
    await call.answer()


@router.callback_query(F.data.startswith("pay_uzum:"))
async def pay_uzum_cb(call: CallbackQuery):
    plan = call.data.split(":")[1]
    price = int(await get_setting(f"{plan}_price", "10000"))

    from database.queries import create_payment
    pay_id = await create_payment(call.from_user.id, plan, price, "uzum")
    await call.message.edit_text(
        f"💳 <b>Uzum Bank orqali to'lov</b>\n\n"
        f"Reja: {plan.capitalize()}\n"
        f"Summa: {format_price(price)}\n\n"
        f"Uzum Bank to'lov tizimi tez orada ulanadi.\n"
        f"Hozircha qo'lda to'lov usulidan foydalaning.",
        reply_markup=MainKeyboard.check_payment(pay_id)
    )
    await call.answer()


@router.callback_query(F.data.startswith("pay_manual:"))
async def pay_manual_cb(call: CallbackQuery):
    """Qo'lda to'lov."""
    plan = call.data.split(":")[1]
    price = int(await get_setting(f"{plan}_price", "10000"))
    support = await get_setting("support_username", "ShopMakerUzBot")

    from database.queries import create_payment
    pay_id = await create_payment(call.from_user.id, plan, price, "manual")

    await call.message.edit_text(
        f"💵 <b>Qo'lda to'lov</b>\n\n"
        f"Reja: {plan.capitalize()}\n"
        f"Summa: {format_price(price)}\n\n"
        f"Quyidagi ma'lumotlarga pul o'tkazing va chekni adminga yuboring:\n\n"
        f"👤 Admin: @{support}\n"
        f"📝 To'lov ID: <code>{pay_id}</code>\n\n"
        f"⚠️ To'lov IDni adminga yuboring, tekshirib reja faollashtiriladi.",
        reply_markup=MainKeyboard.check_payment(pay_id)
    )
    await call.answer()


@router.callback_query(F.data.startswith("check_payment:"))
async def check_payment_cb(call: CallbackQuery):
    """To'lov holatini tekshiradi."""
    pay_id = int(call.data.split(":")[1])
    from database.queries import get_payment
    pay = await get_payment(pay_id)

    if not pay:
        await call.answer("❌ To'lov topilmadi.", show_alert=True)
        return

    if pay["status"] == "paid":
        await call.message.edit_text(
            f"✅ <b>To'lov tasdiqlandi!</b>\n\n"
            f"Reja: {pay['plan'].capitalize()}\n"
            f"Summa: {format_price(pay['amount'])}\n\n"
            f"Rejangiz faollashtirildi!"
        )
    elif pay["status"] == "pending":
        await call.answer(
            "⏳ To'lov hali tekshirilmadi. Admin tekshirib javob beradi.",
            show_alert=True
        )
    elif pay["status"] == "failed":
        await call.answer("❌ To'lov rad etildi.", show_alert=True)


@router.callback_query(F.data.startswith("cancel_payment:"))
async def cancel_payment_cb(call: CallbackQuery):
    """To'lovni bekor qiladi."""
    pay_id = int(call.data.split(":")[1])
    from database.queries import update_payment
    await update_payment(pay_id, status="failed")
    await call.message.edit_text("❌ To'lov bekor qilindi.")
    await call.answer()


# ── Promo kod ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "promo_code")
async def promo_code_cb(call: CallbackQuery, state: FSMContext):
    """Promo kod kiritish."""
    await state.set_state(PromoState.waiting_code)
    await call.message.answer(
        "🎁 <b>Promo kod</b>\n\nPromo kodni kiriting:",
        reply_markup=MainKeyboard.cancel()
    )
    await call.answer()


@router.message(PromoState.waiting_code)
async def process_promo_code(message: Message, state: FSMContext, user_data: dict):
    """Promo kodni tekshiradi va rejani beradi."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        is_admin = config.is_super_admin(message.from_user.id)
        await message.answer("❌ Bekor qilindi.", reply_markup=MainKeyboard.main_menu(is_admin=is_admin))
        return

    from utils.validators import validate_promo_code
    code = validate_promo_code(message.text)
    promo = await get_promo(code)

    if not promo:
        await message.answer("❌ Noto'g'ri yoki muddati o'tgan promo kod!")
        return

    if promo["used_count"] >= promo["max_uses"]:
        await message.answer("❌ Bu promo kod ishlatib bo'lindi!")
        return

    if await has_used_promo(promo["id"], message.from_user.id):
        await message.answer("❌ Siz bu promo kodni avval ishlatgansiz!")
        return

    # Promo kodni ishlatadi va rejani beradi
    await use_promo(promo["id"], message.from_user.id)
    await set_user_plan(
        message.from_user.id,
        promo["plan"],
        promo["days"],
        note=f"promo:{code}"
    )
    await state.clear()

    is_admin = config.is_super_admin(message.from_user.id)
    await message.answer(
        f"✅ <b>Promo kod muvaffaqiyatli ishlatildi!</b>\n\n"
        f"🎁 Reja: {get_plan_label(promo['plan'])}\n"
        f"📅 Muddat: {promo['days']} kun",
        reply_markup=MainKeyboard.main_menu(is_admin=is_admin)
    )
