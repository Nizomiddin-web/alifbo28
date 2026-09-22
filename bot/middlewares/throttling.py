from __future__ import annotations

import time
from collections import OrderedDict
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User


class ThrottleMiddleware(BaseMiddleware):
    """Bir foydalanuvçidan keladigan xabarlarni çeklaydi."""

    def __init__(self, rate: float = 0.5, cache_size: int = 10_000) -> None:
        self.rate = rate
        self._seen: OrderedDict[int, float] = OrderedDict()
        self._size = cache_size

    async def __call__(self, handler: Callable[[TelegramObject, dict], Awaitable[Any]],
                       event: TelegramObject, data: dict[str, Any]) -> Any:
        user: User | None = data.get("event_from_user")
        if user is not None and self.rate > 0:
            now = time.monotonic()
            last = self._seen.get(user.id, 0.0)
            if now - last < self.rate:
                return None
            self._seen[user.id] = now
            self._seen.move_to_end(user.id)
            while len(self._seen) > self._size:
                self._seen.popitem(last=False)
        return await handler(event, data)
