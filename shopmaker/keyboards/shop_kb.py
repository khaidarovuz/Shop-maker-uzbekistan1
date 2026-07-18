"""
Shop bot klaviaturaları — xaridorlar va shop admin uchun.
"""

from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


class ShopKeyboard:
    """Shop bot klaviaturaları."""

    @staticmethod
    def main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
        """Shop bot asosiy menyusi."""
        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text="🛍 Mahsulotlar"),
            KeyboardButton(text="📂 Kategoriyalar"),
        )
        builder.row(
            KeyboardButton(text="🔍 Qidirish"),
            KeyboardButton(text="🛒 Savat"),
        )
        builder.row(
            KeyboardButton(text="📋 Buyurtmalarim"),
            KeyboardButton(text="📞 Admin bilan bog'lanish"),
        )
        builder.row(KeyboardButton(text="ℹ️ Bot haqida"))
        if is_admin:
            builder.row(KeyboardButton(text="👑 Admin panel"))
        return builder.as_markup(resize_keyboard=True)

    @staticmethod
    def remove() -> ReplyKeyboardRemove:
        return ReplyKeyboardRemove()

    @staticmethod
    def cancel() -> ReplyKeyboardMarkup:
        builder = ReplyKeyboardBuilder()
        builder.row(KeyboardButton(text="❌ Bekor qilish"))
        return builder.as_markup(resize_keyboard=True)

    @staticmethod
    def back() -> ReplyKeyboardMarkup:
        builder = ReplyKeyboardBuilder()
        builder.row(KeyboardButton(text="⬅️ Orqaga"))
        return builder.as_markup(resize_keyboard=True)

    @staticmethod
    def skip_cancel() -> ReplyKeyboardMarkup:
        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text="⏩ O'tkazib yuborish"),
            KeyboardButton(text="❌ Bekor qilish"),
        )
        return builder.as_markup(resize_keyboard=True)

    @staticmethod
    def share_contact() -> ReplyKeyboardMarkup:
        builder = ReplyKeyboardBuilder()
        builder.row(KeyboardButton(text="📱 Telefon raqamimni ulashish", request_contact=True))
        builder.row(KeyboardButton(text="❌ Bekor qilish"))
        return builder.as_markup(resize_keyboard=True)

    # ── Mahsulotlar ─────────────────────────────────────────────────────────

    @staticmethod
    def categories_inline(cats: list) -> InlineKeyboardMarkup:
        """Kategoriyalar inline ro'yxati."""
        builder = InlineKeyboardBuilder()
        for cat in cats:
            builder.row(
                InlineKeyboardButton(
                    text=f"{cat['icon']} {cat['name']}",
                    callback_data=f"shop_cat:{cat['id']}"
                )
            )
        builder.row(
            InlineKeyboardButton(text="📋 Barcha mahsulotlar", callback_data="shop_cat:all"),
        )
        return builder.as_markup()

    @staticmethod
    def product_page(
        product_id: int,
        page: int,
        total: int,
        in_cart: int = 0
    ) -> InlineKeyboardMarkup:
        """Mahsulot sahifasi klaviaturasi."""
        builder = InlineKeyboardBuilder()

        if in_cart > 0:
            builder.row(
                InlineKeyboardButton(text="➖", callback_data=f"cart_dec:{product_id}"),
                InlineKeyboardButton(text=f"🛒 {in_cart}", callback_data=f"cart_count:{product_id}"),
                InlineKeyboardButton(text="➕", callback_data=f"cart_inc:{product_id}"),
            )
        else:
            builder.row(
                InlineKeyboardButton(text="🛒 Savatga qo'shish", callback_data=f"cart_add:{product_id}"),
            )

        nav = []
        if page > 1:
            nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"shop_prod:{page-1}"))
        nav.append(InlineKeyboardButton(text=f"{page}/{total}", callback_data="noop"))
        if page < total:
            nav.append(InlineKeyboardButton(text="➡️", callback_data=f"shop_prod:{page+1}"))
        if len(nav) > 1:
            builder.row(*nav)

        builder.row(
            InlineKeyboardButton(text="⬅️ Ro'yxatga qaytish", callback_data="shop_products_back"),
        )
        return builder.as_markup()

    @staticmethod
    def cart_view(items: list) -> InlineKeyboardMarkup:
        """Savat ko'rinishi."""
        builder = InlineKeyboardBuilder()

        for item in items:
            builder.row(
                InlineKeyboardButton(
                    text=f"➖",
                    callback_data=f"cart_dec:{item['product_id']}"
                ),
                InlineKeyboardButton(
                    text=f"{item['name'][:20]} × {item['quantity']}",
                    callback_data=f"noop"
                ),
                InlineKeyboardButton(
                    text=f"➕",
                    callback_data=f"cart_inc:{item['product_id']}"
                ),
            )

        builder.row(
            InlineKeyboardButton(text="🗑 Savatni tozalash", callback_data="cart_clear"),
        )
        builder.row(
            InlineKeyboardButton(text="✅ Buyurtma berish", callback_data="order_checkout"),
        )
        return builder.as_markup()

    @staticmethod
    def order_confirm() -> InlineKeyboardMarkup:
        """Buyurtma tasdiqlash."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="order_confirm"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="order_cancel"),
        )
        return builder.as_markup()

    @staticmethod
    def my_orders(orders: list) -> InlineKeyboardMarkup:
        """Foydalanuvchi buyurtmalari."""
        builder = InlineKeyboardBuilder()
        status_icons = {
            "new": "🆕", "processing": "⏳", "shipped": "🚚",
            "delivered": "✅", "cancelled": "❌"
        }
        for order in orders[:10]:  # Oxirgi 10 ta
            icon = status_icons.get(order["status"], "📋")
            builder.row(
                InlineKeyboardButton(
                    text=f"{icon} Buyurtma #{order['id']}",
                    callback_data=f"my_order:{order['id']}"
                )
            )
        return builder.as_markup()

    # ── Admin panel ─────────────────────────────────────────────────────────

    @staticmethod
    def admin_main(bot_id: int) -> ReplyKeyboardMarkup:
        """Shop admin asosiy menyusi."""
        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text="➕ Mahsulot qo'shish"),
            KeyboardButton(text="📦 Mahsulotlar"),
        )
        builder.row(
            KeyboardButton(text="📂 Kategoriyalar"),
            KeyboardButton(text="📋 Buyurtmalar"),
        )
        builder.row(
            KeyboardButton(text="📊 Statistika"),
            KeyboardButton(text="📣 Xabar yuborish"),
        )
        builder.row(
            KeyboardButton(text="⚙️ Sozlamalar"),
            KeyboardButton(text="🏠 Asosiy menyu"),
        )
        return builder.as_markup(resize_keyboard=True)

    @staticmethod
    def admin_orders_filter() -> InlineKeyboardMarkup:
        """Admin buyurtmalar filtri."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="🆕 Yangi", callback_data="admin_orders:new"),
            InlineKeyboardButton(text="⏳ Jarayonda", callback_data="admin_orders:processing"),
        )
        builder.row(
            InlineKeyboardButton(text="🚚 Yetkazilmoqda", callback_data="admin_orders:shipped"),
            InlineKeyboardButton(text="✅ Yetkazildi", callback_data="admin_orders:delivered"),
        )
        builder.row(
            InlineKeyboardButton(text="❌ Bekor qilindi", callback_data="admin_orders:cancelled"),
            InlineKeyboardButton(text="📋 Barchasi", callback_data="admin_orders:all"),
        )
        return builder.as_markup()

    @staticmethod
    def admin_order_actions(order_id: int) -> InlineKeyboardMarkup:
        """Admin buyurtma amallari."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="⏳ Jarayonda", callback_data=f"ao_status:{order_id}:processing"),
            InlineKeyboardButton(text="🚚 Yetkazilmoqda", callback_data=f"ao_status:{order_id}:shipped"),
        )
        builder.row(
            InlineKeyboardButton(text="✅ Yetkazildi", callback_data=f"ao_status:{order_id}:delivered"),
            InlineKeyboardButton(text="❌ Bekor qilindi", callback_data=f"ao_status:{order_id}:cancelled"),
        )
        builder.row(
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_orders:all"),
        )
        return builder.as_markup()

    @staticmethod
    def admin_cats(cats: list) -> InlineKeyboardMarkup:
        """Admin kategoriyalar ro'yxati."""
        builder = InlineKeyboardBuilder()
        for cat in cats:
            builder.row(
                InlineKeyboardButton(
                    text=f"🗑 {cat['icon']} {cat['name']}",
                    callback_data=f"admin_del_cat:{cat['id']}"
                )
            )
        return builder.as_markup()

    @staticmethod
    def admin_products(prods: list, page: int = 1, total_pages: int = 1) -> InlineKeyboardMarkup:
        """Admin mahsulotlar ro'yxati."""
        builder = InlineKeyboardBuilder()
        for prod in prods:
            avail = "✅" if prod["is_available"] else "❌"
            builder.row(
                InlineKeyboardButton(
                    text=f"{avail} {prod['name']} — {prod['price']:,.0f} so'm",
                    callback_data=f"admin_product:{prod['id']}"
                )
            )

        nav = []
        if page > 1:
            nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"admin_prods_page:{page-1}"))
        if page < total_pages:
            nav.append(InlineKeyboardButton(text="➡️", callback_data=f"admin_prods_page:{page+1}"))
        if nav:
            builder.row(*nav)

        return builder.as_markup()

    @staticmethod
    def admin_product_actions(product_id: int, is_available: bool) -> InlineKeyboardMarkup:
        """Admin mahsulot amallari."""
        builder = InlineKeyboardBuilder()
        toggle_text = "❌ Yashirish" if is_available else "✅ Ko'rsatish"
        builder.row(
            InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"admin_edit_prod:{product_id}"),
            InlineKeyboardButton(text=toggle_text, callback_data=f"admin_toggle_prod:{product_id}"),
        )
        builder.row(
            InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"admin_del_prod:{product_id}"),
        )
        builder.row(
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_prods_page:1"),
        )
        return builder.as_markup()

    @staticmethod
    def admin_edit_product_fields(product_id: int) -> InlineKeyboardMarkup:
        """Admin mahsulot tahrirlash maydonlari."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="📝 Nomi", callback_data=f"aep_name:{product_id}"),
            InlineKeyboardButton(text="💰 Narxi", callback_data=f"aep_price:{product_id}"),
        )
        builder.row(
            InlineKeyboardButton(text="📄 Tavsifi", callback_data=f"aep_desc:{product_id}"),
            InlineKeyboardButton(text="🖼 Rasmi", callback_data=f"aep_photo:{product_id}"),
        )
        builder.row(
            InlineKeyboardButton(text="📂 Kategoriya", callback_data=f"aep_cat:{product_id}"),
        )
        builder.row(
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"admin_product:{product_id}"),
        )
        return builder.as_markup()

    @staticmethod
    def admin_del_cat_confirm(cat_id: int) -> InlineKeyboardMarkup:
        """Kategoriya o'chirish tasdiqlash (admin)."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=f"admin_del_cat_ok:{cat_id}"),
            InlineKeyboardButton(text="❌ Yo'q", callback_data="admin_cats_list"),
        )
        return builder.as_markup()

    @staticmethod
    def admin_del_prod_confirm(product_id: int) -> InlineKeyboardMarkup:
        """Mahsulot o'chirish tasdiqlash (admin)."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=f"admin_del_prod_ok:{product_id}"),
            InlineKeyboardButton(text="❌ Yo'q", callback_data=f"admin_product:{product_id}"),
        )
        return builder.as_markup()

    @staticmethod
    def admin_settings() -> InlineKeyboardMarkup:
        """Admin sozlamalar menyusi."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="👋 Xush kelibsiz", callback_data="admin_set_welcome"),
        )
        builder.row(
            InlineKeyboardButton(text="ℹ️ Bot haqida", callback_data="admin_set_about"),
        )
        builder.row(
            InlineKeyboardButton(text="📞 Aloqa", callback_data="admin_set_contact"),
        )
        return builder.as_markup()

    @staticmethod
    def broadcast_confirm() -> InlineKeyboardMarkup:
        """Broadcast tasdiqlash (shop admin)."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="✅ Yuborish", callback_data="admin_broadcast_send"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_broadcast_cancel"),
        )
        return builder.as_markup()

    @staticmethod
    def admin_cats_for_product(cats: list) -> InlineKeyboardMarkup:
        """Admin mahsulot uchun kategoriya tanlash."""
        builder = InlineKeyboardBuilder()
        for cat in cats:
            builder.row(
                InlineKeyboardButton(
                    text=f"{cat['icon']} {cat['name']}",
                    callback_data=f"aep_set_cat:{cat['id']}"
                )
            )
        builder.row(
            InlineKeyboardButton(text="❌ Kategoriyasiz", callback_data="aep_set_cat:0"),
        )
        return builder.as_markup()
