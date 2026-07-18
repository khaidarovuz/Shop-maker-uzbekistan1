"""
Super Admin klaviaturaları — ShopMaker bosh admin panel uchun.
"""

from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


class AdminKeyboard:
    """Super admin klaviaturaları."""

    @staticmethod
    def main_panel() -> InlineKeyboardMarkup:
        """Super admin asosiy panel."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="📊 Statistika", callback_data="sa_stats"),
            InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="sa_users"),
        )
        builder.row(
            InlineKeyboardButton(text="💎 Premium berish", callback_data="sa_give_premium"),
            InlineKeyboardButton(text="🌟 Comfort berish", callback_data="sa_give_comfort"),
        )
        builder.row(
            InlineKeyboardButton(text="❌ Rejani bekor qilish", callback_data="sa_remove_plan"),
            InlineKeyboardButton(text="🚫 Bloklash", callback_data="sa_block_user"),
        )
        builder.row(
            InlineKeyboardButton(text="✅ Blokdan chiqarish", callback_data="sa_unblock_user"),
            InlineKeyboardButton(text="🗑 Bot o'chirish", callback_data="sa_delete_bot"),
        )
        builder.row(
            InlineKeyboardButton(text="📣 Global broadcast", callback_data="sa_broadcast"),
            InlineKeyboardButton(text="🎁 Promo kod", callback_data="sa_promo"),
        )
        builder.row(
            InlineKeyboardButton(text="💳 Kutilayotgan to'lovlar", callback_data="sa_payments"),
            InlineKeyboardButton(text="💰 Narxlar", callback_data="sa_prices"),
        )
        builder.row(
            InlineKeyboardButton(text="🔒 Ro'yxatdan o'tish", callback_data="sa_registration"),
            InlineKeyboardButton(text="📋 Tizim loglari", callback_data="sa_logs"),
        )
        builder.row(
            InlineKeyboardButton(text="💾 Zaxira nusxa", callback_data="sa_backup"),
        )
        return builder.as_markup()

    @staticmethod
    def users_list(users: list, page: int = 1, total_pages: int = 1) -> InlineKeyboardMarkup:
        """Foydalanuvchilar ro'yxati."""
        builder = InlineKeyboardBuilder()
        for user in users:
            plan_icon = {"free": "🆓", "comfort": "🌟", "premium": "💎"}.get(user["plan"], "🆓")
            blocked = "🚫" if user["is_blocked"] else ""
            name = user["full_name"][:20]
            builder.row(
                InlineKeyboardButton(
                    text=f"{plan_icon} {blocked} {name} (#{user['id']})",
                    callback_data=f"sa_user:{user['id']}"
                )
            )

        nav = []
        if page > 1:
            nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"sa_users_page:{page-1}"))
        if page < total_pages:
            nav.append(InlineKeyboardButton(text="➡️", callback_data=f"sa_users_page:{page+1}"))
        if nav:
            builder.row(*nav)

        builder.row(
            InlineKeyboardButton(text="⬅️ Admin panel", callback_data="sa_main"),
        )
        return builder.as_markup()

    @staticmethod
    def user_actions(user_id: int, is_blocked: bool, plan: str) -> InlineKeyboardMarkup:
        """Foydalanuvchi amallari."""
        builder = InlineKeyboardBuilder()

        if is_blocked:
            builder.row(
                InlineKeyboardButton(text="✅ Blokdan chiqarish", callback_data=f"sa_unblock:{user_id}"),
            )
        else:
            builder.row(
                InlineKeyboardButton(text="🚫 Bloklash", callback_data=f"sa_block:{user_id}"),
            )

        if plan == "free":
            builder.row(
                InlineKeyboardButton(text="💎 Premium", callback_data=f"sa_give_prem:{user_id}"),
                InlineKeyboardButton(text="🌟 Comfort", callback_data=f"sa_give_comf:{user_id}"),
            )
        else:
            builder.row(
                InlineKeyboardButton(text="❌ Rejani olib tashlash", callback_data=f"sa_rm_plan:{user_id}"),
            )

        builder.row(
            InlineKeyboardButton(text="🤖 Botlari", callback_data=f"sa_user_bots:{user_id}"),
        )
        builder.row(
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data="sa_users"),
        )
        return builder.as_markup()

    @staticmethod
    def payments_list(payments: list) -> InlineKeyboardMarkup:
        """Kutilayotgan to'lovlar."""
        builder = InlineKeyboardBuilder()
        for pay in payments:
            name = (pay["full_name"] or str(pay["user_id"]))[:15]
            builder.row(
                InlineKeyboardButton(
                    text=f"#{pay['id']} {name} — {pay['amount']:,.0f} so'm ({pay['plan']})",
                    callback_data=f"sa_pay:{pay['id']}"
                )
            )
        builder.row(
            InlineKeyboardButton(text="⬅️ Admin panel", callback_data="sa_main"),
        )
        return builder.as_markup()

    @staticmethod
    def payment_actions(payment_id: int) -> InlineKeyboardMarkup:
        """To'lov amallari."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"sa_pay_approve:{payment_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"sa_pay_reject:{payment_id}"),
        )
        builder.row(
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data="sa_payments"),
        )
        return builder.as_markup()

    @staticmethod
    def prices_menu() -> InlineKeyboardMarkup:
        """Narxlar boshqaruvi."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="💎 Premium narxi", callback_data="sa_set_premium_price"),
            InlineKeyboardButton(text="💎 Premium muddati", callback_data="sa_set_premium_days"),
        )
        builder.row(
            InlineKeyboardButton(text="🌟 Comfort narxi", callback_data="sa_set_comfort_price"),
            InlineKeyboardButton(text="🌟 Comfort muddati", callback_data="sa_set_comfort_days"),
        )
        builder.row(
            InlineKeyboardButton(text="⬅️ Admin panel", callback_data="sa_main"),
        )
        return builder.as_markup()

    @staticmethod
    def promo_menu() -> InlineKeyboardMarkup:
        """Promo kod menyusi."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="➕ Yangi promo kod", callback_data="sa_create_promo"),
            InlineKeyboardButton(text="📋 Barcha promo kodlar", callback_data="sa_list_promos"),
        )
        builder.row(
            InlineKeyboardButton(text="⬅️ Admin panel", callback_data="sa_main"),
        )
        return builder.as_markup()

    @staticmethod
    def promo_plan_select() -> InlineKeyboardMarkup:
        """Promo kod rejasini tanlash."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="💎 Premium", callback_data="promo_plan:premium"),
            InlineKeyboardButton(text="🌟 Comfort", callback_data="promo_plan:comfort"),
        )
        return builder.as_markup()

    @staticmethod
    def registration_toggle(enabled: bool) -> InlineKeyboardMarkup:
        """Ro'yxatdan o'tishni boshqarish."""
        builder = InlineKeyboardBuilder()
        if enabled:
            builder.row(
                InlineKeyboardButton(text="🔒 O'chirish", callback_data="sa_reg_disable"),
            )
        else:
            builder.row(
                InlineKeyboardButton(text="🔓 Yoqish", callback_data="sa_reg_enable"),
            )
        builder.row(
            InlineKeyboardButton(text="⬅️ Admin panel", callback_data="sa_main"),
        )
        return builder.as_markup()

    @staticmethod
    def back_to_admin() -> InlineKeyboardMarkup:
        """Admin panelga qaytish."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="⬅️ Admin panel", callback_data="sa_main"),
        )
        return builder.as_markup()

    @staticmethod
    def user_bots_list(bots: list, user_id: int) -> InlineKeyboardMarkup:
        """Foydalanuvchi botlari ro'yxati."""
        builder = InlineKeyboardBuilder()
        for bot in bots:
            builder.row(
                InlineKeyboardButton(
                    text=f"@{bot['bot_username'] or bot['bot_name']}",
                    callback_data=f"sa_del_bot:{bot['id']}:{user_id}"
                )
            )
        builder.row(
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"sa_user:{user_id}"),
        )
        return builder.as_markup()

    @staticmethod
    def del_bot_confirm(bot_id: int, user_id: int) -> InlineKeyboardMarkup:
        """Bot o'chirish tasdiqlash."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=f"sa_del_bot_ok:{bot_id}:{user_id}"),
            InlineKeyboardButton(text="❌ Yo'q", callback_data=f"sa_user_bots:{user_id}"),
        )
        return builder.as_markup()
