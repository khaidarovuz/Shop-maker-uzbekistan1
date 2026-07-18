# 🤖 ShopMakerUzBot

**ShopMakerUzBot** — foydalanuvchilar o'z Telegram do'kon botlarini yaratishi va boshqarishi uchun professional platforma.

---

## 📦 Loyiha tarkibi

```
shopmaker/
├── main.py                      # Asosiy kirish nuqtasi
├── config.py                    # Konfiguratsiya va matnlar
├── requirements.txt             # Python kutubxonalar ro'yxati
├── .env.example                 # Muhit o'zgaruvchilari namunasi
│
├── database/
│   ├── __init__.py
│   ├── db.py                    # SQLite ulanish va jadval yaratish
│   └── queries.py               # Barcha ma'lumotlar bazasi so'rovlari
│
├── handlers/
│   ├── __init__.py
│   ├── start.py                 # /start, yordam, sozlamalar
│   ├── my_bots.py               # Bot boshqaruvi
│   ├── plans.py                 # Rejalar va to'lovlar
│   ├── admin.py                 # Super admin panel
│   └── shop_bot/                # Shop bot handlerlari
│       ├── __init__.py
│       ├── start.py             # /start va asosiy menyu
│       ├── products.py          # Mahsulotlar ko'rish
│       ├── categories.py        # Kategoriyalar
│       ├── search.py            # Mahsulot qidirish
│       ├── cart.py              # Savat va buyurtma
│       ├── orders.py            # Foydalanuvchi buyurtmalari
│       ├── admin.py             # Shop admin panel
│       └── settings.py          # Shop sozlamalari
│
├── keyboards/
│   ├── __init__.py
│   ├── main_kb.py               # Asosiy bot klaviaturaları
│   ├── shop_kb.py               # Shop bot klaviaturaları
│   └── admin_kb.py              # Super admin klaviaturaları
│
├── middlewares/
│   ├── __init__.py
│   └── auth.py                  # Autentifikatsiya middleware
│
├── filters/
│   ├── __init__.py
│   └── admin.py                 # Admin filtrlari
│
└── utils/
    ├── __init__.py
    ├── bot_manager.py           # Ko'p bot boshqaruvi
    ├── validators.py            # Token va ma'lumot tekshiruvi
    └── helpers.py               # Yordamchi funksiyalar
```

---

## 🚀 O'rnatish

### 1. Talablar

- Python 3.12+
- pip

### 2. Kutubxonalarni o'rnatish

```bash
pip install -r requirements.txt
```

### 3. Muhit o'zgaruvchilarini sozlash

```bash
cp .env.example .env
nano .env
```

`.env` faylida quyidagilarni to'ldiring:

```env
BOT_TOKEN=YOUR_BOT_TOKEN
ADMIN_IDS=123456789
```

### 4. Botni ishga tushirish

```bash
cd shopmaker
python main.py
```

---

## ⚙️ Konfiguratsiya

| O'zgaruvchi | Tavsif | Majburiy |
|-------------|--------|----------|
| `BOT_TOKEN` | ShopMakerUzBot tokeni | ✅ |
| `ADMIN_IDS` | Super admin Telegram ID lari (vergul bilan) | ✅ |
| `DB_PATH` | SQLite fayl yo'li | ❌ |
| `PREMIUM_PRICE` | Premium narxi (so'm) | ❌ |
| `PREMIUM_DAYS` | Premium muddati (kun) | ❌ |
| `COMFORT_PRICE` | Comfort narxi (so'm) | ❌ |
| `COMFORT_DAYS` | Comfort muddati (kun) | ❌ |

---

## 📊 Ma'lumotlar bazasi jadvallari

| Jadval | Tavsif |
|--------|--------|
| `users` | ShopMaker foydalanuvchilari |
| `bots` | Yaratilgan shop botlar |
| `products` | Mahsulotlar |
| `categories` | Kategoriyalar |
| `orders` | Buyurtmalar |
| `carts` | Savatlar |
| `plans` | Reja tarixi |
| `payments` | To'lovlar |
| `promo_codes` | Promo kodlar |
| `promo_usages` | Promo kod foydalanishlari |
| `shop_users` | Shop bot xaridorlari |
| `settings` | Tizim sozlamalari |
| `system_logs` | Tizim loglari |

---

## 💎 Rejalar

### 🆓 Bepul reja
- 1 ta bot
- Cheksiz mahsulotlar, kategoriyalar, buyurtmalar
- Savat tizimi, qidirish, rasm
- "Powered by ShopMaker" footer

### 🌟 Comfort reja (5 000 so'm / 3 oy)
- 1 ta bot
- Ko'proq mavzular
- Kengaytirilgan limitlar

### 💎 Premium reja (10 000 so'm / 30 kun)
- 3 ta bot
- "Powered by ShopMaker" olib tashlanadi
- Excel eksport
- Kengaytirilgan statistika
- Broadcast
- Premium nishon

---

## 🏪 Shop bot funksiyalari

### Xaridor uchun
- 🛍 Mahsulotlar ko'rish
- 📂 Kategoriyalar bo'yicha filtrlash
- 🔍 Mahsulot qidirish
- 🛒 Savat tizimi
- 📋 Buyurtmalarim
- 📞 Admin bilan bog'lanish
- ℹ️ Bot haqida

### Admin uchun
- ➕ Mahsulot qo'shish / tahrirlash / o'chirish
- 📂 Kategoriya boshqaruvi
- 📋 Buyurtmalar boshqaruvi
- 📣 Broadcast xabari
- 📊 Statistika
- ⚙️ Bot sozlamalari

---

## 👑 Super Admin panel

- 📊 Global statistika
- 👥 Foydalanuvchilar boshqaruvi
- 💎 Premium / Comfort berish va olib tashlash
- 🚫 Bloklash / blokdan chiqarish
- 🗑 Botlarni o'chirish
- 📣 Global broadcast
- 🎁 Promo kodlar
- 💳 To'lovlar tasdiqlash
- 💰 Narxlarni o'zgartirish
- 🔒 Ro'yxatdan o'tishni boshqarish
- 📋 Tizim loglari
- 💾 Zaxira nusxa

---

## 💳 To'lov tizimlari

Joriy arxitektura quyidagilarni qo'llab-quvvatlaydi:
- **Click** — CLICK merchant ID orqali
- **Payme** — Payme merchant orqali
- **Uzum Bank** — tez orada
- **Qo'lda to'lov** — admin tomonidan tasdiqlanadi

---

## 🏗️ Arxitektura

```
ShopMakerUzBot (asosiy bot)
    │
    ├── Ma'lumotlar bazasi (SQLite)
    │       └── Barcha botlar uchun umumiy
    │
    └── Bot Manager
            ├── Shop Bot 1 (o'z dispatcher + Bot instance)
            ├── Shop Bot 2
            └── Shop Bot N (asyncio.Task)
```

Har bir shop boti o'z `asyncio.Task` sida ishlaydi.
Barcha botlar bitta SQLite bazasini ulashadi.

---

## 📝 Muhim eslatmalar

1. Token xavfsizligi: tokenlarni hech qachon ochiq holda saqlimang
2. Backup: ma'lumotlar bazasini muntazam zaxiralang
3. Serverda ishlash: `systemd` yoki `supervisor` dan foydalaning
4. Log monitoring: `logs/shopmaker.log` faylini kuzating

---

## 🔧 Deployment (Ishlab chiqarish)

### systemd xizmati

```ini
[Unit]
Description=ShopMakerUzBot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/shopmaker
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable shopmaker
sudo systemctl start shopmaker
sudo systemctl status shopmaker
```

---

## 📞 Murojaat

- Telegram: @ShopMakerUzBot
- Version: 1.0.0
