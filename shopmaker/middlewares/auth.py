"""
Middleware — Foydalanuvchi autentifikatsiyasi va bot ma'lumotlari.
"""

import logging
from typing import Any, Callable, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from database.queries import get_or_create_user, get_user, get_bot_by_token, add_log

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseMiddleware):
    """
    Asosiy bot uchun middleware.
    Har bir so'rovda foydalanuvchini yaratadi/yangilaydi
    va user_data ni context ga qo'shadi.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        # Foydalanuvchi ma'lumotlarini olamiz
        telegram_user = None
        if isinstance(event, (Message, CallbackQuery)):
            telegram_user = event.from_user

        if telegram_user:
            try:
                user, created = await get_or_create_user(
                    user_id=telegram_user.id,
                    full_name=telegram_user.full_name,
                    username=telegram_user.username
                )
                data["user_data"] = dict(user) if user else {}
                data["is_new_user"] = created

                # Bloklangan foydalanuvchini to'sadi
                if user and user["is_blocked"]:
                    if isinstance(event, Message):
                        await event.answer(
                            "❌ Siz bloklangansiz. Muammo uchun admin bilan bog'laning."
                        )
                    elif isinstance(event, CallbackQuery):
                        await event.answer(
                            "❌ Siz bloklangansiz.", show_alert=True
                        )
                    return

            except Exception as e:
                logger.error("AuthMiddleware xatosi: %s", e)
                data["user_data"] = {}
                data["is_new_user"] = False

        return await handler(event, data)


class ShopBotMiddleware(BaseMiddleware):
    """
    Shop bot uchun middleware.
    bot_id va bot_data ni context ga qo'shadi.
    Har bir shop boti uchun alohida instance yaratiladi.
    """

    def __init__(self, bot_id: int, bot_data: dict):
        """
        bot_id: Ma'lumotlar bazasidagi bot ID si
        bot_data: Botga oid ma'lumotlar (owner_id, token, ...)
        """
        super().__init__()
        self.bot_id = bot_id
        self.bot_data = bot_data

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        # Bot ma'lumotlarini contextga qo'shamiz
        data["bot_id"] = self.bot_id
        data["bot_data"] = self.bot_data

        # Shop foydalanuvchisini ham saqlaymiz
        from database.queries import get_or_create_shop_user, get_shop_user
        telegram_user = None
        if isinstance(event, (Message, CallbackQuery)):
            telegram_user = event.from_user

        if telegram_user:
            try:
                await get_or_create_shop_user(
                    bot_id=self.bot_id,
                    user_id=telegram_user.id,
                    full_name=telegram_user.full_name,
                    username=telegram_user.username
                )
                shop_user = await get_shop_user(self.bot_id, telegram_user.id)
                data["shop_user"] = dict(shop_user) if shop_user else {}

                # Bloklangan shop foydalanuvchini to'sadi
                if shop_user and shop_user["is_blocked"]:
                    if isinstance(event, Message):
                        await event.answer(
                            "❌ Siz bu botda bloklangansiz."
                        )
                    elif isinstance(event, CallbackQuery):
                        await event.answer("❌ Siz bloklangansiz.", show_alert=True)
                    return

            except Exception as e:
                logger.error("ShopBotMiddleware xatosi (bot_id=%d): %s", self.bot_id, e)
                data["shop_user"] = {}

        return await handler(event, data)
