"""
Bot Manager — barcha shop botlarini boshqaradi.
Har bir shop boti o'z Bot va Dispatcher instanceiga ega.
asyncio yordamida parallel ishlaydi.
"""

import asyncio
import logging
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

logger = logging.getLogger(__name__)

# Faol bot instancelari: {bot_id: {"bot": Bot, "dp": Dispatcher, "task": Task}}
_active_bots: dict[int, dict] = {}


def _build_shop_dispatcher(bot_id: int, bot_data: dict) -> Dispatcher:
    """Shop bot uchun Dispatcher yaratadi va handlerlarni ro'yxatdan o'tkazadi."""
    from middlewares.auth import ShopBotMiddleware
    from handlers.shop_bot import (
        start as shop_start,
        products as shop_products,
        categories as shop_categories,
        cart as shop_cart,
        orders as shop_orders,
        search as shop_search,
        admin as shop_admin,
        settings as shop_settings,
    )

    dp = Dispatcher()

    # Middleware
    dp.message.middleware(ShopBotMiddleware(bot_id, bot_data))
    dp.callback_query.middleware(ShopBotMiddleware(bot_id, bot_data))

    # Routerlarni qo'shamiz
    dp.include_router(shop_start.router)
    dp.include_router(shop_products.router)
    dp.include_router(shop_categories.router)
    dp.include_router(shop_search.router)
    dp.include_router(shop_cart.router)
    dp.include_router(shop_orders.router)
    dp.include_router(shop_admin.router)
    dp.include_router(shop_settings.router)

    return dp


async def start_shop_bot(bot_id: int, token: str, bot_data: dict) -> bool:
    """
    Shop botini ishga tushiradi.
    Allaqachon ishlayotgan bo'lsa, False qaytaradi.
    """
    if bot_id in _active_bots:
        logger.debug("Bot #%d allaqachon ishlayapti.", bot_id)
        return False

    try:
        bot = Bot(
            token=token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        dp = _build_shop_dispatcher(bot_id, bot_data)

        # Polling ni async task sifatida ishga tushiramiz
        task = asyncio.create_task(
            dp.start_polling(bot, handle_signals=False),
            name=f"shop_bot_{bot_id}"
        )

        _active_bots[bot_id] = {
            "bot": bot,
            "dp": dp,
            "task": task,
            "bot_data": bot_data,
        }

        logger.info("✅ Shop bot #%d (@%s) ishga tushirildi.", bot_id, bot_data.get("bot_username"))
        return True

    except Exception as e:
        logger.error("❌ Shop bot #%d ishga tushirishda xato: %s", bot_id, e)
        return False


async def stop_shop_bot(bot_id: int) -> bool:
    """Shop botini to'xtatadi."""
    if bot_id not in _active_bots:
        return False

    entry = _active_bots.pop(bot_id)
    try:
        task: asyncio.Task = entry["task"]
        task.cancel()
        try:
            await asyncio.wait_for(asyncio.shield(task), timeout=5)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass

        bot: Bot = entry["bot"]
        await bot.session.close()

        logger.info("⏹ Shop bot #%d to'xtatildi.", bot_id)
        return True
    except Exception as e:
        logger.error("Shop bot #%d to'xtatishda xato: %s", bot_id, e)
        return False


async def restart_shop_bot(bot_id: int, token: str, bot_data: dict) -> bool:
    """Shop botini qayta ishga tushiradi."""
    await stop_shop_bot(bot_id)
    await asyncio.sleep(1)
    return await start_shop_bot(bot_id, token, bot_data)


async def get_shop_bot(bot_id: int) -> Optional[Bot]:
    """Faol shop botini qaytaradi."""
    entry = _active_bots.get(bot_id)
    return entry["bot"] if entry else None


def is_bot_running(bot_id: int) -> bool:
    """Shop boti ishlaymiyotganligini tekshiradi."""
    if bot_id not in _active_bots:
        return False
    entry = _active_bots[bot_id]
    task: asyncio.Task = entry["task"]
    return not task.done()


def get_active_bot_count() -> int:
    """Faol botlar sonini qaytaradi."""
    return sum(1 for e in _active_bots.values() if not e["task"].done())


async def load_all_bots() -> int:
    """
    Barcha faol shop botlarini ma'lumotlar bazasidan yuklab,
    ishga tushiradi. Startup paytida chaqiriladi.
    """
    from database.queries import get_all_active_bots

    bots = await get_all_active_bots()
    started = 0
    tasks = []

    for row in bots:
        bot_data = dict(row)
        tasks.append(start_shop_bot(row["id"], row["token"], bot_data))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    for r in results:
        if r is True:
            started += 1

    logger.info("🚀 Jami %d shop bot ishga tushirildi.", started)
    return started


async def send_to_shop_bot(bot_id: int, chat_id: int, text: str, **kwargs) -> bool:
    """Shop bot orqali xabar yuboradi."""
    bot = await get_shop_bot(bot_id)
    if not bot:
        return False
    try:
        await bot.send_message(chat_id, text, **kwargs)
        return True
    except Exception as e:
        logger.error("Shop bot #%d xabar yuborishda xato: %s", bot_id, e)
        return False


async def broadcast_to_shop_users(
    bot_id: int,
    user_ids: list[int],
    text: str,
    **kwargs
) -> tuple[int, int]:
    """
    Barcha shop foydalanuvchilariga xabar yuboradi.
    (yuborildi, xato) ni qaytaradi.
    """
    bot = await get_shop_bot(bot_id)
    if not bot:
        return 0, len(user_ids)

    sent = 0
    failed = 0

    for uid in user_ids:
        try:
            await bot.send_message(uid, text, **kwargs)
            sent += 1
            await asyncio.sleep(0.05)  # Flood limitga qarshi
        except Exception as e:
            logger.warning("Broadcast uid=%d ga yuborishda xato: %s", uid, e)
            failed += 1

    return sent, failed
