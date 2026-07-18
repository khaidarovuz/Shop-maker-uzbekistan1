"""
ShopMaker Bot — Konfiguratsiya fayli
Barcha sozlamalar shu yerda saqlanadi.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    # ── Asosiy bot sozlamalari ──────────────────────────────────────────────
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_IDS: list[int] = None          # Super admin ro'yxati

    # ── Ma'lumotlar bazasi ──────────────────────────────────────────────────
    DB_PATH: str = os.getenv("DB_PATH", "shopmaker.db")

    # ── Rejalar narxi va muddati ────────────────────────────────────────────
    PREMIUM_PRICE: int = int(os.getenv("PREMIUM_PRICE", "10000"))   # UZS
    PREMIUM_DAYS: int = int(os.getenv("PREMIUM_DAYS", "30"))

    COMFORT_PRICE: int = int(os.getenv("COMFORT_PRICE", "5000"))    # UZS
    COMFORT_DAYS: int = int(os.getenv("COMFORT_DAYS", "90"))

    # ── To'lov tizimi ───────────────────────────────────────────────────────
    CLICK_MERCHANT_ID: str = os.getenv("CLICK_MERCHANT_ID", "")
    CLICK_SERVICE_ID: str = os.getenv("CLICK_SERVICE_ID", "")
    CLICK_SECRET_KEY: str = os.getenv("CLICK_SECRET_KEY", "")

    PAYME_MERCHANT_ID: str = os.getenv("PAYME_MERCHANT_ID", "")
    PAYME_KEY: str = os.getenv("PAYME_KEY", "")

    UZUM_MERCHANT_ID: str = os.getenv("UZUM_MERCHANT_ID", "")
    UZUM_TOKEN: str = os.getenv("UZUM_TOKEN", "")

    # ── Bot limitleri ───────────────────────────────────────────────────────
    FREE_BOT_LIMIT: int = 1
    PREMIUM_BOT_LIMIT: int = 3
    COMFORT_BOT_LIMIT: int = 1

    # ── Log fayli ───────────────────────────────────────────────────────────
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/shopmaker.log")

    # ── Webhook (ixtiyoriy) ─────────────────────────────────────────────────
    USE_WEBHOOK: bool = os.getenv("USE_WEBHOOK", "false").lower() == "true"
    WEBHOOK_HOST: str = os.getenv("WEBHOOK_HOST", "")
    WEBHOOK_PATH: str = os.getenv("WEBHOOK_PATH", "/webhook")
    WEBAPP_PORT: int = int(os.getenv("WEBAPP_PORT", "8080"))

    def __post_init__(self):
        raw_ids = os.getenv("ADMIN_IDS", "8143880963")
        self.ADMIN_IDS = [int(i.strip()) for i in raw_ids.split(",") if i.strip()]

        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN muhit o'zgaruvchisi o'rnatilmagan!")

    def is_super_admin(self, user_id: int) -> bool:
        """Foydalanuvchi super admin ekanligini tekshiradi."""
        return user_id in self.ADMIN_IDS


# Global konfiguratsiya obyekti
config = Config()

# ── Matnlar (Uzbek) ─────────────────────────────────────────────────────────
class Texts:
    # Umumiy
    BTN_BACK = "⬅️ Orqaga"
    BTN_CANCEL = "❌ Bekor qilish"
    BTN_CONFIRM = "✅ Tasdiqlash"
    BTN_CLOSE = "❌ Yopish"
    BTN_YES = "✅ Ha"
    BTN_NO = "❌ Yo'q"
    BTN_NEXT = "➡️ Keyingisi"
    BTN_PREV = "⬅️ Oldingisi"
    BTN_SKIP = "⏩ O'tkazib yuborish"
    BTN_SAVE = "💾 Saqlash"

    # Asosiy menyu
    BTN_MY_BOTS = "🤖 Mening botlarim"
    BTN_CREATE_BOT = "➕ Bot yaratish"
    BTN_PLANS = "💎 Rejalar"
    BTN_STATISTICS = "📊 Statistika"
    BTN_SETTINGS = "⚙️ Sozlamalar"
    BTN_HELP = "❓ Yordam"
    BTN_ADMIN_PANEL = "👑 Admin panel"

    # Bot boshqaruv
    BTN_MANAGE_BOT = "⚙️ Boshqarish"
    BTN_BOT_PRODUCTS = "📦 Mahsulotlar"
    BTN_BOT_CATEGORIES = "📂 Kategoriyalar"
    BTN_BOT_ORDERS = "📋 Buyurtmalar"
    BTN_BOT_SETTINGS = "⚙️ Sozlamalar"
    BTN_BOT_STATS = "📊 Statistika"
    BTN_BOT_BROADCAST = "📣 Xabar yuborish"
    BTN_DELETE_BOT = "🗑 Botni o'chirish"
    BTN_START_BOT = "▶️ Yoqish"
    BTN_STOP_BOT = "⏹ O'chirish"

    # Rejalar
    BTN_FREE_PLAN = "🆓 Bepul"
    BTN_PREMIUM_PLAN = "💎 Premium"
    BTN_COMFORT_PLAN = "🌟 Comfort"
    BTN_BUY_PREMIUM = "💎 Premium sotib olish"
    BTN_BUY_COMFORT = "🌟 Comfort sotib olish"

    # To'lov
    BTN_PAY_CLICK = "💳 Click orqali"
    BTN_PAY_PAYME = "💳 Payme orqali"
    BTN_PAY_UZUM = "💳 Uzum Bank orqali"
    BTN_PAY_MANUAL = "💵 Qo'lda to'lov"
    BTN_CHECK_PAYMENT = "🔄 To'lovni tekshirish"

    # Mahsulot
    BTN_ADD_PRODUCT = "➕ Mahsulot qo'shish"
    BTN_EDIT_PRODUCT = "✏️ Tahrirlash"
    BTN_DELETE_PRODUCT = "🗑 O'chirish"
    BTN_PRODUCT_LIST = "📋 Ro'yxat"

    # Kategoriya
    BTN_ADD_CATEGORY = "➕ Kategoriya qo'shish"
    BTN_DELETE_CATEGORY = "🗑 Kategoriyani o'chirish"
    BTN_CATEGORY_LIST = "📂 Kategoriyalar ro'yxati"

    # Shop bot menyu
    SHOP_BTN_PRODUCTS = "🛍 Mahsulotlar"
    SHOP_BTN_CATEGORIES = "📂 Kategoriyalar"
    SHOP_BTN_SEARCH = "🔍 Qidirish"
    SHOP_BTN_CART = "🛒 Savat"
    SHOP_BTN_ORDERS = "📋 Buyurtmalarim"
    SHOP_BTN_CONTACT = "📞 Admin bilan bog'lanish"
    SHOP_BTN_ABOUT = "ℹ️ Bot haqida"
    SHOP_BTN_ADMIN = "👑 Admin panel"

    # Shop bot admin
    SHOP_ADMIN_ADD_PRODUCT = "➕ Mahsulot qo'shish"
    SHOP_ADMIN_PRODUCTS = "📦 Mahsulotlar"
    SHOP_ADMIN_CATEGORIES = "📂 Kategoriyalar"
    SHOP_ADMIN_ORDERS = "📋 Buyurtmalar"
    SHOP_ADMIN_BROADCAST = "📣 Xabar yuborish"
    SHOP_ADMIN_STATS = "📊 Statistika"
    SHOP_ADMIN_SETTINGS = "⚙️ Sozlamalar"

    # Buyurtma holatlari
    ORDER_STATUS_NEW = "🆕 Yangi"
    ORDER_STATUS_PROCESSING = "⏳ Jarayonda"
    ORDER_STATUS_SHIPPED = "🚚 Yetkazilmoqda"
    ORDER_STATUS_DELIVERED = "✅ Yetkazildi"
    ORDER_STATUS_CANCELLED = "❌ Bekor qilindi"

    # Footer
    FOOTER_FREE = "\n\n<i>Powered by @ShopMakerUzBot</i>"
    FOOTER_PREMIUM = ""

    # Xatolar
    ERR_INVALID_TOKEN = "❌ Noto'g'ri token! Iltimos, @BotFather dan olgan tokeningizni kiriting."
    ERR_TOKEN_USED = "❌ Bu token allaqachon ishlatilgan!"
    ERR_BOT_LIMIT = "❌ Botlar limitiga yetdingiz! Premium rejaga o'ting."
    ERR_BLOCKED = "❌ Siz bloklangansiz. Muammo uchun @ShopMakerUzBot admin bilan bog'laning."
    ERR_NOT_FOUND = "❌ Ma'lumot topilmadi."
    ERR_UNKNOWN = "❌ Xato yuz berdi. Iltimos, qayta urinib ko'ring."

texts = Texts()
