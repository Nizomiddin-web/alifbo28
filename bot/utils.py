from __future__ import annotations

import html
import re

from yozuv import Options, Target, convert, options_from

from .db import User

TG_LIMIT = 4096
SAFE_LIMIT = 3900


def user_options(user: User) -> Options:
    return options_from(smart_links=bool(user.smart), keep_foreign=bool(user.keep_foreign))


def convert_for(user: User, text: str, target: str | None = None):
    return convert(text, Target(target or user.mode or "yangi"), user_options(user))


_SPLIT_AT = re.compile(r"(?<=\n\n)|(?<=\n)|(?<=[.!?…] )|(?<= )")


def split_text(text: str, limit: int = SAFE_LIMIT) -> list[str]:
    """Uzun matnni Telegram çegarasiga sığadigan bölaklarga ajratadi."""
    if len(text) <= limit:
        return [text]
    parts: list[str] = []
    rest = text
    while len(rest) > limit:
        window = rest[:limit]
        cut = max(window.rfind("\n\n"), window.rfind("\n"), window.rfind(". "), window.rfind(" "))
        if cut <= 0:
            cut = limit
        parts.append(rest[:cut].rstrip())
        rest = rest[cut:].lstrip()
    if rest:
        parts.append(rest)
    return parts


def as_html(text: str, fmt: str = "oddiy") -> str:
    esc = html.escape(text, quote=False)
    return f"<code>{esc}</code>" if fmt == "kod" else esc
