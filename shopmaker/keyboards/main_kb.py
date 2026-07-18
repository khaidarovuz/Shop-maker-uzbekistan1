"""
Asosiy bot klaviaturaları — inline va reply klaviaturalar.
"""

from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


class MainKeyboard:
    """Asosiy ShopMaker bot klaviaturaları."""

    @staticmethod
    def main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
        """Asosiy menyu klaviaturasi."""
        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text="🤖 Mening botlarim"),
            KeyboardButton(text="➕ Bot qo'shish"),
        )
        builder.row(
            KeyboardButton(text="💎 Rejalar"),
            KeyboardButton(text="📊 Statistika"),
        )
        builder.row(
            KeyboardButton(text="⚙️ Sozlamalar"),
            KeyboardButton(text="❓ Yordam"),
        )
        if is_admin:
            builder.row(KeyboardButton(text="👑 Admin panel"))
        return builder.as_markup(resize_keyboard=True)

    @staticmethod
    def remove() -> ReplyKeyboardRemove:
        """Klaviaturani olib tashlaydi."""
        return ReplyKeyboardRemove()

    @staticmethod
    def cancel() -> ReplyKeyboardMarkup:
        """Bekor qilish klaviaturasi."""
        builder = ReplyKeyboardBuilder()
        builder.row(KeyboardButton(text="❌ Bekor qilish"))
        return builder.as_markup(resize_keyboard=True)

    @staticmethod
    def back_cancel() -> ReplyKeyboardMarkup:
        """Orqaga va bekor qilish."""
        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text="⬅️ Orqaga"),
            KeyboardButton(text="❌ Bekor qilish"),
        )
        return builder.as_markup(resize_keyboard=True)

    @staticmethod
    def skip_cancel() -> ReplyKeyboardMarkup:
        """O'tkazib yuborish va bekor qilish."""
        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text="⏩ O'tkazib yuborish"),
            KeyboardButton(text="❌ Bekor qilish"),
        )
        return builder.as_markup(resize_keyboard=True)

    @staticmethod
    def share_contact() -> ReplyKeyboardMarkup:
        """Telefon raqam ulashish klaviaturasi."""
        builder = ReplyKeyboardBuilder()
        builder.row(KeyboardButton(text="📱 Telefon raqamimni ulashish", request_contact=True))
        builder.row(KeyboardButton(text="❌ Bekor qilish"))
        return builder.as_markup(resize_keyboard=True)

    @staticmethod
    def confirm_cancel() -> InlineKeyboardMarkup:
        """Tasdiqlash/bekor qilish inline klaviaturasi."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel"),
        )
        return builder.as_markup()

    # ── Bot ro'yxati ────────────────────────────────────────────────────────

    @staticmethod
    def bot_list(bots: list, page: int = 1, total_pages: int = 1) -> InlineKeyboardMarkup:
        """Botlar ro'yxati inline klaviaturasi."""
        builder = InlineKeyboardBuilder()

        for bot in bots:
            status = "🔴" if not bot["is_active"] or bot["is_locked"] else "🟢"
            locked = "🔒 " if bot["is_locked"] else ""
            builder.row(
                InlineKeyboardButton(
                    text=f"{status} {locked}@{bot['bot_username'] or bot['bot_name']}",
                    callback_data=f"bot:{bot['id']}"
                )
            )

        # Sahifalash
        nav_buttons = []
        if page > 1:
            nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"bots_page:{page-1}"))
        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"bots_page:{page+1}"))
        if nav_buttons:
            builder.row(*nav_buttons)

        return builder.as_markup()

    @staticmethod
    def bot_menu(bot_id: int, is_active: bool, is_locked: bool) -> InlineKeyboardMarkup:
        """Bot boshqaruv menyusi."""
        builder = InlineKeyboardBuilder()

        if is_locked:
            builder.row(
                InlineKeyboardButton(text="🔒 Bot qulflangan", callback_data="locked_info")
            )
        else:
            toggle = "⏹ O'chirish" if is_active else "▶️ Yoqish"
            toggle_cb = f"bot_toggle:{bot_id}"
            builder.row(InlineKeyboardButton(text=toggle, callback_data=toggle_cb))

        builder.row(
            InlineKeyboardButton(text="📦 Mahsulotlar", callback_data=f"bot_products:{bot_id}"),
            InlineKeyboardButton(text="📂 Kategoriyalar", callback_data=f"bot_cats:{bot_id}"),
        )
        builder.row(
            InlineKeyboardButton(text="📋 Buyurtmalar", callback_data=f"bot_orders:{bot_id}"),
            InlineKeyboardButton(text="📊 Statistika", callback_data=f"bot_stats:{bot_id}"),
        )
        builder.row(
            InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data=f"bot_settings:{bot_id}"),
        )
        builder.row(
            InlineKeyboardButton(text="🗑 Botni o'chirish", callback_data=f"bot_delete:{bot_id}"),
        )
        builder.row(
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data="my_bots"),
        )
        return builder.as_markup()

    @staticmethod
    def bot_settings(bot_id: int) -> InlineKeyboardMarkup:
        """Bot sozlamalari menyusi."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="👋 Xush kelibsiz matni", callback_data=f"bs_welcome:{bot_id}"),
        )
        builder.row(
            InlineKeyboardButton(text="ℹ️ Bot haqida", callback_data=f"bs_about:{bot_id}"),
        )
        builder.row(
            InlineKeyboardButton(text="📞 Aloqa ma'lumoti", callback_data=f"bs_contact:{bot_id}"),
        )
        builder.row(
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"bot:{bot_id}"),
        )
        return builder.as_markup()

    @staticmethod
    def delete_confirm(bot_id: int) -> InlineKeyboardMarkup:
        """Bot o'chirish tasdiqlash."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=f"bot_delete_confirm:{bot_id}"),
            InlineKeyboardButton(text="❌ Yo'q", callback_data=f"bot:{bot_id}"),
        )
        return builder.as_markup()

    # ── Rejalar ─────────────────────────────────────────────────────────────

    @staticmethod
    def plans_menu() -> InlineKeyboardMarkup:
        """Rejalar menyusi."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="💎 Premium sotib olish", callback_data="buy_premium"),
        )
        builder.row(
            InlineKeyboardButton(text="🌟 Comfort sotib olish", callback_data="buy_comfort"),
        )
        builder.row(
            InlineKeyboardButton(text="🎁 Promo kod", callback_data="promo_code"),
        )
        return builder.as_markup()

    @staticmethod
    def payment_methods(plan: str) -> InlineKeyboardMarkup:
        """To'lov usullari."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="💳 Click", callback_data=f"pay_click:{plan}"),
        )
        builder.row(
            InlineKeyboardButton(text="💳 Payme", callback_data=f"pay_payme:{plan}"),
        )
        builder.row(
            InlineKeyboardButton(text="💳 Uzum Bank", callback_data=f"pay_uzum:{plan}"),
        )
        builder.row(
            InlineKeyboardButton(text="💵 Qo'lda to'lov", callback_data=f"pay_manual:{plan}"),
        )
        builder.row(
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data="plans"),
        )
        return builder.as_markup()

    @staticmethod
    def check_payment(payment_id: int) -> InlineKeyboardMarkup:
        """To'lovni tekshirish."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="🔄 Tekshirish", callback_data=f"check_payment:{payment_id}"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"cancel_payment:{payment_id}"),
        )
        return builder.as_markup()

    # ── Mahsulot boshqaruv ──────────────────────────────────────────────────

    @staticmethod
    def products_menu(bot_id: int) -> InlineKeyboardMarkup:
        """Mahsulotlar boshqaruv menyusi."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="➕ Mahsulot qo'shish", callback_data=f"add_product:{bot_id}"),
        )
        builder.row(
            InlineKeyboardButton(text="📋 Mahsulotlar ro'yxati", callback_data=f"product_list:{bot_id}:1"),
        )
        builder.row(
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"bot:{bot_id}"),
        )
        return builder.as_markup()

    @staticmethod
    def product_list(products: list, bot_id: int, page: int = 1, total_pages: int = 1) -> InlineKeyboardMarkup:
        """Mahsulotlar ro'yxati."""
        builder = InlineKeyboardBuilder()

        for prod in products:
            avail = "✅" if prod["is_available"] else "❌"
            builder.row(
                InlineKeyboardButton(
                    text=f"{avail} {prod['name']} — {prod['price']:,.0f} so'm",
                    callback_data=f"product:{prod['id']}:{bot_id}"
                )
            )

        nav = []
        if page > 1:
            nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"product_list:{bot_id}:{page-1}"))
        if page < total_pages:
            nav.append(InlineKeyboardButton(text="➡️", callback_data=f"product_list:{bot_id}:{page+1}"))
        if nav:
            builder.row(*nav)

        builder.row(
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"bot_products:{bot_id}"),
        )
        return builder.as_markup()

    @staticmethod
    def product_actions(product_id: int, bot_id: int, is_available: bool) -> InlineKeyboardMarkup:
        """Mahsulot amallari."""
        builder = InlineKeyboardBuilder()
        toggle_text = "❌ Yashirish" if is_available else "✅ Ko'rsatish"
        builder.row(
            InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"edit_product:{product_id}:{bot_id}"),
            InlineKeyboardButton(text=toggle_text, callback_data=f"toggle_product:{product_id}:{bot_id}"),
        )
        builder.row(
            InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"delete_product:{product_id}:{bot_id}"),
        )
        builder.row(
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"product_list:{bot_id}:1"),
        )
        return builder.as_markup()

    @staticmethod
    def edit_product_fields(product_id: int, bot_id: int) -> InlineKeyboardMarkup:
        """Mahsulot tahrirlash maydonlari."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="📝 Nomi", callback_data=f"ep_name:{product_id}:{bot_id}"),
            InlineKeyboardButton(text="💰 Narxi", callback_data=f"ep_price:{product_id}:{bot_id}"),
        )
        builder.row(
            InlineKeyboardButton(text="📄 Tavsifi", callback_data=f"ep_desc:{product_id}:{bot_id}"),
            InlineKeyboardButton(text="🖼 Rasmi", callback_data=f"ep_photo:{product_id}:{bot_id}"),
        )
        builder.row(
            InlineKeyboardButton(text="📂 Kategoriya", callback_data=f"ep_cat:{product_id}:{bot_id}"),
        )
        builder.row(
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"product:{product_id}:{bot_id}"),
        )
        return builder.as_markup()

    @staticmethod
    def delete_product_confirm(product_id: int, bot_id: int) -> InlineKeyboardMarkup:
        """Mahsulot o'chirish tasdiqlash."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=f"del_product_ok:{product_id}:{bot_id}"),
            InlineKeyboardButton(text="❌ Yo'q", callback_data=f"product:{product_id}:{bot_id}"),
        )
        return builder.as_markup()

    @staticmethod
    def categories_list_for_product(cats: list, bot_id: int, product_id: int) -> InlineKeyboardMarkup:
        """Mahsulot uchun kategoriya tanlash."""
        builder = InlineKeyboardBuilder()
        for cat in cats:
            builder.row(
                InlineKeyboardButton(
                    text=f"{cat['icon']} {cat['name']}",
                    callback_data=f"set_cat:{product_id}:{cat['id']}:{bot_id}"
                )
            )
        builder.row(
            InlineKeyboardButton(text="❌ Kategoriyasiz", callback_data=f"set_cat:{product_id}:0:{bot_id}"),
        )
        return builder.as_markup()

    # ── Kategoriyalar ───────────────────────────────────────────────────────

    @staticmethod
    def categories_menu(bot_id: int) -> InlineKeyboardMarkup:
        """Kategoriyalar boshqaruv menyusi."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="➕ Kategoriya qo'shish", callback_data=f"add_cat:{bot_id}"),
        )
        builder.row(
            InlineKeyboardButton(text="📋 Kategoriyalar ro'yxati", callback_data=f"cat_list:{bot_id}"),
        )
        builder.row(
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"bot:{bot_id}"),
        )
        return builder.as_markup()

    @staticmethod
    def cat_list(cats: list, bot_id: int) -> InlineKeyboardMarkup:
        """Kategoriyalar ro'yxati."""
        builder = InlineKeyboardBuilder()
        for cat in cats:
            builder.row(
                InlineKeyboardButton(
                    text=f"{cat['icon']} {cat['name']}",
                    callback_data=f"cat_action:{cat['id']}:{bot_id}"
                )
            )
        builder.row(
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"bot_cats:{bot_id}"),
        )
        return builder.as_markup()

    @staticmethod
    def cat_actions(cat_id: int, bot_id: int) -> InlineKeyboardMarkup:
        """Kategoriya amallari."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"del_cat:{cat_id}:{bot_id}"),
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"cat_list:{bot_id}"),
        )
        return builder.as_markup()

    @staticmethod
    def del_cat_confirm(cat_id: int, bot_id: int) -> InlineKeyboardMarkup:
        """Kategoriya o'chirish tasdiqlash."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="✅ Ha", callback_data=f"del_cat_ok:{cat_id}:{bot_id}"),
            InlineKeyboardButton(text="❌ Yo'q", callback_data=f"cat_action:{cat_id}:{bot_id}"),
        )
        return builder.as_markup()

    # ── Buyurtmalar ─────────────────────────────────────────────────────────

    @staticmethod
    def orders_filter(bot_id: int) -> InlineKeyboardMarkup:
        """Buyurtmalar filtri."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="🆕 Yangi", callback_data=f"orders_filter:{bot_id}:new"),
            InlineKeyboardButton(text="⏳ Jarayonda", callback_data=f"orders_filter:{bot_id}:processing"),
        )
        builder.row(
            InlineKeyboardButton(text="🚚 Yetkazilmoqda", callback_data=f"orders_filter:{bot_id}:shipped"),
            InlineKeyboardButton(text="✅ Yetkazildi", callback_data=f"orders_filter:{bot_id}:delivered"),
        )
        builder.row(
            InlineKeyboardButton(text="❌ Bekor qilindi", callback_data=f"orders_filter:{bot_id}:cancelled"),
            InlineKeyboardButton(text="📋 Barchasi", callback_data=f"orders_filter:{bot_id}:all"),
        )
        builder.row(
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"bot:{bot_id}"),
        )
        return builder.as_markup()

    @staticmethod
    def order_status_change(order_id: int, bot_id: int) -> InlineKeyboardMarkup:
        """Buyurtma holat o'zgartirish."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="⏳ Jarayonda", callback_data=f"ord_status:{order_id}:processing:{bot_id}"),
            InlineKeyboardButton(text="🚚 Yetkazilmoqda", callback_data=f"ord_status:{order_id}:shipped:{bot_id}"),
        )
        builder.row(
            InlineKeyboardButton(text="✅ Yetkazildi", callback_data=f"ord_status:{order_id}:delivered:{bot_id}"),
            InlineKeyboardButton(text="❌ Bekor qilindi", callback_data=f"ord_status:{order_id}:cancelled:{bot_id}"),
        )
        builder.row(
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"bot_orders:{bot_id}"),
        )
        return builder.as_markup()

    # ── Statistika ───────────────────────────────────────────────────────────

    @staticmethod
    def stats_menu(bot_id: int) -> InlineKeyboardMarkup:
        """Statistika menyusi."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="📤 Excel eksport", callback_data=f"export_orders:{bot_id}"),
        )
        builder.row(
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"bot:{bot_id}"),
        )
        return builder.as_markup()

    # ── Broadcast ───────────────────────────────────────────────────────────

    @staticmethod
    def broadcast_confirm(bot_id: int) -> InlineKeyboardMarkup:
        """Broadcast tasdiqlash."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="✅ Yuborish", callback_data=f"broadcast_send:{bot_id}"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"bot:{bot_id}"),
        )
        return builder.as_markup()
