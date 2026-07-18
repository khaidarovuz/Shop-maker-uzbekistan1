"""
Validatorlar — token va boshqa ma'lumotlarni tekshiradi.
"""

import re
import logging
import aiohttp
from typing import Optional

logger = logging.getLogger(__name__)

TOKEN_REGEX = re.compile(r"^\d{8,12}:[A-Za-z0-9_-]{35}$")


async def validate_bot_token(token: str) -> Optional[dict]:
    """
    Telegram Bot API ga so'rov yuborib, tokenni tekshiradi.
    Agar token haqiqiy bo'lsa, bot ma'lumotlarini qaytaradi:
        {'id': ..., 'username': ..., 'first_name': ...}
    Aks holda None qaytaradi.
    """
    token = token.strip()

    # Avval format tekshiruvi
    if not TOKEN_REGEX.match(token):
        return None

    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10)
        ) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                if data.get("ok"):
                    bot_info = data["result"]
                    return {
                        "id": bot_info["id"],
                        "username": bot_info.get("username", ""),
                        "first_name": bot_info.get("first_name", ""),
                        "token": token
                    }
    except aiohttp.ClientError as e:
        logger.error("Token tekshirishda tarmoq xatosi: %s", e)
    except Exception as e:
        logger.error("Token tekshirishda xato: %s", e)

    return None


def validate_price(text: str) -> Optional[float]:
    """Narx satrini tekshiradi va float ga aylantiradi."""
    try:
        text = text.strip().replace(",", ".").replace(" ", "")
        price = float(text)
        if price < 0:
            return None
        return price
    except ValueError:
        return None


def validate_phone(phone: str) -> Optional[str]:
    """Telefon raqamini tekshiradi va formatlaydi."""
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 9:
        return f"+998{digits}"
    if len(digits) == 12 and digits.startswith("998"):
        return f"+{digits}"
    if len(digits) == 13 and digits.startswith("998"):
        return f"+{digits}"
    return None


def validate_promo_code(code: str) -> str:
    """Promo kodni normalizatsiya qiladi."""
    return code.strip().upper()
