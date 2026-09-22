"""Özbek yozuvlari orasida ötkazgiç.

Qöllab-quvvatlanadigan yönaliş:
    amaldagi lotin (oʻ, gʻ, sh, ch)  →  yangi lotin (ö, ğ, ş, ç)
    yangi lotin                      →  amaldagi lotin
    kirill                           →  yangi / amaldagi lotin
    lotin (har ikkisi)               →  kirill
"""
from __future__ import annotations

import re
from dataclasses import dataclass, replace as _dc_replace
from enum import Enum
from functools import lru_cache
from pathlib import Path

from .alphabets import (
    APOS_CLASS,
    APOSTROPHES,
    CYR_TO_LAT,
    CYR_VOWELS,
    LAT_DIGRAPH_TO_CYR,
    LAT_TO_CYR,
    LAT_VOWELS,
    OKINA,
    TUTUQ,
)
from .detect import Script, detect

_DATA = Path(__file__).with_name("data") / "exceptions.txt"

#: içki ajratgiç — kirill manbadan kelgan qöşni harflar lotin tomonda
#: tasodifan digrafga (sh, ch, oʻ, gʻ) qöşilib ketmasligi uçun qöyiladi
GUARD = "\x00"

#: matn oldidan keladigan oçuvçi tirnoqlar (yopuvçi apostrofni ajratiş uçun)
OPENERS = "'‘“«‹\"„"


class Target(str, Enum):
    NEW = "yangi"      # yangi lotin alifbosi (28 harf)
    OLD = "eski"       # amaldagi lotin alifbosi
    CYR = "kirill"     # kirill
    AUTO = "avto"      # manbaga qarab teskarisini tanlaydi


@dataclass(frozen=True)
class Options:
    #: havola, e-poçta, @username, #hashtag va kodni tegmay qoldiriş
    smart_links: bool = True
    #: hashtaglarni ham himoyalaş
    protect_hashtags: bool = True
    #: exceptions.txt dagi xalqaro sözlarni saqlaş
    keep_foreign: bool = True
    #: har xil apostroflarni kanonik körinişga keltiriş
    normalize_apostrophes: bool = True
    #: /buyruq körinişidagi sözlarni tegmay qoldiriş (bot interfeysi uçun)
    protect_commands: bool = False


DEFAULT = Options()


@dataclass(frozen=True)
class Result:
    text: str
    source: Script
    target: Target
    changed: bool

    def __str__(self) -> str:  # pragma: no cover - qulaylik uçun
        return self.text


# --------------------------------------------------------------------------
# Himoyalanadigan bölaklar
# --------------------------------------------------------------------------
_PROTECT_PARTS = [
    r"```.*?```",                                   # kod bloki
    r"`[^`\n]*`",                                   # inline kod
    r"<[/!a-zA-Z][^<>\n]*>",                        # HTML teg
    r"\{[a-zA-Z_][a-zA-Z0-9_]*\}",                  # {placeholder}
    r"https?://\S+",                                # havola
    r"www\.\S+",                                    # havola
    r"[\w.+-]+@[\w-]+\.[\w.-]+",                    # e-poçta
    r"@[A-Za-z][A-Za-z0-9_]{2,}",                   # @username
    r"\b[a-zA-Z0-9-]+\.(?:uz|com|net|org|ru|io|me|info|edu|gov|tv|dev|app|ai)\b(?:/\S*)?",
]
_PROTECT_RE = re.compile("|".join(_PROTECT_PARTS), re.S)
_HASHTAG_RE = re.compile(r"#\w+", re.U)
_COMMAND_RE = re.compile(r"/[a-zA-Z][a-zA-Z0-9_]*")


@lru_cache(maxsize=1)
def _exception_words() -> tuple[tuple[str, ...], tuple[str, ...]]:
    """(oddiy istisnolar, xorijiy sözlar) — exceptions.txt dan öqiladi."""
    plain: list[str] = []
    foreign: list[str] = []
    bucket = plain
    if _DATA.exists():
        for raw in _DATA.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.lower() == "@foreign":
                bucket = foreign
                continue
            bucket.append(line)
    return tuple(plain), tuple(foreign)


@lru_cache(maxsize=8)
def _exception_re(plain: bool, foreign: bool) -> re.Pattern[str] | None:
    """Istisno sözlar naqşi.

    Oxirida `\\b` yöq — şu sababli söz qöşimça bilan kelganda ham
    (Chelseaning, Ishoqning) asosning özi himoyalanadi.
    """
    p, f = _exception_words()
    words = (list(p) if plain else []) + (list(f) if foreign else [])
    if not words:
        return None
    words.sort(key=len, reverse=True)
    return re.compile(r"\b(?:" + "|".join(re.escape(w) for w in words) + r")", re.I)


def _exceptions_for(mode: str, opts: Options) -> re.Pattern[str] | None:
    if mode == "none":
        return None
    if mode == "foreign":
        return _exception_re(False, opts.keep_foreign)
    return _exception_re(True, opts.keep_foreign)


def _protected_spans(text: str, opts: Options, exceptions: str = "all") -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    if opts.smart_links:
        spans += [m.span() for m in _PROTECT_RE.finditer(text)]
        if opts.protect_hashtags:
            spans += [m.span() for m in _HASHTAG_RE.finditer(text)]
    if opts.protect_commands:
        spans += [m.span() for m in _COMMAND_RE.finditer(text)]
    rx = _exceptions_for(exceptions, opts)
    if rx is not None:
        spans += [m.span() for m in rx.finditer(text)]
    if not spans:
        return []
    spans.sort()
    merged = [spans[0]]
    for s, e in spans[1:]:
        if s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    return merged


def _map_free(text: str, fn, opts: Options, exceptions: str = "all") -> str:
    """`fn` ni faqat himoyalanmagan bölaklarga qöllaydi."""
    spans = _protected_spans(text, opts, exceptions)
    if not spans:
        return fn(text)
    out: list[str] = []
    pos = 0
    for s, e in spans:
        if pos < s:
            out.append(fn(text[pos:s]))
        out.append(text[s:e])
        pos = e
    if pos < len(text):
        out.append(fn(text[pos:]))
    return "".join(out)


# --------------------------------------------------------------------------
# Yordamçi: katta/kiçik harf va tirnoq konteksti
# --------------------------------------------------------------------------
def _caps_context(text: str, start: int, end: int) -> bool:
    """`text[start:end]` atrofidagi söz butunlay katta harfdami?

    Butun sözni tekşiradi: bitta katta harf yetarli emas, aks holda
    «A’zam» ham ALL-CAPS deb hisoblanib «АЪзам» çiqardi.
    Içki ajratgiç (GUARD) sözni uzmaydi — u körinmas belgi.
    """
    seen_upper = False
    for step, first in ((-1, start - 1), (1, end)):
        i = first
        while 0 <= i < len(text):
            ch = text[i]
            if ch == GUARD:
                i += step
                continue
            if not ch.isalpha():
                break
            if ch.islower():
                return False
            seen_upper = True
            i += step
    return seen_upper


#: qaysi apostrofni qaysi oçuvçi tirnoq yopa oladi.
#: «tog'» da oçuvçi « bölgani uçun oxirgi ' tirnoq emas — harfning qismi.
_QUOTE_OPENERS = {
    "'": ("'",),
    "\u2019": ("\u2018", "'", "\u201a"),
    "\u02bc": ("\u02bb", "'"),
    "\u2032": ("\u2035", "'"),
    "\u00b4": ("`", "'"),
    "`": ("`",),
}


def _is_closing_quote(text: str, idx: int, apos: str) -> bool:
    """`idx` dagi apostrof — sözning bir qismimi yoki yopuvçi tirnoqmi?

    Faqat söz oldidagi oçuvçi tirnoq şu apostrof bilan JUFT bölsa,
    uni tirnoq deb hisoblaymiz.
    """
    openers = _QUOTE_OPENERS.get(apos)
    if not openers:
        return False
    i = idx
    while i > 0:
        ch = text[i - 1]
        if ch == GUARD or ch.isalpha() or ch.isdigit():
            i -= 1
            continue
        # söz içidagi apostrof (ma’lum) sözning qismi, söz oldidagisi esa yöq
        if ch in APOSTROPHES and i >= 2 and (text[i - 2].isalpha() or text[i - 2].isdigit()):
            i -= 1
            continue
        break
    return i > 0 and text[i - 1] in openers


def _sanitize(text: str) -> str:
    """Kiriş matnidan içki ajratgiçni olib taşlaydi.

    GUARD — içki belgi. Foydalanuvçi matnida (masalan buzilgan faylda)
    uçrab qolsa, natijani buzişi mumkin edi.
    """
    return text.replace(GUARD, "") if GUARD in text else text


def _cased(out: str, upper_first: bool, all_caps: bool) -> str:
    if not out:
        return out
    if all_caps:
        return out.upper()
    if upper_first:
        return out[0].upper() + out[1:]
    return out


# --------------------------------------------------------------------------
# Amaldagi lotin → yangi lotin
# --------------------------------------------------------------------------
_OG_RE = re.compile(r"([oOgG])(" + APOS_CLASS + r")")
_SH_RE = re.compile(r"[sS][hH]")
_CH_RE = re.compile(r"[cC][hH]")
_LOOSE_APOS_RE = re.compile(r"(?<=[^\W\d_])" + APOS_CLASS, re.U)


def _make_og_sub(text: str):
    def _sub(m: re.Match[str]) -> str:
        nxt = text[m.end():m.end() + 1]
        if not (nxt.isalpha() or nxt.isdigit()) and m.group(2) != OKINA:
            # söz oxiridagi oddiy apostrof yopuvçi tirnoq bölişi mumkin
            if _is_closing_quote(text, m.start(2), m.group(2)):
                return m.group(0)
        base = "ö" if m.group(1).lower() == "o" else "ğ"
        return base.upper() if m.group(1).isupper() else base
    return _sub


def _digraph_sub(single: str):
    def _sub(m: re.Match[str]) -> str:
        s = m.group(0)
        return single.upper() if s[0].isupper() else single
    return _sub


def _old_to_new_raw(text: str, opts: Options) -> str:
    text = _OG_RE.sub(_make_og_sub(text), text)
    if opts.normalize_apostrophes:
        def _apos(m: re.Match[str]) -> str:
            nxt = text[m.end():m.end() + 1]
            if not (nxt.isalpha() or nxt.isdigit()) and \
                    _is_closing_quote(text, m.start(), m.group(0)):
                return m.group(0)       # yopuvçi tirnoq
            return TUTUQ
        text = _LOOSE_APOS_RE.sub(_apos, text)
    text = _SH_RE.sub(_digraph_sub("ş"), text)
    text = _CH_RE.sub(_digraph_sub("ç"), text)
    return text


def _old_to_new(text: str, opts: Options) -> str:
    """Içki: ajratgiçlarga tegmaydi (quvur içida işlatiladi)."""
    return _map_free(text, lambda s: _old_to_new_raw(s, opts), opts)


def old_to_new(text: str, opts: Options = DEFAULT) -> str:
    return _old_to_new(_sanitize(text), opts)


# --------------------------------------------------------------------------
# Yangi lotin → amaldagi lotin
# --------------------------------------------------------------------------
_NEW_RE = re.compile(r"[şŞçÇöÖğĞ]")
_NEW_PAIR = {"ş": "sh", "ç": "ch", "ö": "o" + OKINA, "ğ": "g" + OKINA}


def _new_to_old_raw(text: str, opts: Options) -> str:
    def _sub(m: re.Match[str]) -> str:
        ch = m.group(0)
        low = ch.lower()
        out = _NEW_PAIR[low]
        if not ch.isupper():
            return out
        if low in ("ö", "ğ"):
            return out[0].upper() + out[1:]
        return out.upper() if _caps_context(text, m.start(), m.end()) else out.capitalize()

    return _NEW_RE.sub(_sub, text)


def _new_to_old(text: str, opts: Options) -> str:
    """Içki: ajratgiçlarga tegmaydi (quvur içida işlatiladi)."""
    return _map_free(text, lambda s: _new_to_old_raw(s, opts), opts)


def new_to_old(text: str, opts: Options = DEFAULT) -> str:
    return _new_to_old(_sanitize(text), opts)


# --------------------------------------------------------------------------
# Kirill → lotin (yangi alifbo)
# --------------------------------------------------------------------------
def _cyr_to_lat_raw(text: str, opts: Options, guard: bool = False) -> str:
    out: list[str] = []
    n = len(text)
    for i, ch in enumerate(text):
        low = ch.lower()
        if low not in CYR_TO_LAT:
            out.append(ch)
            continue
        prev = text[i - 1] if i else ""
        nxt = text[i + 1] if i + 1 < n else ""
        if low == "е":
            piece = "ye" if (not prev.isalpha() or prev in CYR_VOWELS or prev in "ъьЪЬ") else "e"
        elif low == "ц":
            if prev and prev.lower() == "ц":
                piece = ""              # пицца → pitsa
            else:
                piece = "ts" if (prev and prev in CYR_VOWELS) else "s"
        elif low == "ъ":
            # DIQQAT: `nxt` böş bölişi mumkin — matn oxiridagi «ъ» yöqolmasin
            piece = "" if (nxt and nxt.lower() in "еёюя") else TUTUQ
        else:
            piece = CYR_TO_LAT[low]
        if ch.isupper():
            piece = _cased(piece, True, _caps_context(text, i, i + 1))
        out.append(piece)
        if guard:
            out.append(GUARD)
    return "".join(out)


def cyr_to_lat(text: str, opts: Options = DEFAULT) -> str:
    # kirill bir maʼnoli — istisno röyxati bu yerda kerak emas
    return _map_free(_sanitize(text), lambda s: _cyr_to_lat_raw(s, opts), opts,
                     exceptions="none")


def _strip_guard(text: str, mark_split: bool) -> str:
    """Ajratgiçlarni olib taşlaydi.

    `mark_split=True` bölsa (amaldagi alifbo), «s»+«h» kabi qöşilib ketişi
    mumkin bölgan joyga tutuq belgisi qöyiladi: тасҳиҳ → tas’hih.
    Yangi alifboda bunga hojat yöq, çunki «ş» yaxlit harf: tashih.
    """
    if GUARD not in text:
        return text
    out: list[str] = []
    for i, ch in enumerate(text):
        if ch != GUARD:
            out.append(ch)
            continue
        if mark_split and out:
            nxt = text[i + 1] if i + 1 < len(text) else ""
            if out[-1].lower() in ("s", "c") and nxt.lower() == "h":
                out.append(TUTUQ)
    return "".join(out)


# --------------------------------------------------------------------------
# Lotin → kirill
# --------------------------------------------------------------------------
def _split_exception_digraphs(word: str) -> str:
    """Istisno söz içidagi «sh»/«ch» ni ajratgiç bilan bölib qöyadi."""
    return re.sub(r"([sScC])([hH])", r"\1" + GUARD + r"\2", word)


def _lat_to_cyr_raw(text: str, opts: Options) -> str:
    # 1) avval yangi lotinga keltiramiz (istisnolarni hisobga olib)
    text = _old_to_new(text, opts)
    # 2) oddiy istisnolarda s+h alohida talaffuz qilinadi: Ishoq → Исҳоқ
    rx = _exception_re(True, False)
    if rx is not None:
        text = rx.sub(lambda m: _split_exception_digraphs(m.group(0)), text)

    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        if text[i] == GUARD:
            i += 1
            continue
        hit = None
        for dig, cyr in LAT_DIGRAPH_TO_CYR:
            seg = text[i:i + len(dig)]
            if seg.lower() == dig:
                hit = (seg, cyr)
                break
        if hit:
            seg, cyr = hit
            piece = _cased(cyr, seg[0].isupper(), len(seg) > 1 and seg.isupper())
            if seg.lower() == "ye":
                prev = text[i - 1] if i else ""
                # ruscha ösimlaşmalarda undoşdan keyin ajratuvçi «ъ» turadi
                if prev.isalpha() and prev not in LAT_VOWELS and prev.lower() != "y":
                    piece = ("Ъ" if prev.isupper() else "ъ") + piece
            out.append(piece)
            i += len(seg)
            continue
        ch = text[i]
        low = ch.lower()
        if low in LAT_TO_CYR:
            piece = LAT_TO_CYR[low]
            if low == "e":
                prev = text[i - 1] if i else ""
                # söz boşida va unlidan keyin — «э» (aeroport → аэропорт)
                if not prev.isalpha() or prev in LAT_VOWELS:
                    piece = "э"
            if ch in (TUTUQ, "ʼ"):
                nxt = text[i + 1] if i + 1 < n else ""
                if not nxt.isalpha() and _is_closing_quote(text, i, ch):
                    out.append(ch)          # yopuvçi tirnoq — tegmaymiz
                    i += 1
                    continue
                if _caps_context(text, i, i + 1):
                    piece = piece.upper()   # SAN’AT → САНЪАТ
            elif ch.isupper():
                piece = piece.upper()
            out.append(piece)
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def lat_to_cyr(text: str, opts: Options = DEFAULT) -> str:
    # xalqaro brendlar kirill matnda ham lotinça qoladi, oddiy istisnolar esa
    # harfma-harf ötkaziladi
    return _map_free(_sanitize(text), lambda s: _lat_to_cyr_raw(s, opts), opts,
                     exceptions="foreign")


# --------------------------------------------------------------------------
# Yüqori darajali API
# --------------------------------------------------------------------------
def _cyr_stage(text: str, opts: Options) -> str:
    return _map_free(_sanitize(text), lambda s: _cyr_to_lat_raw(s, opts, guard=True), opts,
                     exceptions="none")


def to_new(text: str, opts: Options = DEFAULT) -> str:
    return _strip_guard(_old_to_new(_cyr_stage(text, opts), opts), mark_split=False)


def to_old(text: str, opts: Options = DEFAULT) -> str:
    # avval yangi alifboga keltiramiz — şunda har xil apostroflar ham
    # kanonik "oʻ / gʻ / ’" körinişiga tuşadi
    mid = _old_to_new(_cyr_stage(text, opts), opts)
    return _strip_guard(_new_to_old(mid, opts), mark_split=True)


def to_cyrillic(text: str, opts: Options = DEFAULT) -> str:
    return lat_to_cyr(text, opts)


_TARGETS = {
    Target.NEW: to_new,
    Target.OLD: to_old,
    Target.CYR: to_cyrillic,
}


def convert(text: str, target: Target | str = Target.NEW, opts: Options = DEFAULT) -> Result:
    """Matnni köraslangan yozuvga ötkazadi."""
    target = Target(target)
    src = detect(text)
    real = target
    if target is Target.AUTO:
        real = Target.OLD if src is Script.NEW_LATIN else Target.NEW
    new_text = _TARGETS[real](text, opts)
    return Result(text=new_text, source=src, target=real, changed=new_text != text)


def options_from(**kwargs) -> Options:
    return _dc_replace(DEFAULT, **kwargs)
