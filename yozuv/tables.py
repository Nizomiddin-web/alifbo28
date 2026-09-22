"""Rasmiy alifbo jadvali va misollar.

Misollardagi yangi alifbo şakllari qölda yozilmaydi — ötkazgiçning özi
hisoblaydi, şunda jadval bilan kod hеç qaçon bir-biridan uzoqlaşmaydi.
"""
from __future__ import annotations

from .alphabets import ALPHABET, ALPHABET_SIZE, OKINA, REMOVED_DIGRAPH, TUTUQ

__all__ = [
    "ALPHABET_SIZE", "EXAMPLES", "alphabet_rows", "alphabet_table",
    "example_pairs", "examples_text", "letter_note",
]


def alphabet_rows() -> list[tuple[int, str, str]]:
    """[(tartib raqami, "Ğ ğ", "Gʻ gʻ"), ...] — 28 ta harf."""
    return [(i, f"{nu} {nl}", f"{ou} {ol}")
            for i, (nu, nl, ou, ol) in enumerate(ALPHABET, start=1)]


def alphabet_table() -> str:
    """Monoşrift uçun soliştirma jadval (Telegramda <pre> içida körsatiladi)."""
    rows = alphabet_rows()
    w_new = max(len(r[1]) for r in rows + [(0, "Yangi", "")])
    w_old = max([len(r[2]) for r in rows] + [len("Amaldagi")])
    head = f"{'№':>2}  {'Yangi':<{w_new}}  {'Amaldagi':<{w_old}}"
    body = [f"{n:>2}  {new:<{w_new}}  {old:<{w_old}}" for n, new, old in rows]
    tail = [
        f"{ALPHABET_SIZE + 1:>2}  {TUTUQ:<{w_new}}  {TUTUQ:<{w_old}}  tutuq belgisi",
        f"{'–':>2}  {'':<{w_new}}  {REMOVED_DIGRAPH:<{w_old}}  alifbodan çiqarildi",
    ]
    width = max(len(x) for x in [head, *body, *tail])
    line = "─" * width
    return "\n".join([head, line, *[x.rstrip() for x in body], line,
                      *[x.rstrip() for x in tail]])


def letter_note() -> str:
    """Jadval ostidagi izoh."""
    return (
        f"Yangi alifboda {ALPHABET_SIZE} ta harf va 1 ta tutuq belgisi bor.\n"
        f"Qöşma harflar (O{OKINA}, G{OKINA}, Sh, Ch) örniga yaxlit "
        f"Ö, Ğ, Ş, Ç joriy etildi.\n"
        f"«{REMOVED_DIGRAPH}» alifbodan çiqarildi, ammo sözlar içida "
        f"(tong, köngil) saqlanaveradi."
    )


#: (sarlavha, amaldagi alifbodagi misol sözlar)
EXAMPLES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (f"O{OKINA} o{OKINA}  →  Ö ö", (
        "O" + OKINA + "zbekiston", "o" + OKINA + "qituvchi", "ko" + OKINA + "cha",
        "so" + OKINA + "z", "to" + OKINA + "g" + OKINA + "ri", "o" + OKINA + "rtoq",
    )),
    (f"G{OKINA} g{OKINA}  →  Ğ ğ", (
        "yomg" + OKINA + "ir", "g" + OKINA + "alaba", "tog" + OKINA,
        "bog" + OKINA + "bon", "og" + OKINA + "ir", "sog" + OKINA + "lom",
    )),
    ("Sh sh  →  Ş ş", (
        "shahar", "ishchi", "yoshlar", "mashhur", "quyosh", "Toshkent",
    )),
    ("Ch ch  →  Ç ç", (
        "chiroq", "kecha", "uchun", "ochiq", "kuch", "Chirchiq",
    )),
    (f"Tutuq belgisi  →  {TUTUQ}", (
        "ma" + TUTUQ + "no", "san" + TUTUQ + "at", "ta" + TUTUQ + "lim",
        "e" + TUTUQ + "lon", "shu" + TUTUQ + "la",
    )),
    (f"«{REMOVED_DIGRAPH}» saqlanadi", (
        "ko" + OKINA + "ngil", "tong", "singil", "yangi", "dengiz",
    )),
)


def example_pairs() -> list[tuple[str, list[tuple[str, str]]]]:
    """[(sarlavha, [(amaldagi, yangi), ...]), ...]"""
    from .converter import to_new
    return [(title, [(w, to_new(w)) for w in words]) for title, words in EXAMPLES]


def examples_text(arrow: str = " → ") -> str:
    blocks = []
    for title, pairs in example_pairs():
        width = max(len(a) for a, _ in pairs)
        lines = [f"{a:<{width}}{arrow}{b}" for a, b in pairs]
        blocks.append(title + "\n" + "\n".join(lines))
    return "\n\n".join(blocks)
