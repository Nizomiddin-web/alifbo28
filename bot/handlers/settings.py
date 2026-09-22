from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from .. import db
from ..db import User
from ..keyboards import main_kb, settings_kb
from ..texts import b, t

router = Router(name="settings")

_MODE_CYCLE = ("yangi", "eski", "kirill", "avto")
_UI_CYCLE = ("yangi", "eski", "kirill")


def _view(u: User) -> str:
    return t("settings", u.ui, mode=b(u.mode, u.ui), ui=b(u.ui, u.ui),
             smart=b("on" if u.smart else "off", u.ui),
             foreign=b("on" if u.keep_foreign else "off", u.ui),
             fmt=b("codefmt" if u.fmt == "kod" else "plain", u.ui))


@router.message(Command("sozlama", "settings"))
async def cmd_settings(message: Message, user: User) -> None:
    await message.answer(_view(user), reply_markup=settings_kb(user))


@router.callback_query(F.data.startswith("st|"))
async def cb_settings(call: CallbackQuery, user: User) -> None:
    _, field, action = call.data.split("|")
    if field == "mode":
        user.mode = _MODE_CYCLE[(_MODE_CYCLE.index(user.mode) + 1) % len(_MODE_CYCLE)]
        await db.set_field(user.user_id, "mode", user.mode)
    elif field == "ui":
        user.ui = _UI_CYCLE[(_UI_CYCLE.index(user.ui) + 1) % len(_UI_CYCLE)]
        await db.set_field(user.user_id, "ui", user.ui)
        await call.message.answer(t("mode_set", user.ui, mode=b(user.ui, user.ui)),
                                  reply_markup=main_kb(user.ui))
    elif field == "fmt":
        user.fmt = "oddiy" if user.fmt == "kod" else "kod"
        await db.set_field(user.user_id, "fmt", user.fmt)
    elif field in ("smart", "keep_foreign"):
        new = 0 if getattr(user, field) else 1
        setattr(user, field, new)
        await db.set_field(user.user_id, field, new)
    try:
        await call.message.edit_text(_view(user), reply_markup=settings_kb(user))
    except Exception:
        pass
    await call.answer()
