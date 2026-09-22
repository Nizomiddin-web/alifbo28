"""Admin buyruqlari: statistika, tarqatma va şaxsiy xabarlar."""
from __future__ import annotations

import html
import time

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from .. import broadcast as bc_engine
from .. import db
from ..config import config
from ..db import User
from ..models import Audience, BroadcastStatus
from ..texts import AUDIENCE_NAME, render, t

router = Router(name="admin")
router.message.filter(F.from_user.id.in_(config.admins))
router.callback_query.filter(F.from_user.id.in_(config.admins))

#: bir xabarni juda tez-tez tahrirlamaslik uçun (Telegram çegarasi ~1/sek)
_PROGRESS_GAP = 2.0


# --------------------------------------------------------------- statistika
@router.message(Command("stat", "stats"))
async def cmd_stat(message: Message, user: User) -> None:
    await message.answer(t("admin_stats", user.ui, **await db.stats()))


@router.message(Command("kim", "who"))
async def cmd_who(message: Message, user: User, command: CommandObject) -> None:
    key = (command.args or "").strip()
    if not key and message.reply_to_message and message.reply_to_message.from_user:
        key = str(message.reply_to_message.from_user.id)
    if not key:
        await message.answer(t("who_usage", user.ui))
        return
    found = await db.find_user(key)
    if found is None:
        await message.answer(t("dm_no_user", user.ui, key=html.escape(key)))
        return
    await message.answer(t(
        "who_card", user.ui,
        name=html.escape(found.full_name or "—"),
        id=found.user_id,
        username=f"@{found.username}" if found.username else "—",
        mode=found.mode, ui=found.ui,
        subscribed="ha" if found.subscribed else "yöq",
        blocked="ha" if found.blocked else "yöq",
        conv=found.conv, chars=found.chars,
        created=str(found.created_at)[:16], seen=str(found.last_seen)[:16],
    ))


# ------------------------------------------------------------ şaxsiy xabar
async def resolve_target(key: str):
    """«@nom» yoki ID böyiça manzilni topadi.

    Foydalanuvçi (musbat ID), guruh/kanal (manfiy ID) yoki oçiq kanal
    («@nom») böla oladi. Bazada yöq manfiy ID ham qabul qilinadi — uni
    Telegramning özi tekşiradi.
    """
    key = key.strip()
    if key.lstrip("-").isdigit():
        num = int(key)
        if num < 0:
            chat = await db.find_chat(num)
            return num, (chat.title if chat and chat.title else str(num))
        found = await db.find_user(num)
        if found is None:
            return None, None
        return found.user_id, (f"@{found.username}" if found.username else str(num))

    name = key.lstrip("@")
    found = await db.find_user(name)
    if found is not None:
        return found.user_id, f"@{found.username or name}"
    chat = await db.find_chat(name)
    if chat is not None:
        return chat.chat_id, (chat.title or f"@{name}")
    return f"@{name}", f"@{name}"        # oçiq kanal — Telegram hal qiladi


@router.message(Command("yubor", "dm"))
async def cmd_direct(message: Message, user: User, command: CommandObject) -> None:
    args = (command.args or "").strip()
    key, _, text = args.partition(" ")
    if not text and message.reply_to_message:
        text = message.reply_to_message.text or message.reply_to_message.caption or ""
    if not key or not text.strip():
        await message.answer(t("dm_usage", user.ui))
        return
    target, label = await resolve_target(key)
    if target is None:
        await message.answer(t("dm_no_user", user.ui, key=html.escape(key)))
        return
    ok, why = await bc_engine.get().send_direct(user.user_id, target, text.strip())
    if ok:
        await message.answer(t("dm_ok", user.ui, who=html.escape(str(label))))
    else:
        await message.answer(t("dm_fail", user.ui, why=html.escape(why or "")))


@router.message(Command("guruhlar", "chats"))
async def cmd_chats(message: Message, user: User) -> None:
    rows = await db.list_chats(50)
    if not rows:
        await message.answer(t("chats_empty", user.ui))
        return
    lines = [t("chats_head", user.ui, n=len(rows))]
    for c in rows:
        lines.append(t("chats_row", user.ui,
                       title=html.escape(c.title or "—"),
                       id=c.chat_id,
                       kind="kanal" if c.type == "channel" else "guruh",
                       auto="🔁" if c.auto else "·"))
    await message.answer("\n".join(lines))


# ---------------------------------------------------------------- tarqatma
def _audience_kb(bid: int, counts: dict[str, int], ui: str) -> InlineKeyboardMarkup:
    rows = []
    for key in ("barça", "faol", "guruhlar", "yangi_ui", "eski_ui", "kirill_ui"):
        n = counts.get(key, 0)
        if not n:
            continue
        rows.append([InlineKeyboardButton(
            text=f"{render(AUDIENCE_NAME[key], ui)} · {n}",
            callback_data=f"bc|{bid}|{key}")])
    rows.append([InlineKeyboardButton(text=render("❌ Bekor qilish", ui),
                                      callback_data=f"bcx|{bid}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _confirm_kb(bid: int, ui: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=render("🚀 Yuborish", ui), callback_data=f"bcgo|{bid}"),
        InlineKeyboardButton(text=render("❌ Bekor qilish", ui), callback_data=f"bcx|{bid}"),
    ]])


@router.message(Command("xabar", "broadcast"))
async def cmd_broadcast(message: Message, user: User) -> None:
    source = message.reply_to_message
    if source is None:
        await message.answer(t("bc_usage", user.ui))
        return
    bc = await db.create_broadcast(
        admin_id=user.user_id, audience=Audience.ALL,
        from_chat_id=source.chat.id, message_id=source.message_id, kind="nusxa")
    counts = {
        "barça": len(await db.audience_ids(Audience.ALL)),
        "faol": len(await db.audience_ids(Audience.ACTIVE, "30")),
        "guruhlar": len(await db.audience_ids(Audience.CHATS)),
        "yangi_ui": len(await db.audience_ids(Audience.NEW_UI)),
        "eski_ui": len(await db.audience_ids(Audience.OLD_UI)),
        "kirill_ui": len(await db.audience_ids(Audience.CYR_UI)),
    }
    await message.answer(t("bc_pick", user.ui, id=bc.id),
                         reply_markup=_audience_kb(bc.id, counts, user.ui))


@router.callback_query(F.data.startswith("bc|"))
async def cb_audience(call: CallbackQuery, user: User) -> None:
    _, raw_id, audience = call.data.split("|")
    bid = int(raw_id)
    arg = "30" if audience == "faol" else None
    ids = await db.audience_ids(audience, arg)
    if not ids:
        await call.answer(render("Bo'sh auditoriya", user.ui), show_alert=True)
        return
    total = await db.queue_targets(bid, ids)
    async with db.session() as s:
        row = await s.get(db.Broadcast, bid)
        if row is not None:
            row.audience, row.audience_arg = audience, arg
            await s.commit()
    await call.message.edit_text(
        t("bc_confirm", user.ui, id=bid,
          audience=render(AUDIENCE_NAME[audience], user.ui), total=total),
        reply_markup=_confirm_kb(bid, user.ui))
    await call.answer()


@router.callback_query(F.data.startswith("bcx|"))
async def cb_cancel(call: CallbackQuery, user: User) -> None:
    bid = int(call.data.split("|")[1])
    bc_engine.get().cancel(bid)
    await db.set_broadcast_status(bid, BroadcastStatus.CANCELLED)
    await call.message.edit_text(t("bc_cancelled", user.ui, id=bid))
    await call.answer()


@router.callback_query(F.data.startswith("bcgo|"))
async def cb_go(call: CallbackQuery, user: User) -> None:
    bid = int(call.data.split("|")[1])
    status_msg = call.message
    last = [0.0]

    async def on_progress(bc) -> None:
        if bc is None:
            return
        now = time.monotonic()
        if now - last[0] < _PROGRESS_GAP and bc.done < bc.total:
            return
        last[0] = now
        try:
            await status_msg.edit_text(t(
                "bc_progress", user.ui, id=bc.id,
                status=render(bc.status, user.ui), sent=bc.sent,
                blocked=bc.blocked, failed=bc.failed,
                done=bc.done, total=bc.total))
        except Exception:
            pass

    bc_engine.get().start(bid, on_progress)
    await call.answer(render("Boshlandi", user.ui))
    await status_msg.answer(t("bc_started", user.ui, id=bid))


@router.message(Command("toxtat", "stop"))
async def cmd_stop(message: Message, user: User, command: CommandObject) -> None:
    arg = (command.args or "").strip()
    if not arg.isdigit():
        rows = [b for b in await db.list_broadcasts(20)
                if b.status == BroadcastStatus.RUNNING.value]
        if not rows:
            await message.answer(t("bc_not_running", user.ui, id="—"))
            return
        arg = str(rows[0].id)
    bid = int(arg)
    if bc_engine.get().cancel(bid):
        await message.answer(t("bc_cancelled", user.ui, id=bid))
    else:
        await message.answer(t("bc_not_running", user.ui, id=bid))


@router.message(Command("xabarlar", "broadcasts"))
async def cmd_list(message: Message, user: User) -> None:
    rows = await db.list_broadcasts(10)
    if not rows:
        await message.answer(t("bc_list_empty", user.ui))
        return
    lines = [t("bc_list_head", user.ui)]
    for b in rows:
        lines.append(t("bc_row", user.ui, id=b.id,
                       status=render(b.status, user.ui),
                       sent=b.sent, total=b.total,
                       when=str(b.created_at)[:16]))
    await message.answer("\n".join(lines))
