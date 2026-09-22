from __future__ import annotations

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message

from .. import cache, db
from ..db import User
from ..keyboards import UNCODE, button_texts, result_kb, settings_kb
from ..texts import MODE_NAME, b, t
from ..utils import SAFE_LIMIT, as_html, convert_for, split_text

router = Router(name="convert")

_BUTTONS = button_texts()
_MODES = ("yangi", "eski", "kirill", "avto")


async def send_result(message: Message, user: User, source: str,
                      target: str | None = None) -> None:
    res = convert_for(user, source, target)
    key = cache.put(source)
    parts = split_text(res.text)
    # Tugmalar faqat bir xabarga sığgan natija uçun: tugma bosilganda
    # xabar tahrirlanadi, bir neça bölakni esa tahrirlab bölmaydi —
    # aks holda natijaning qolgani jimgina yöqolardi.
    kb = result_kb(key, res.target.value, user.fmt, user.ui) if len(parts) == 1 else None
    for i, part in enumerate(parts):
        await message.answer(
            as_html(part, user.fmt),
            reply_markup=kb if i == len(parts) - 1 else None,
        )
    await db.bump(user.user_id, len(source))


# ------------------------------------------------------------ rejim buyruqlari
@router.message(Command(*_MODES))
async def cmd_mode(message: Message, user: User, command: CommandObject) -> None:
    mode = command.command
    await db.set_field(user.user_id, "mode", mode)
    user.mode = mode
    rest = (command.args or "").strip()
    await message.answer(t("mode_set", user.ui, mode=b(mode, user.ui)))
    if rest:
        await send_result(message, user, rest)


# ------------------------------------------------- pastki klaviatura tugmalari
@router.message(F.text.in_(_BUTTONS))
async def kb_buttons(message: Message, user: User) -> None:
    name = _BUTTONS[message.text]
    if name == "help":
        await message.answer(t("help", user.ui))
        return
    if name == "settings":
        await message.answer(t("settings", user.ui, mode=b(user.mode, user.ui),
                               ui=b(user.ui, user.ui),
                               smart=b("on" if user.smart else "off", user.ui),
                               foreign=b("on" if user.keep_foreign else "off", user.ui),
                               fmt=b("codefmt" if user.fmt == "kod" else "plain", user.ui)),
                             reply_markup=settings_kb(user))
        return
    await db.set_field(user.user_id, "mode", name)
    user.mode = name
    await message.answer(t("mode_set", user.ui, mode=b(name, user.ui)))


# ------------------------------------------------------------- asosiy handler
@router.message(F.chat.type == ChatType.PRIVATE, F.text)
async def on_text(message: Message, user: User) -> None:
    text = message.text.strip()
    if not text:
        await message.answer(t("empty", user.ui))
        return
    if len(text) > SAFE_LIMIT * 8:
        await message.answer(t("too_long", user.ui))
        return
    await send_result(message, user, text)


@router.message(F.chat.type == ChatType.PRIVATE, F.caption)
async def on_caption(message: Message, user: User) -> None:
    await send_result(message, user, message.caption)


@router.edited_message(F.chat.type == ChatType.PRIVATE, F.text)
async def on_edit(message: Message, user: User) -> None:
    await send_result(message, user, message.text.strip())


# ------------------------------------------------------------------- tugmalar
@router.callback_query(F.data.startswith("cv|"))
async def cb_convert(call: CallbackQuery, user: User) -> None:
    _, key, tcode, fcode = call.data.split("|")
    source = cache.get(key)
    if source is None:
        await call.answer("⌛️", show_alert=False)
        return
    fmt = "kod" if fcode == "c" else "oddiy"
    target = UNCODE.get(tcode, "yangi")
    if tcode == "a":
        body, current = source, "asl"
    else:
        res = convert_for(user, source, target)
        body, current = res.text, res.target.value
    parts = split_text(body)
    try:
        await call.message.edit_text(
            as_html(parts[0], fmt),
            reply_markup=result_kb(key, current, fmt, user.ui) if len(parts) == 1 else None,
        )
        for extra in parts[1:]:
            await call.message.answer(as_html(extra, fmt))
    except Exception:  # matn ösgarmagan bölsa Telegram xato qaytaradi
        pass
    await call.answer(MODE_NAME.get(current, current))
