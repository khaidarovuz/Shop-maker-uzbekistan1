"""
Shop bot — admin sozlamalari handlerlari.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.queries import update_bot
from keyboards.shop_kb import ShopKeyboard

logger = logging.getLogger(__name__)
router = Router()


class ShopSettingsState(StatesGroup):
    welcome = State()
    about = State()
    contact = State()


def _is_admin(user_id: int, bot_data: dict) -> bool:
    return user_id == bot_data.get("owner_id")


def _get_footer(bot_data: dict) -> str:
    if bot_data.get("footer_enabled", 1):
        return "\n\n<i>Powered by @ShopMakerUzBot</i>"
    return ""


@router.message(F.text == "⚙️ Sozlamalar")
async def shop_settings_menu(message: Message, bot_id: int, bot_data: dict):
    """Sozlamalar menyusi."""
    if not _is_admin(message.from_user.id, bot_data):
        return

    footer = _get_footer(bot_data)
    await message.answer(
        "⚙️ <b>Sozlamalar</b>\n\nNimani o'zgartirishni xohlaysiz?" + footer,
        reply_markup=ShopKeyboard.admin_settings()
    )


@router.callback_query(F.data == "admin_set_welcome")
async def set_welcome_cb(call: CallbackQuery, bot_id: int, bot_data: dict, state: FSMContext):
    if not _is_admin(call.from_user.id, bot_data):
        return
    await state.set_state(ShopSettingsState.welcome)
    await call.message.answer(
        "👋 Xush kelibsiz matnini kiriting:\n"
        "(Foydalanuvchi /start berganda ko'rsatiladi)",
        reply_markup=ShopKeyboard.cancel()
    )
    await call.answer()


@router.message(ShopSettingsState.welcome)
async def set_welcome_save(message: Message, bot_id: int, bot_data: dict, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=ShopKeyboard.admin_main(bot_id))
        return
    await update_bot(bot_id, welcome_text=message.text)
    await state.clear()
    await message.answer("✅ Xush kelibsiz matni saqlandi!", reply_markup=ShopKeyboard.admin_main(bot_id))


@router.callback_query(F.data == "admin_set_about")
async def set_about_cb(call: CallbackQuery, bot_id: int, bot_data: dict, state: FSMContext):
    if not _is_admin(call.from_user.id, bot_data):
        return
    await state.set_state(ShopSettingsState.about)
    await call.message.answer(
        "ℹ️ Bot haqida ma'lumot kiriting:",
        reply_markup=ShopKeyboard.cancel()
    )
    await call.answer()


@router.message(ShopSettingsState.about)
async def set_about_save(message: Message, bot_id: int, bot_data: dict, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=ShopKeyboard.admin_main(bot_id))
        return
    await update_bot(bot_id, about_text=message.text)
    await state.clear()
    await message.answer("✅ Bot haqida ma'lumot saqlandi!", reply_markup=ShopKeyboard.admin_main(bot_id))


@router.callback_query(F.data == "admin_set_contact")
async def set_contact_cb(call: CallbackQuery, bot_id: int, bot_data: dict, state: FSMContext):
    if not _is_admin(call.from_user.id, bot_data):
        return
    await state.set_state(ShopSettingsState.contact)
    await call.message.answer(
        "📞 Aloqa ma'lumotini kiriting:\n(Masalan: @username yoki +998901234567)",
        reply_markup=ShopKeyboard.cancel()
    )
    await call.answer()


@router.message(ShopSettingsState.contact)
async def set_contact_save(message: Message, bot_id: int, bot_data: dict, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=ShopKeyboard.admin_main(bot_id))
        return
    await update_bot(bot_id, contact_info=message.text)
    await state.clear()
    await message.answer("✅ Aloqa ma'lumoti saqlandi!", reply_markup=ShopKeyboard.admin_main(bot_id))
