"""Ixtiyoriy: rasmdan matn öqiş (OCR).

Işlaşi uçun `tesseract` va `pytesseract` + `pillow` örnatilgan bölişi kerak:
    brew install tesseract tesseract-lang     # macOS
    pip install pytesseract pillow
"""
from __future__ import annotations

import io

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.types import Message

from ..db import User
from ..texts import t

router = Router(name="photo")

try:  # pragma: no cover
    import pytesseract
    from PIL import Image
    OCR = True
except ModuleNotFoundError:  # pragma: no cover
    OCR = False

LANGS = "uzb+uzb_cyrl+eng"


@router.message(F.chat.type == ChatType.PRIVATE, F.photo)
async def on_photo(message: Message, user: User) -> None:
    if not OCR:
        await message.answer(t("ocr_off", user.ui))
        return
    from .convert import send_result

    buf = io.BytesIO()
    await message.bot.download(message.photo[-1], destination=buf)
    buf.seek(0)
    try:
        text = pytesseract.image_to_string(Image.open(buf), lang=LANGS).strip()
    except Exception:
        text = ""
    if not text:
        await message.answer(t("ocr_fail", user.ui))
        return
    await send_result(message, user, text)
