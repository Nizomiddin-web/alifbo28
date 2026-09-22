"""Matn qaysi yozuvda ekanini aniqlaş."""
from __future__ import annotations

import re
from enum import Enum

from .alphabets import APOS_CLASS, NEW_LETTERS

_CYR_RE = re.compile(r"[Ѐ-ӿ]")
_LAT_RE = re.compile(r"[A-Za-z]")
_NEW_RE = re.compile("[" + NEW_LETTERS + "]")
_OLD_RE = re.compile(r"(?i)(?:sh|ch)|(?:[og]" + APOS_CLASS + ")")


class Script(str, Enum):
    CYRILLIC = "kirill"
    NEW_LATIN = "yangi"
    OLD_LATIN = "eski"
    NEUTRAL = "neytral"     # lotin, ammo farqli belgisi yöq
    UNKNOWN = "noma’lum"


def counts(text: str) -> dict[str, int]:
    return {
        "cyr": len(_CYR_RE.findall(text)),
        "lat": len(_LAT_RE.findall(text)),
        "new": len(_NEW_RE.findall(text)),
        "old": len(_OLD_RE.findall(text)),
    }


def detect(text: str) -> Script:
    """Matnning asosiy yozuvini qaytaradi."""
    c = counts(text)
    if not c["cyr"] and not c["lat"]:
        return Script.UNKNOWN
    if c["cyr"] > c["lat"]:
        return Script.CYRILLIC
    if c["new"] and c["new"] >= c["old"]:
        return Script.NEW_LATIN
    if c["old"]:
        return Script.OLD_LATIN
    if c["cyr"]:
        return Script.CYRILLIC
    return Script.NEUTRAL


def is_mixed(text: str) -> bool:
    c = counts(text)
    return bool(c["cyr"]) and bool(c["lat"])
