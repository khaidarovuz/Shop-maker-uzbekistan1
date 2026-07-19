"""
ShopMakerUzBot — Asosiy kirish nuqtasi.
Barcha botlarni ishga tushiradi va boshqaradi.
"""

import asyncio
import logging
import logging.handlers
import os
import sys

# Event loop siyosatini o'rnatadi (Windows uchun)
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import config
from database.db import Database
from middlewares.auth import AuthMiddleware
from utils.bot_manager import load_all_bots

# ── Handlerlarni import qilamiz ──────────────────────────────────────────────
from handlers import start, my_bots, plans, admin

# ── Logger sozlamalari ───────────────────────────────────────────────────────

def setup_logging():
    """Logging tizimini sozlaydi."""
    os.makedirs("logs", exist_ok=True)
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    console.setLevel(logging.INFO)

    # File handler (rotatsiyali)
    file_handler = logging.handlers.RotatingFileHandler(
        config.LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    file_handler.setLevel(logging.DEBUG)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(console)
    root.addHandler(file_handler)

    # Uchinchi tomon kutubxonalar uchun level
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiosqlite").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)


# ── Asosiy bot sozlamalari ───────────────────────────────────────────────────

def create_main_bot() -> Bot:
    """Asosiy ShopMaker botini yaratadi."""
    return Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )


def create_main_dispatcher() -> Dispatcher:
    """Asosiy bot dispatcherini yaratadi."""
    dp = Dispatcher(storage=MemoryStorage())

    # Middleware
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())

    # Routerlarni qo'shamiz (tartib muhim!)
    dp.include_router(start.router)
    dp.include_router(my_bots.router)
    dp.include_router(plans.router)
    dp.include_router(admin.router)

    return dp


# ── Reja muddatlarini tekshiruvchi vazifa ────────────────────────────────────

async def plan_expiry_checker(bot: Bot):
    """
    Har soatda muddati o'tgan rejalarni tekshiradi.
    Muddati o'tgan foydalanuvchilarga xabar yuboradi.
    """
    import asyncio
    from database.queries import check_and_expire_plans

    logger = logging.getLogger("plan_checker")

    while True:
        try:
            expired_ids = await check_and_expire_plans()
            if expired_ids:
                logger.info("Muddati o'tgan rejalar: %d ta foydalanuvchi", len(expired_ids))
                for uid in expired_ids:
                    try:
                        await bot.send_message(
                            uid,
                            "📢 <b>Reja muddati tugadi!</b>\n\n"
                            "Rejangiz muddati tugadi va bepul rejaga o'tdingiz.\n"
                            "Rejangizni yangilash uchun «💎 Rejalar» bo'limiga o'ting.",
                            parse_mode="HTML"
                        )
                    except Exception:
                        pass
        except Exception as e:
            logger.error("Reja tekshiruv xatosi: %s", e)

        await asyncio.sleep(3600)  # Har soatda


# ── Render uchun health-check HTTP serveri ───────────────────────────────────

async def run_health_server():
    """
    Render web service PORT ni talab qiladi.
    Oddiy aiohttp server /health endpoint bilan ishga tushadi.
    """
    async def health(request):
        return web.Response(text="OK", status=200)

    async def root(request):
        return web.Response(text="ShopMakerUzBot ishlayapti ✅", status=200)

    app = web.Application()
    app.router.add_get("/", root)
    app.router.add_get("/health", health)

    port = int(os.environ.get("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.getLogger("main").info("🌐 Health server port=%d da ishlamoqda", port)

    # Abadiy kutadi (bot polling bilan parallel ishlaydi)
    while True:
        await asyncio.sleep(3600)


# ── Asosiy funksiya ──────────────────────────────────────────────────────────

async def main():
    """Asosiy dastur."""
    setup_logging()
    logger = logging.getLogger("main")

    logger.info("🚀 ShopMakerUzBot ishga tushmoqda...")

    # Ma'lumotlar bazasini tayyorlaydi
    db = Database(config.DB_PATH)
    await db.init()
    logger.info("✅ Ma'lumotlar bazasi tayyor.")

    # Asosiy botni yaratadi
    bot = create_main_bot()
    dp = create_main_dispatcher()

    # Bot haqida ma'lumot oladi
    try:
        me = await bot.get_me()
        logger.info("✅ Asosiy bot: @%s (ID: %d)", me.username, me.id)
    except Exception as e:
        logger.critical("❌ Bot tokenini tekshiring! Xato: %s", e)
        return

    # Barcha shop botlarini ishga tushiradi
    logger.info("⏳ Shop botlari yuklanmoqda...")
    started_count = await load_all_bots()
    logger.info("✅ %d ta shop bot ishga tushirildi.", started_count)

    # Reja tekshiruvchisini ishga tushiradi
    asyncio.create_task(plan_expiry_checker(bot), name="plan_expiry_checker")

    # Adminlarga xabar yuboradi
    for admin_id in config.ADMIN_IDS:
        try:
            from utils.bot_manager import get_active_bot_count
            active = get_active_bot_count()
            await bot.send_message(
                admin_id,
                f"✅ <b>ShopMakerUzBot ishga tushdi!</b>\n\n"
                f"🤖 Faol shop botlar: {active} ta\n"
                f"🗄 Baza: {config.DB_PATH}",
                parse_mode="HTML"
            )
        except Exception:
            pass

    logger.info("✅ ShopMakerUzBot tayyor! Polling va health server boshlanmoqda...")

    async def polling_task():
        try:
            await dp.start_polling(
                bot,
                allowed_updates=dp.resolve_used_update_types(),
                handle_signals=False,
            )
        finally:
            logger.info("⏹ ShopMakerUzBot to'xtatilmoqda...")
            from utils.bot_manager import _active_bots, stop_shop_bot
            bot_ids = list(_active_bots.keys())
            for bid in bot_ids:
                await stop_shop_bot(bid)
            await bot.session.close()
            logger.info("✅ ShopMakerUzBot to'xtatildi.")

    # Health server va bot polling — ikkalasi parallel ishlaydi
    await asyncio.gather(
        polling_task(),
        run_health_server(),
    )


if __name__ == "__main__":
    try:
        # uvloop (Linux/Mac da tezroq)
        try:
            import uvloop
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
            logging.getLogger("main").info("⚡ uvloop ishlatilmoqda.")
        except ImportError:
            pass

        asyncio.run(main())
    except KeyboardInterrupt:
        logging.getLogger("main").info("👋 Bot to'xtatildi (Ctrl+C).")
