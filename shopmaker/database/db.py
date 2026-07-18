"""
Ma'lumotlar bazasi — SQLite + aiosqlite
Barcha jadvallar va asosiy so'rovlar shu yerda.
"""

import aiosqlite
import logging
from datetime import datetime, timedelta
from typing import Optional, Any

logger = logging.getLogger(__name__)

_db_path: str = "shopmaker.db"


async def get_db() -> aiosqlite.Connection:
    """Ma'lumotlar bazasiga ulanishni qaytaradi."""
    conn = await aiosqlite.connect(_db_path)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA journal_mode=WAL")
    await conn.execute("PRAGMA foreign_keys=ON")
    return conn


class Database:
    """SQLite ma'lumotlar bazasini boshqaruvchi sinf."""

    def __init__(self, db_path: str):
        global _db_path
        _db_path = db_path
        self.path = db_path

    async def init(self):
        """Barcha jadvallarni yaratadi."""
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            await db.execute("PRAGMA journal_mode=WAL")
            await db.execute("PRAGMA foreign_keys=ON")
            await self._create_tables(db)
            await db.commit()
        logger.info("✅ Ma'lumotlar bazasi tayyor: %s", self.path)

    async def _create_tables(self, db: aiosqlite.Connection):
        """Jadvallarni yaratadi."""

        # ── Foydalanuvchilar ────────────────────────────────────────────────
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY,        -- Telegram user_id
            username    TEXT,
            full_name   TEXT    NOT NULL,
            phone       TEXT,
            plan        TEXT    NOT NULL DEFAULT 'free',  -- free | comfort | premium
            plan_expires_at DATETIME,
            is_blocked  INTEGER NOT NULL DEFAULT 0,
            is_registered INTEGER NOT NULL DEFAULT 1,
            language    TEXT    NOT NULL DEFAULT 'uz',
            created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # ── Botlar ──────────────────────────────────────────────────────────
        await db.execute("""
        CREATE TABLE IF NOT EXISTS bots (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token       TEXT    NOT NULL UNIQUE,
            bot_username TEXT,
            bot_name    TEXT,
            is_active   INTEGER NOT NULL DEFAULT 1,
            is_locked   INTEGER NOT NULL DEFAULT 0,
            theme       TEXT    NOT NULL DEFAULT 'default',
            welcome_text TEXT,
            about_text  TEXT,
            contact_info TEXT,
            footer_enabled INTEGER NOT NULL DEFAULT 1,
            created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # ── Mahsulotlar ─────────────────────────────────────────────────────
        await db.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            bot_id      INTEGER NOT NULL REFERENCES bots(id) ON DELETE CASCADE,
            category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
            name        TEXT    NOT NULL,
            description TEXT,
            price       REAL    NOT NULL DEFAULT 0,
            photo_id    TEXT,
            is_available INTEGER NOT NULL DEFAULT 1,
            sort_order  INTEGER NOT NULL DEFAULT 0,
            created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # ── Kategoriyalar ───────────────────────────────────────────────────
        await db.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            bot_id      INTEGER NOT NULL REFERENCES bots(id) ON DELETE CASCADE,
            name        TEXT    NOT NULL,
            icon        TEXT    DEFAULT '📦',
            sort_order  INTEGER NOT NULL DEFAULT 0,
            created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # ── Buyurtmalar ─────────────────────────────────────────────────────
        await db.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            bot_id      INTEGER NOT NULL REFERENCES bots(id) ON DELETE CASCADE,
            customer_id INTEGER NOT NULL,
            customer_name TEXT,
            customer_phone TEXT,
            customer_address TEXT,
            items       TEXT    NOT NULL,   -- JSON: [{product_id, name, price, qty}]
            total_price REAL    NOT NULL DEFAULT 0,
            status      TEXT    NOT NULL DEFAULT 'new',  -- new|processing|shipped|delivered|cancelled
            note        TEXT,
            created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # ── Savatlar ────────────────────────────────────────────────────────
        await db.execute("""
        CREATE TABLE IF NOT EXISTS carts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            bot_id      INTEGER NOT NULL REFERENCES bots(id) ON DELETE CASCADE,
            user_id     INTEGER NOT NULL,
            product_id  INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
            quantity    INTEGER NOT NULL DEFAULT 1,
            created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(bot_id, user_id, product_id)
        )
        """)

        # ── Rejalar tarixi ──────────────────────────────────────────────────
        await db.execute("""
        CREATE TABLE IF NOT EXISTS plans (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            plan        TEXT    NOT NULL,
            started_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            expires_at  DATETIME,
            given_by    INTEGER,   -- super admin id
            note        TEXT
        )
        """)

        # ── To'lovlar ───────────────────────────────────────────────────────
        await db.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            plan        TEXT    NOT NULL,
            amount      REAL    NOT NULL,
            method      TEXT    NOT NULL,   -- click|payme|uzum|manual
            status      TEXT    NOT NULL DEFAULT 'pending',  -- pending|paid|failed|refunded
            transaction_id TEXT,
            receipt_photo TEXT,
            admin_note  TEXT,
            created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # ── Promo kodlar ────────────────────────────────────────────────────
        await db.execute("""
        CREATE TABLE IF NOT EXISTS promo_codes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            code        TEXT    NOT NULL UNIQUE,
            plan        TEXT    NOT NULL,
            days        INTEGER NOT NULL,
            max_uses    INTEGER NOT NULL DEFAULT 1,
            used_count  INTEGER NOT NULL DEFAULT 0,
            is_active   INTEGER NOT NULL DEFAULT 1,
            created_by  INTEGER NOT NULL,
            expires_at  DATETIME,
            created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # ── Promo kod foydalanishlari ────────────────────────────────────────
        await db.execute("""
        CREATE TABLE IF NOT EXISTS promo_usages (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            code_id     INTEGER NOT NULL REFERENCES promo_codes(id) ON DELETE CASCADE,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            used_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(code_id, user_id)
        )
        """)

        # ── Shop bot foydalanuvchilari (xaridorlar) ─────────────────────────
        await db.execute("""
        CREATE TABLE IF NOT EXISTS shop_users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            bot_id      INTEGER NOT NULL REFERENCES bots(id) ON DELETE CASCADE,
            user_id     INTEGER NOT NULL,
            username    TEXT,
            full_name   TEXT,
            phone       TEXT,
            is_blocked  INTEGER NOT NULL DEFAULT 0,
            created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(bot_id, user_id)
        )
        """)

        # ── Tizim sozlamalari ───────────────────────────────────────────────
        await db.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key     TEXT PRIMARY KEY,
            value   TEXT NOT NULL,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # ── Tizim loglari ───────────────────────────────────────────────────
        await db.execute("""
        CREATE TABLE IF NOT EXISTS system_logs (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            level   TEXT NOT NULL DEFAULT 'INFO',
            action  TEXT NOT NULL,
            user_id INTEGER,
            detail  TEXT,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # ── Default sozlamalar ──────────────────────────────────────────────
        defaults = [
            ("registration_enabled", "1"),
            ("premium_price", "10000"),
            ("comfort_price", "5000"),
            ("premium_days", "30"),
            ("comfort_days", "90"),
            ("support_username", "ShopMakerUzBot"),
        ]
        for key, value in defaults:
            await db.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )

        # ── Indekslar ───────────────────────────────────────────────────────
        await db.execute("CREATE INDEX IF NOT EXISTS idx_bots_owner ON bots(owner_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_products_bot ON products(bot_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_categories_bot ON categories(bot_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_orders_bot ON orders(bot_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_carts_bot_user ON carts(bot_id, user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_shop_users ON shop_users(bot_id, user_id)")
