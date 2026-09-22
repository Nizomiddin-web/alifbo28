from __future__ import annotations

from aiogram import Router, html
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from yozuv import __version__

from .. import db
from ..db import User
from ..keyboards import main_kb
from ..texts import t

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, user: User) -> None:
    me = await message.bot.me()
    await message.answer(
        t("start", user.ui, name=html.quote(message.from_user.first_name or "döst"),
          bot=me.username),
        reply_markup=main_kb(user.ui),
    )


@router.message(Command("yordam", "help"))
async def cmd_help(message: Message, user: User) -> None:
    await message.answer(t("help", user.ui))


@router.message(Command("haqida", "about"))
async def cmd_about(message: Message, user: User) -> None:
    await message.answer(t("about", user.ui, ver=__version__))


@router.message(Command("obuna", "subscribe"))
async def cmd_subscribe(message: Message, user: User) -> None:
    new = not user.subscribed
    await db.set_subscribed(user.user_id, new)
    await message.answer(t("sub_on" if new else "sub_off", user.ui))


@router.message(Command("mening", "me"))
async def cmd_me(message: Message, user: User) -> None:
    await message.answer(t("my_stats", user.ui, conv=user.conv, chars=user.chars,
                           joined=str(user.created_at)[:10]))
