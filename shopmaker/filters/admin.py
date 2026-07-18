"""
Filtrlar — Super admin va shop admin tekshiruvi.
"""

from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from config import config
from database.queries import get_bot


class IsSuperAdmin(BaseFilter):
    """Foydalanuvchi super admin ekanligini tekshiradi."""

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user = event.from_user
        if not user:
            return False
        return config.is_super_admin(user.id)


class IsShopAdmin(BaseFilter):
    """
    Foydalanuvchi ma'lum bir shop botning admin ekanligini tekshiradi.
    'bot_data' middleware orqali uzatiladi.
    """

    async def __call__(
        self,
        event: Message | CallbackQuery,
        bot_data: dict | None = None
    ) -> bool:
        if not bot_data:
            return False
        user = event.from_user
        if not user:
            return False
        # bot_data['owner_id'] — bot yaratgan foydalanuvchi
        return user.id == bot_data.get("owner_id")


class IsNotBlocked(BaseFilter):
    """Foydalanuvchi bloklangan emas ekanligini tekshiradi (main bot uchun)."""

    async def __call__(
        self,
        event: Message | CallbackQuery,
        user_data: dict | None = None
    ) -> bool:
        if not user_data:
            return True
        return not user_data.get("is_blocked", False)
