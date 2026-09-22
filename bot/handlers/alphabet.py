"""Rasmiy alifbo jadvali va misollar."""
from __future__ import annotations

import html

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from yozuv.alphabets import ALPHABET_SIZE, OKINA, REMOVED_DIGRAPH
from yozuv.tables import alphabet_table, examples_text

from ..db import User
from ..texts import render, t

router = Router(name="alphabet")


@router.message(Command("alifbo", "alphabet"))
async def cmd_alphabet(message: Message, user: User) -> None:
    # DIQQAT: jadval va harf misollari hеç qaçon ötkazilmaydi — ular
    # alifboning özini körsatadi, matn emas.
    note = t("alphabet_note", user.ui,
             size=ALPHABET_SIZE,
             old=f"O{OKINA}, G{OKINA}, Sh, Ch",
             new="Ö, Ğ, Ş, Ç",
             ng=REMOVED_DIGRAPH,
             ng_misol="tong, köngil")
    await message.answer(
        render("<b>🔤 Yangi o'zbek alifbosi</b>", user.ui) + "\n"
        + f"<pre>{html.escape(alphabet_table())}</pre>\n"
        + note
    )


@router.message(Command("misol", "examples"))
async def cmd_examples(message: Message, user: User) -> None:
    await message.answer(
        render("<b>✍️ So'zlarning yangi alifbodagi yozilishi</b>", user.ui) + "\n"
        f"<pre>{html.escape(examples_text())}</pre>"
    )
