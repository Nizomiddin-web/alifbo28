from __future__ import annotations

from aiogram import Router
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InlineQueryResultsButton,
    InputTextMessageContent,
)

from yozuv import Target, detect

from ..db import User
from ..texts import MODE_NAME, render
from ..utils import SAFE_LIMIT, convert_for

router = Router(name="inline")

_ICON = {"yangi": "🆕", "eski": "🔙", "kirill": "🇺🇿"}


@router.inline_query()
async def inline_convert(query: InlineQuery, user: User) -> None:
    text = (query.query or "").strip()
    if not text:
        await query.answer(
            results=[],
            cache_time=5,
            is_personal=True,
            button=InlineQueryResultsButton(
                text=render("Matn yozing — o'giraman", user.ui),
                start_parameter="inline",
            ),
        )
        return

    text = text[:SAFE_LIMIT]
    src = detect(text).value
    order = [m for m in ("yangi", "eski", "kirill") if m != src] + \
            [m for m in ("yangi", "eski", "kirill") if m == src]

    results = []
    for i, mode in enumerate(order):
        out = convert_for(user, text, mode).text
        results.append(InlineQueryResultArticle(
            id=f"{mode}-{abs(hash(text)) % 10**8}",
            title=f"{_ICON[mode]} {render(MODE_NAME[mode], user.ui)}",
            description=out[:90],
            input_message_content=InputTextMessageContent(message_text=out),
        ))
    await query.answer(results=results, cache_time=30, is_personal=True)
