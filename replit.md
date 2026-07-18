# ShopMakerUzBot

Foydalanuvchilar o'z Telegram do'kon botlarini yaratishi va boshqarishi uchun professional platforma. Hamma narsa O'zbek tilida.

## Run & Operate

- `cd shopmaker && python main.py` — botni ishga tushirish
- Barcha loglar `shopmaker/logs/shopmaker.log` ga yoziladi

## Stack

- Python 3.12 + aiogram 3.13.1 (Telegram Bot Framework)
- SQLite + aiosqlite (asinxron ma'lumotlar bazasi)
- openpyxl (Excel eksport)
- Multi-bot arxitekturasi: har bir shop bot o'z `asyncio.Task` sida ishlaydi

## Where things live

- `shopmaker/main.py` — asosiy kirish nuqtasi
- `shopmaker/config.py` — konfiguratsiya + barcha O'zbek matnlar
- `shopmaker/database/db.py` — 13 jadval + indekslar
- `shopmaker/database/queries.py` — barcha CRUD operatsiyalar
- `shopmaker/utils/bot_manager.py` — ko'p bot boshqaruvi (start/stop/restart/load)
- `shopmaker/handlers/` — asosiy bot handlerlari
- `shopmaker/handlers/shop_bot/` — shop bot handlerlari

## Architecture decisions

- SQLite bitta fayl — deployment soddaligi uchun, tranzaksiya xavfsizligi `aiosqlite` bilan
- Ko'p bot: har bir shop bot o'z `Bot` + `Dispatcher` + `asyncio.Task` instanceiga ega; barcha botlar bitta bazani ulashadi
- Shop bot middleware — `bot_id`, `bot_data`, `shop_user` ni har bir handlerga inject qiladi
- Auth middleware — foydalanuvchini auto-create/update qiladi va bloklangan userni to'xtatadi
- Alohida router fayllari — `handlers/my_bots.py`, `handlers/plans.py`, `handlers/admin.py` va shop bot uchun `handlers/shop_bot/`

## Product

- **ShopMakerUzBot** (asosiy bot): ro'yxatdan o'tish, BotFather token ulash, shop botni boshqarish, rejalar sotib olish
- **Shop botlar**: mustaqil ishlaydi, xaridorlar mahsulot ko'radi, savat, buyurtma, qidiruv
- **Rejalar**: Bepul (1 bot), Comfort (5000 so'm/90 kun), Premium (10000 so'm/30 kun, 3 bot)

## User preferences

- Barcha matnlar O'zbek tilida
- Main bot token: `8566204932:AAEU0MBdt2d4WcOlh5Qb6dBP8l_vzYxWmEU`
- Admin ID: `8143880963`

## Gotchas

- `.env` fayl platformada bloklanadi — `BOT_TOKEN` va `ADMIN_IDS` ni Replit Secrets orqali qo'shing
- Har yangi shop bot start bo'lganda Telegram API dan bot info so'raydi — to'g'ri token kerak
- `shopmaker/logs/` papkasi botni ishga tushirishdan oldin yaratilishi shart (already created)
- `check_and_expire_plans` async funksiya — har soatda `asyncio.Task` sifatida chaqiriladi

## Pointers

- Shop bot admin panel `handlers/shop_bot/admin.py` da, faqat `bot_data.owner_id` ga ruxsat beriladi
- Savat + buyurtma flow `handlers/shop_bot/cart.py` (FSM: phone → address → note → confirm)
- Super admin panel `handlers/admin.py` da
