"""
Ma'lumotlar bazasi so'rovlari — barcha CRUD operatsiyalar.
Har bir domenga oid funksiyalar shu yerda joylashgan.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Any
import aiosqlite
from .db import get_db

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# FOYDALANUVCHILAR
# ═══════════════════════════════════════════════════════════════════════════════

async def get_user(user_id: int) -> Optional[aiosqlite.Row]:
    """Foydalanuvchini ID bo'yicha oladi."""
    async with get_db() as db:
        async with db.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ) as cur:
            return await cur.fetchone()


async def get_or_create_user(
    user_id: int,
    full_name: str,
    username: Optional[str] = None
) -> tuple[aiosqlite.Row, bool]:
    """Foydalanuvchini oladi yoki yaratadi. (row, created) qaytaradi."""
    async with get_db() as db:
        async with db.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()

        if row:
            # Mavjud foydalanuvchini yangilaydi
            await db.execute(
                """UPDATE users SET full_name=?, username=?, updated_at=CURRENT_TIMESTAMP
                   WHERE id=?""",
                (full_name, username, user_id)
            )
            await db.commit()
            async with db.execute("SELECT * FROM users WHERE id=?", (user_id,)) as cur:
                row = await cur.fetchone()
            return row, False
        else:
            # Yangi foydalanuvchi yaratadi
            await db.execute(
                """INSERT INTO users (id, full_name, username) VALUES (?, ?, ?)""",
                (user_id, full_name, username)
            )
            await db.commit()
            async with db.execute("SELECT * FROM users WHERE id=?", (user_id,)) as cur:
                row = await cur.fetchone()
            return row, True


async def update_user(user_id: int, **kwargs) -> None:
    """Foydalanuvchi ma'lumotlarini yangilaydi."""
    if not kwargs:
        return
    cols = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [user_id]
    async with get_db() as db:
        await db.execute(
            f"UPDATE users SET {cols}, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            vals
        )
        await db.commit()


async def set_user_plan(
    user_id: int,
    plan: str,
    days: int,
    given_by: Optional[int] = None,
    note: Optional[str] = None
) -> None:
    """Foydalanuvchiga reja beradi."""
    expires = datetime.now() + timedelta(days=days) if days > 0 else None
    async with get_db() as db:
        await db.execute(
            """UPDATE users SET plan=?, plan_expires_at=?, updated_at=CURRENT_TIMESTAMP
               WHERE id=?""",
            (plan, expires, user_id)
        )
        await db.execute(
            """INSERT INTO plans (user_id, plan, expires_at, given_by, note)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, plan, expires, given_by, note)
        )
        await db.commit()


async def reset_user_plan(user_id: int) -> None:
    """Foydalanuvchi rejasini bekor qiladi (free ga qaytaradi)."""
    async with get_db() as db:
        await db.execute(
            """UPDATE users SET plan='free', plan_expires_at=NULL,
               updated_at=CURRENT_TIMESTAMP WHERE id=?""",
            (user_id,)
        )
        await db.commit()


async def check_and_expire_plans() -> list[int]:
    """Muddati o'tgan rejalarni yangilaydi. O'zgargan user_id larni qaytaradi."""
    now = datetime.now()
    async with get_db() as db:
        async with db.execute(
            "SELECT id FROM users WHERE plan != 'free' AND plan_expires_at <= ?",
            (now,)
        ) as cur:
            rows = await cur.fetchall()

        expired_ids = [r["id"] for r in rows]
        if expired_ids:
            placeholders = ",".join("?" * len(expired_ids))
            await db.execute(
                f"""UPDATE users SET plan='free', plan_expires_at=NULL,
                    updated_at=CURRENT_TIMESTAMP WHERE id IN ({placeholders})""",
                expired_ids
            )
            await db.commit()

        # Qo'shimcha botlarni qulflaydi
        for uid in expired_ids:
            await _lock_extra_bots(db, uid)

        return expired_ids


async def _lock_extra_bots(db: aiosqlite.Connection, owner_id: int) -> None:
    """Free rejada 1 tadan ortiq botlarni qulflaydi."""
    async with db.execute(
        "SELECT id FROM bots WHERE owner_id=? ORDER BY created_at ASC",
        (owner_id,)
    ) as cur:
        bot_rows = await cur.fetchall()

    for i, row in enumerate(bot_rows):
        locked = 0 if i == 0 else 1
        await db.execute(
            "UPDATE bots SET is_locked=? WHERE id=?", (locked, row["id"])
        )
    await db.commit()


async def get_all_users(limit: int = 50, offset: int = 0) -> list[aiosqlite.Row]:
    """Barcha foydalanuvchilarni qaytaradi."""
    async with get_db() as db:
        async with db.execute(
            "SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        ) as cur:
            return await cur.fetchall()


async def count_users_by_plan() -> dict:
    """Reja bo'yicha foydalanuvchilar sonini qaytaradi."""
    async with get_db() as db:
        async with db.execute(
            "SELECT plan, COUNT(*) as cnt FROM users GROUP BY plan"
        ) as cur:
            rows = await cur.fetchall()
    return {r["plan"]: r["cnt"] for r in rows}


async def get_total_users() -> int:
    """Jami foydalanuvchilar sonini qaytaradi."""
    async with get_db() as db:
        async with db.execute("SELECT COUNT(*) as cnt FROM users") as cur:
            row = await cur.fetchone()
    return row["cnt"] if row else 0


# ═══════════════════════════════════════════════════════════════════════════════
# BOTLAR
# ═══════════════════════════════════════════════════════════════════════════════

async def create_bot(
    owner_id: int,
    token: str,
    bot_username: str,
    bot_name: str
) -> int:
    """Yangi bot yaratadi va bot ID sini qaytaradi."""
    async with get_db() as db:
        cur = await db.execute(
            """INSERT INTO bots (owner_id, token, bot_username, bot_name)
               VALUES (?, ?, ?, ?)""",
            (owner_id, token, bot_username, bot_name)
        )
        bot_id = cur.lastrowid
        await db.commit()
    return bot_id


async def get_bot(bot_id: int) -> Optional[aiosqlite.Row]:
    """Bot ID bo'yicha botni oladi."""
    async with get_db() as db:
        async with db.execute(
            "SELECT * FROM bots WHERE id = ?", (bot_id,)
        ) as cur:
            return await cur.fetchone()


async def get_bot_by_token(token: str) -> Optional[aiosqlite.Row]:
    """Token bo'yicha botni oladi."""
    async with get_db() as db:
        async with db.execute(
            "SELECT * FROM bots WHERE token = ?", (token,)
        ) as cur:
            return await cur.fetchone()


async def get_user_bots(owner_id: int) -> list[aiosqlite.Row]:
    """Foydalanuvchining barcha botlarini qaytaradi."""
    async with get_db() as db:
        async with db.execute(
            "SELECT * FROM bots WHERE owner_id = ? ORDER BY created_at DESC",
            (owner_id,)
        ) as cur:
            return await cur.fetchall()


async def get_all_active_bots() -> list[aiosqlite.Row]:
    """Barcha faol botlarni qaytaradi (main bot uchun startup)."""
    async with get_db() as db:
        async with db.execute(
            "SELECT * FROM bots WHERE is_active = 1 AND is_locked = 0"
        ) as cur:
            return await cur.fetchall()


async def update_bot(bot_id: int, **kwargs) -> None:
    """Bot ma'lumotlarini yangilaydi."""
    if not kwargs:
        return
    cols = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [bot_id]
    async with get_db() as db:
        await db.execute(
            f"UPDATE bots SET {cols}, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            vals
        )
        await db.commit()


async def delete_bot(bot_id: int) -> None:
    """Botni o'chiradi (kaskad bilan mahsulotlar, buyurtmalar ham o'chadi)."""
    async with get_db() as db:
        await db.execute("DELETE FROM bots WHERE id=?", (bot_id,))
        await db.commit()


async def count_user_bots(owner_id: int) -> int:
    """Foydalanuvchining botlar sonini qaytaradi."""
    async with get_db() as db:
        async with db.execute(
            "SELECT COUNT(*) as cnt FROM bots WHERE owner_id=?", (owner_id,)
        ) as cur:
            row = await cur.fetchone()
    return row["cnt"] if row else 0


async def get_total_bots() -> int:
    """Jami botlar sonini qaytaradi."""
    async with get_db() as db:
        async with db.execute("SELECT COUNT(*) as cnt FROM bots") as cur:
            row = await cur.fetchone()
    return row["cnt"] if row else 0


# ═══════════════════════════════════════════════════════════════════════════════
# KATEGORIYALAR
# ═══════════════════════════════════════════════════════════════════════════════

async def create_category(bot_id: int, name: str, icon: str = "📦") -> int:
    """Yangi kategoriya yaratadi."""
    async with get_db() as db:
        cur = await db.execute(
            "INSERT INTO categories (bot_id, name, icon) VALUES (?, ?, ?)",
            (bot_id, name, icon)
        )
        cat_id = cur.lastrowid
        await db.commit()
    return cat_id


async def get_categories(bot_id: int) -> list[aiosqlite.Row]:
    """Bot kategoriyalarini qaytaradi."""
    async with get_db() as db:
        async with db.execute(
            "SELECT * FROM categories WHERE bot_id=? ORDER BY sort_order, name",
            (bot_id,)
        ) as cur:
            return await cur.fetchall()


async def get_category(cat_id: int) -> Optional[aiosqlite.Row]:
    """Kategoriyani ID bo'yicha oladi."""
    async with get_db() as db:
        async with db.execute(
            "SELECT * FROM categories WHERE id=?", (cat_id,)
        ) as cur:
            return await cur.fetchone()


async def delete_category(cat_id: int) -> None:
    """Kategoriyani o'chiradi."""
    async with get_db() as db:
        await db.execute("DELETE FROM categories WHERE id=?", (cat_id,))
        await db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# MAHSULOTLAR
# ═══════════════════════════════════════════════════════════════════════════════

async def create_product(
    bot_id: int,
    name: str,
    price: float,
    description: Optional[str] = None,
    category_id: Optional[int] = None,
    photo_id: Optional[str] = None
) -> int:
    """Yangi mahsulot yaratadi."""
    async with get_db() as db:
        cur = await db.execute(
            """INSERT INTO products (bot_id, name, price, description, category_id, photo_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (bot_id, name, price, description, category_id, photo_id)
        )
        prod_id = cur.lastrowid
        await db.commit()
    return prod_id


async def get_products(
    bot_id: int,
    category_id: Optional[int] = None,
    available_only: bool = True
) -> list[aiosqlite.Row]:
    """Bot mahsulotlarini qaytaradi."""
    async with get_db() as db:
        query = "SELECT * FROM products WHERE bot_id=?"
        params: list = [bot_id]

        if category_id is not None:
            query += " AND category_id=?"
            params.append(category_id)

        if available_only:
            query += " AND is_available=1"

        query += " ORDER BY sort_order, name"

        async with db.execute(query, params) as cur:
            return await cur.fetchall()


async def get_product(product_id: int) -> Optional[aiosqlite.Row]:
    """Mahsulotni ID bo'yicha oladi."""
    async with get_db() as db:
        async with db.execute(
            "SELECT * FROM products WHERE id=?", (product_id,)
        ) as cur:
            return await cur.fetchone()


async def update_product(product_id: int, **kwargs) -> None:
    """Mahsulotni yangilaydi."""
    if not kwargs:
        return
    cols = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [product_id]
    async with get_db() as db:
        await db.execute(
            f"UPDATE products SET {cols}, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            vals
        )
        await db.commit()


async def delete_product(product_id: int) -> None:
    """Mahsulotni o'chiradi."""
    async with get_db() as db:
        await db.execute("DELETE FROM products WHERE id=?", (product_id,))
        await db.commit()


async def search_products(bot_id: int, query: str) -> list[aiosqlite.Row]:
    """Mahsulotlarni qidiradi."""
    like = f"%{query}%"
    async with get_db() as db:
        async with db.execute(
            """SELECT * FROM products WHERE bot_id=? AND is_available=1
               AND (name LIKE ? OR description LIKE ?)
               ORDER BY name""",
            (bot_id, like, like)
        ) as cur:
            return await cur.fetchall()


async def count_products(bot_id: int) -> int:
    """Bot mahsulotlar sonini qaytaradi."""
    async with get_db() as db:
        async with db.execute(
            "SELECT COUNT(*) as cnt FROM products WHERE bot_id=?", (bot_id,)
        ) as cur:
            row = await cur.fetchone()
    return row["cnt"] if row else 0


# ═══════════════════════════════════════════════════════════════════════════════
# SAVAT (CART)
# ═══════════════════════════════════════════════════════════════════════════════

async def add_to_cart(bot_id: int, user_id: int, product_id: int, qty: int = 1) -> None:
    """Savatga mahsulot qo'shadi yoki miqdorini oshiradi."""
    async with get_db() as db:
        await db.execute(
            """INSERT INTO carts (bot_id, user_id, product_id, quantity)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(bot_id, user_id, product_id)
               DO UPDATE SET quantity = quantity + excluded.quantity""",
            (bot_id, user_id, product_id, qty)
        )
        await db.commit()


async def set_cart_qty(bot_id: int, user_id: int, product_id: int, qty: int) -> None:
    """Savatdagi mahsulot miqdorini o'rnatadi."""
    if qty <= 0:
        await remove_from_cart(bot_id, user_id, product_id)
        return
    async with get_db() as db:
        await db.execute(
            """INSERT INTO carts (bot_id, user_id, product_id, quantity)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(bot_id, user_id, product_id)
               DO UPDATE SET quantity = excluded.quantity""",
            (bot_id, user_id, product_id, qty)
        )
        await db.commit()


async def remove_from_cart(bot_id: int, user_id: int, product_id: int) -> None:
    """Savatdan mahsulotni olib tashlaydi."""
    async with get_db() as db:
        await db.execute(
            "DELETE FROM carts WHERE bot_id=? AND user_id=? AND product_id=?",
            (bot_id, user_id, product_id)
        )
        await db.commit()


async def clear_cart(bot_id: int, user_id: int) -> None:
    """Savatni tozalaydi."""
    async with get_db() as db:
        await db.execute(
            "DELETE FROM carts WHERE bot_id=? AND user_id=?",
            (bot_id, user_id)
        )
        await db.commit()


async def get_cart(bot_id: int, user_id: int) -> list[dict]:
    """Foydalanuvchi savatini mahsulot ma'lumotlari bilan qaytaradi."""
    async with get_db() as db:
        async with db.execute(
            """SELECT c.product_id, c.quantity, p.name, p.price, p.photo_id
               FROM carts c
               JOIN products p ON p.id = c.product_id
               WHERE c.bot_id=? AND c.user_id=? AND p.is_available=1
               ORDER BY c.created_at""",
            (bot_id, user_id)
        ) as cur:
            rows = await cur.fetchall()
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
# BUYURTMALAR
# ═══════════════════════════════════════════════════════════════════════════════

async def create_order(
    bot_id: int,
    customer_id: int,
    customer_name: str,
    items: list[dict],
    total_price: float,
    customer_phone: Optional[str] = None,
    customer_address: Optional[str] = None,
    note: Optional[str] = None
) -> int:
    """Yangi buyurtma yaratadi."""
    items_json = json.dumps(items, ensure_ascii=False)
    async with get_db() as db:
        cur = await db.execute(
            """INSERT INTO orders
               (bot_id, customer_id, customer_name, customer_phone,
                customer_address, items, total_price, note)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (bot_id, customer_id, customer_name, customer_phone,
             customer_address, items_json, total_price, note)
        )
        order_id = cur.lastrowid
        await db.commit()
    return order_id


async def get_order(order_id: int) -> Optional[aiosqlite.Row]:
    """Buyurtmani ID bo'yicha oladi."""
    async with get_db() as db:
        async with db.execute(
            "SELECT * FROM orders WHERE id=?", (order_id,)
        ) as cur:
            return await cur.fetchone()


async def get_bot_orders(
    bot_id: int,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> list[aiosqlite.Row]:
    """Bot buyurtmalarini qaytaradi."""
    async with get_db() as db:
        if status:
            query = "SELECT * FROM orders WHERE bot_id=? AND status=? ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params = (bot_id, status, limit, offset)
        else:
            query = "SELECT * FROM orders WHERE bot_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params = (bot_id, limit, offset)
        async with db.execute(query, params) as cur:
            return await cur.fetchall()


async def get_user_orders(bot_id: int, customer_id: int) -> list[aiosqlite.Row]:
    """Foydalanuvchi buyurtmalarini qaytaradi."""
    async with get_db() as db:
        async with db.execute(
            "SELECT * FROM orders WHERE bot_id=? AND customer_id=? ORDER BY created_at DESC",
            (bot_id, customer_id)
        ) as cur:
            return await cur.fetchall()


async def update_order_status(order_id: int, status: str) -> None:
    """Buyurtma holatini yangilaydi."""
    async with get_db() as db:
        await db.execute(
            "UPDATE orders SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (status, order_id)
        )
        await db.commit()


async def count_orders(bot_id: int, status: Optional[str] = None) -> int:
    """Buyurtmalar sonini qaytaradi."""
    async with get_db() as db:
        if status:
            async with db.execute(
                "SELECT COUNT(*) as cnt FROM orders WHERE bot_id=? AND status=?",
                (bot_id, status)
            ) as cur:
                row = await cur.fetchone()
        else:
            async with db.execute(
                "SELECT COUNT(*) as cnt FROM orders WHERE bot_id=?", (bot_id,)
            ) as cur:
                row = await cur.fetchone()
    return row["cnt"] if row else 0


async def get_orders_revenue(bot_id: int) -> float:
    """Bot jami daromadini qaytaradi."""
    async with get_db() as db:
        async with db.execute(
            "SELECT COALESCE(SUM(total_price),0) as total FROM orders WHERE bot_id=? AND status='delivered'",
            (bot_id,)
        ) as cur:
            row = await cur.fetchone()
    return row["total"] if row else 0


# ═══════════════════════════════════════════════════════════════════════════════
# SHOP FOYDALANUVCHILARI
# ═══════════════════════════════════════════════════════════════════════════════

async def get_or_create_shop_user(
    bot_id: int,
    user_id: int,
    full_name: str,
    username: Optional[str] = None
) -> None:
    """Shop foydalanuvchisini yaratadi yoki yangilaydi."""
    async with get_db() as db:
        await db.execute(
            """INSERT INTO shop_users (bot_id, user_id, full_name, username)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(bot_id, user_id) DO UPDATE
               SET full_name=excluded.full_name, username=excluded.username""",
            (bot_id, user_id, full_name, username)
        )
        await db.commit()


async def set_shop_user_phone(bot_id: int, user_id: int, phone: str) -> None:
    """Shop foydalanuvchisining telefon raqamini saqlaydi."""
    async with get_db() as db:
        await db.execute(
            "UPDATE shop_users SET phone=? WHERE bot_id=? AND user_id=?",
            (phone, bot_id, user_id)
        )
        await db.commit()


async def get_shop_user(bot_id: int, user_id: int) -> Optional[aiosqlite.Row]:
    """Shop foydalanuvchisini oladi."""
    async with get_db() as db:
        async with db.execute(
            "SELECT * FROM shop_users WHERE bot_id=? AND user_id=?",
            (bot_id, user_id)
        ) as cur:
            return await cur.fetchone()


async def get_shop_users(bot_id: int) -> list[aiosqlite.Row]:
    """Barcha shop foydalanuvchilarini qaytaradi."""
    async with get_db() as db:
        async with db.execute(
            "SELECT * FROM shop_users WHERE bot_id=? ORDER BY created_at DESC",
            (bot_id,)
        ) as cur:
            return await cur.fetchall()


async def count_shop_users(bot_id: int) -> int:
    """Shop foydalanuvchilar sonini qaytaradi."""
    async with get_db() as db:
        async with db.execute(
            "SELECT COUNT(*) as cnt FROM shop_users WHERE bot_id=?", (bot_id,)
        ) as cur:
            row = await cur.fetchone()
    return row["cnt"] if row else 0


# ═══════════════════════════════════════════════════════════════════════════════
# TO'LOVLAR
# ═══════════════════════════════════════════════════════════════════════════════

async def create_payment(
    user_id: int,
    plan: str,
    amount: float,
    method: str
) -> int:
    """Yangi to'lov yaratadi."""
    async with get_db() as db:
        cur = await db.execute(
            "INSERT INTO payments (user_id, plan, amount, method) VALUES (?, ?, ?, ?)",
            (user_id, plan, amount, method)
        )
        pay_id = cur.lastrowid
        await db.commit()
    return pay_id


async def get_payment(payment_id: int) -> Optional[aiosqlite.Row]:
    """To'lovni ID bo'yicha oladi."""
    async with get_db() as db:
        async with db.execute(
            "SELECT * FROM payments WHERE id=?", (payment_id,)
        ) as cur:
            return await cur.fetchone()


async def get_pending_payments() -> list[aiosqlite.Row]:
    """Kutilayotgan to'lovlarni qaytaradi."""
    async with get_db() as db:
        async with db.execute(
            "SELECT p.*, u.full_name, u.username FROM payments p "
            "JOIN users u ON u.id=p.user_id "
            "WHERE p.status='pending' ORDER BY p.created_at DESC"
        ) as cur:
            return await cur.fetchall()


async def update_payment(payment_id: int, **kwargs) -> None:
    """To'lovni yangilaydi."""
    cols = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [payment_id]
    async with get_db() as db:
        await db.execute(
            f"UPDATE payments SET {cols}, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            vals
        )
        await db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# PROMO KODLAR
# ═══════════════════════════════════════════════════════════════════════════════

async def create_promo(
    code: str,
    plan: str,
    days: int,
    max_uses: int,
    created_by: int,
    expires_at: Optional[datetime] = None
) -> int:
    """Yangi promo kod yaratadi."""
    async with get_db() as db:
        cur = await db.execute(
            """INSERT INTO promo_codes (code, plan, days, max_uses, created_by, expires_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (code, plan, days, max_uses, created_by, expires_at)
        )
        promo_id = cur.lastrowid
        await db.commit()
    return promo_id


async def get_promo(code: str) -> Optional[aiosqlite.Row]:
    """Promo kodni oladi."""
    async with get_db() as db:
        async with db.execute(
            "SELECT * FROM promo_codes WHERE code=? AND is_active=1",
            (code.upper(),)
        ) as cur:
            return await cur.fetchone()


async def use_promo(code_id: int, user_id: int) -> None:
    """Promo kodni ishlatadi."""
    async with get_db() as db:
        await db.execute(
            "INSERT INTO promo_usages (code_id, user_id) VALUES (?, ?)",
            (code_id, user_id)
        )
        await db.execute(
            "UPDATE promo_codes SET used_count=used_count+1 WHERE id=?",
            (code_id,)
        )
        await db.commit()


async def has_used_promo(code_id: int, user_id: int) -> bool:
    """Foydalanuvchi promo kodni ishlatganligini tekshiradi."""
    async with get_db() as db:
        async with db.execute(
            "SELECT id FROM promo_usages WHERE code_id=? AND user_id=?",
            (code_id, user_id)
        ) as cur:
            return await cur.fetchone() is not None


async def get_all_promos() -> list[aiosqlite.Row]:
    """Barcha promo kodlarni qaytaradi."""
    async with get_db() as db:
        async with db.execute(
            "SELECT * FROM promo_codes ORDER BY created_at DESC"
        ) as cur:
            return await cur.fetchall()


# ═══════════════════════════════════════════════════════════════════════════════
# SOZLAMALAR
# ═══════════════════════════════════════════════════════════════════════════════

async def get_setting(key: str, default: str = "") -> str:
    """Sozlamani oladi."""
    async with get_db() as db:
        async with db.execute(
            "SELECT value FROM settings WHERE key=?", (key,)
        ) as cur:
            row = await cur.fetchone()
    return row["value"] if row else default


async def set_setting(key: str, value: str) -> None:
    """Sozlamani o'rnatadi."""
    async with get_db() as db:
        await db.execute(
            """INSERT INTO settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)
               ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at""",
            (key, value)
        )
        await db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# TIZIM LOGLARI
# ═══════════════════════════════════════════════════════════════════════════════

async def add_log(
    action: str,
    level: str = "INFO",
    user_id: Optional[int] = None,
    detail: Optional[str] = None
) -> None:
    """Tizim logiga yozadi."""
    async with get_db() as db:
        await db.execute(
            "INSERT INTO system_logs (level, action, user_id, detail) VALUES (?, ?, ?, ?)",
            (level, action, user_id, detail)
        )
        await db.commit()


async def get_logs(limit: int = 100) -> list[aiosqlite.Row]:
    """Tizim loglarini qaytaradi."""
    async with get_db() as db:
        async with db.execute(
            "SELECT * FROM system_logs ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ) as cur:
            return await cur.fetchall()


# ═══════════════════════════════════════════════════════════════════════════════
# STATISTIKA
# ═══════════════════════════════════════════════════════════════════════════════

async def get_global_stats() -> dict:
    """Global statistikani qaytaradi."""
    total_users = await get_total_users()
    total_bots = await get_total_bots()
    plan_counts = await count_users_by_plan()

    async with get_db() as db:
        async with db.execute("SELECT COUNT(*) as cnt FROM orders") as cur:
            row = await cur.fetchone()
        total_orders = row["cnt"] if row else 0

        async with db.execute("SELECT COUNT(*) as cnt FROM payments WHERE status='paid'") as cur:
            row = await cur.fetchone()
        total_payments = row["cnt"] if row else 0

    return {
        "total_users": total_users,
        "total_bots": total_bots,
        "total_orders": total_orders,
        "total_payments": total_payments,
        "free_users": plan_counts.get("free", 0),
        "premium_users": plan_counts.get("premium", 0),
        "comfort_users": plan_counts.get("comfort", 0),
    }


async def get_bot_stats(bot_id: int) -> dict:
    """Bot statistikasini qaytaradi."""
    total_products = await count_products(bot_id)
    total_users = await count_shop_users(bot_id)
    total_orders = await count_orders(bot_id)
    new_orders = await count_orders(bot_id, status="new")
    revenue = await get_orders_revenue(bot_id)

    async with get_db() as db:
        async with db.execute(
            "SELECT COUNT(*) as cnt FROM categories WHERE bot_id=?", (bot_id,)
        ) as cur:
            row = await cur.fetchone()
        total_categories = row["cnt"] if row else 0

    return {
        "total_products": total_products,
        "total_categories": total_categories,
        "total_users": total_users,
        "total_orders": total_orders,
        "new_orders": new_orders,
        "revenue": revenue,
    }
