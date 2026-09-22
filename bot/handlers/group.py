"""Guruh va kanallardagi iş."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandObject
from aiogram.types import ChatMemberUpdated, Message

from yozuv import Script, detect

from .. import db
from ..config import config
from ..db import User
from ..texts import t
from ..utils import convert_for, split_text

router = Router(name="group")

GROUPS = {ChatType.GROUP, ChatType.SUPERGROUP}


@router.message(Command("yoz", "convert"), F.chat.type.in_(GROUPS))
async def cmd_yoz(message: Message, user: User, command: CommandObject) -> None:
    await db.remember_chat(message.chat.id, message.chat.type, message.chat.title)
    source = (command.args or "").strip()
    if not source and message.reply_to_message:
        source = (message.reply_to_message.text or message.reply_to_message.caption or "").strip()
    if not source:
        await message.reply(t("reply_needed", user.ui))
        return
    res = convert_for(user, source)
    for part in split_text(res.text):
        await message.reply(part)


async def _is_chat_admin(message: Message) -> bool:
    if config.is_admin(message.from_user.id if message.from_user else None):
        return True
    if message.from_user is None:
        return False
    member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
    return member.status in {"creator", "administrator"}


@router.message(Command("avtokanal", "autochat"), F.chat.type.in_(GROUPS))
async def cmd_auto(message: Message, user: User) -> None:
    if not await _is_chat_admin(message):
        await message.reply(t("not_admin", user.ui))
        return
    auto, mode = await db.chat_auto(message.chat.id)
    await db.set_chat_auto(message.chat.id, not auto, user.mode)
    await message.reply(t("auto_off" if auto else "auto_on", user.ui))


@router.message(F.chat.type.in_(GROUPS), F.text, ~F.text.startswith("/"))
async def group_auto(message: Message, user: User) -> None:
    auto, mode = await db.chat_auto(message.chat.id)
    if not auto:
        return
    if detect(message.text) in (Script.NEW_LATIN, Script.UNKNOWN):
        return
    res = convert_for(user, message.text, mode)
    if res.changed:
        await message.reply(split_text(res.text)[0])


# ---------------------------------------------------------------- kanal postlari
@router.channel_post(F.text)
async def channel_post(message: Message) -> None:
    """Kanal postini avtomatik ötkaziş (bot admin va tahrir huquqi bölişi şart)."""
    auto, mode = await db.chat_auto(message.chat.id)
    if not (auto or config.channel_auto):
        return
    if detect(message.text) in (Script.NEW_LATIN, Script.UNKNOWN):
        return
    from yozuv import Target, convert as _convert
    res = _convert(message.text, Target(mode))
    if not res.changed or len(res.text) > 4096:
        return
    try:
        await message.edit_text(res.text)
    except Exception:
        pass


@router.channel_post(Command("avtokanal"))
async def channel_toggle(message: Message) -> None:
    auto, _ = await db.chat_auto(message.chat.id)
    await db.set_chat_auto(message.chat.id, not auto)
    await db.remember_chat(message.chat.id, message.chat.type, message.chat.title)
    await message.reply(t("auto_off" if auto else "auto_on", "yangi"))


# ─────────────────────────────────────────────────────────────────────────
# Botning aʼzolik holati ösganda
# ─────────────────────────────────────────────────────────────────────────
IN_CHAT = {"member", "administrator", "creator", "restricted"}
OUT_CHAT = {"left", "kicked"}


@router.my_chat_member()
async def on_membership(event: ChatMemberUpdated) -> None:
    """Bot guruh/kanalga qöşilganda yoki çiqarilganda bazani yangilaydi.

    Buni qölda buyruq kutib ötirmasdan qilamiz — aks holda bot qöşilgan,
    ammo hеç kim /yoz yozmagan guruh tarqatmalarga umuman tuşmay qolardi.
    """
    status = event.new_chat_member.status
    chat = event.chat

    if chat.type == "private":
        # foydalanuvçi botni bloklagan yoki qaytadan oçgan
        if event.from_user and not event.from_user.is_bot:
            await db.mark_blocked(event.from_user.id, status in OUT_CHAT)
        return

    if status in IN_CHAT:
        await db.remember_chat(chat.id, chat.type, chat.title, chat.username)
    elif status in OUT_CHAT:
        await db.deactivate_chat(chat.id)
