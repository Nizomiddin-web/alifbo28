from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser

from .. import db


class UserMiddleware(BaseMiddleware):
    """Har bir hodisaga baza yozuvini (`user`) qöşib beradi."""

    async def __call__(self, handler: Callable[[TelegramObject, dict], Awaitable[Any]],
                       event: TelegramObject, data: dict[str, Any]) -> Any:
        tg: TgUser | None = data.get("event_from_user")
        if tg is not None and not tg.is_bot:
            data["user"] = await db.get_user(tg.id, tg.username, tg.full_name)
        return await handler(event, data)
