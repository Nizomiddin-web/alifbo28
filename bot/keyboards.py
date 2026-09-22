from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from .db import User
from .texts import b

CODE = {"yangi": "y", "eski": "e", "kirill": "k", "asl": "a"}
UNCODE = {v: k for k, v in CODE.items()}
ORDER = ("yangi", "eski", "kirill")


def result_kb(key: str, current: str, fmt: str = "oddiy", ui: str = "yangi") -> InlineKeyboardMarkup:
    """Natija tagidagi tugmalar: boşqa yozuvlar, asl matn, nusxalaş."""
    row = [
        InlineKeyboardButton(text=b(name, ui), callback_data=f"cv|{key}|{CODE[name]}|{fmt[0]}")
        for name in ORDER if name != current
    ]
    second = [
        InlineKeyboardButton(text=b("orig", ui), callback_data=f"cv|{key}|a|{fmt[0]}"),
        InlineKeyboardButton(
            text=b("code", ui),
            callback_data=f"cv|{key}|{CODE.get(current, 'y')}|{'p' if fmt == 'kod' else 'c'}"),
    ]
    return InlineKeyboardMarkup(inline_keyboard=[row, second])


def settings_kb(u: User) -> InlineKeyboardMarkup:
    ui = u.ui
    on, off = b("on", ui), b("off", ui)
    rows = [
        [InlineKeyboardButton(text=b("mode", ui, v=b(u.mode, ui)), callback_data="st|mode|next")],
        [InlineKeyboardButton(text=b("ui", ui, v=b(u.ui, ui)), callback_data="st|ui|next")],
        [InlineKeyboardButton(text=b("smart", ui, v=on if u.smart else off),
                              callback_data="st|smart|toggle")],
        [InlineKeyboardButton(text=b("foreign", ui, v=on if u.keep_foreign else off),
                              callback_data="st|keep_foreign|toggle")],
        [InlineKeyboardButton(
            text=b("fmt", ui, v=b("codefmt" if u.fmt == "kod" else "plain", ui)),
            callback_data="st|fmt|toggle")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def main_kb(ui: str = "yangi") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=b("yangi", ui)), KeyboardButton(text=b("eski", ui))],
            [KeyboardButton(text=b("kirill", ui)), KeyboardButton(text=b("avto", ui))],
            [KeyboardButton(text=b("settings", ui)), KeyboardButton(text=b("help", ui))],
        ],
        resize_keyboard=True,
        input_field_placeholder="matn yuboring…",
    )


def button_texts() -> dict[str, str]:
    """Barça tillardagi tugma matnlari → maʼno (matn handleridan ajratiş uçun)."""
    out: dict[str, str] = {}
    for ui in ORDER:
        for name in ("yangi", "eski", "kirill", "avto", "settings", "help"):
            out[b(name, ui)] = name
    return out
