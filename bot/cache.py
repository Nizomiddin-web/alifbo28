"""Tugmalar uçun asl matnlarni vaqtinça saqlaş."""
from __future__ import annotations

import time
from collections import OrderedDict
from itertools import count

_MAX = 20_000
_TTL = 60 * 60 * 24  # 1 kun
_counter = count(1)
_store: "OrderedDict[str, tuple[float, str]]" = OrderedDict()

_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"


def _b36(n: int) -> str:
    out = ""
    while n:
        n, r = divmod(n, 36)
        out = _ALPHABET[r] + out
    return out or "0"


def put(text: str) -> str:
    key = _b36(next(_counter))
    _store[key] = (time.time(), text)
    _store.move_to_end(key)
    while len(_store) > _MAX:
        _store.popitem(last=False)
    return key


def get(key: str) -> str | None:
    item = _store.get(key)
    if item is None:
        return None
    ts, text = item
    if time.time() - ts > _TTL:
        _store.pop(key, None)
        return None
    return text
