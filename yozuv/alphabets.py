"""Alifbo jadvallari: eski lotin, yangi lotin va kirill."""
from __future__ import annotations

# ---------------------------------------------------------------- belgilar
# Tutuq belgisi (ʼ) va "oʻ/gʻ" tutashtiruvçisi (ʻ) rasman ikki xil belgi,
# ammo foydalanuvçilar ularni ön-öngi apostroflar bilan yozadi.
# Rasmiy jadval böyiça tutuq belgisi ikkala alifboda ham "’" (U+2019),
# amaldagi alifbodagi Oʻ/Gʻ da esa "ʻ" (U+02BB) qöllanadi.
OKINA = "ʻ"   # ʻ  U+02BB  amaldagi alifbo: oʻ, gʻ
TUTUQ = "’"   # ’  U+2019  tutuq belgisi: a’lo, san’at

#: apostrof sifatida qabul qilinadigan barça belgilar
APOSTROPHES = (
    "'"        # U+0027 ASCII
    "‘"   # ‘
    "’"   # ’
    "‛"   # ‛
    "ʹ"   # ʹ
    "ʻ"   # ʻ
    "ʼ"   # ʼ
    "ʽ"   # ʽ
    "ˈ"   # ˈ
    "`"   # `
    "´"   # ´
    "′"   # ′
    "‵"   # ‵
    "＇"   # ＇
)
APOS_CLASS = "[" + "".join("\\" + c if c in "^]\\-" else c for c in APOSTROPHES) + "]"

# ---------------------------------------------------------- yangi harflar
NEW_LETTERS = "çÇşŞğĞöÖ"
OLD_ONLY = ("sh", "ch", "o" + OKINA, "g" + OKINA)

#: yangi → amaldagi juftliklar (kiçik harf)
NEW_TO_OLD_MAP = {
    "ç": "ch",
    "ş": "sh",
    "ğ": "g" + OKINA,
    "ö": "o" + OKINA,
}

# ------------------------------------------------- rasmiy alifbo jadvali
#: yangi alifbo — 28 harf, tartib böyiça (yangi_bosh, yangi_kiçik,
#: amaldagi_bosh, amaldagi_kiçik)
ALPHABET: tuple[tuple[str, str, str, str], ...] = (
    ("A", "a", "A", "a"),
    ("B", "b", "B", "b"),
    ("D", "d", "D", "d"),
    ("E", "e", "E", "e"),
    ("F", "f", "F", "f"),
    ("G", "g", "G", "g"),
    ("Ğ", "ğ", "G" + OKINA, "g" + OKINA),
    ("H", "h", "H", "h"),
    ("I", "i", "I", "i"),
    ("J", "j", "J", "j"),
    ("K", "k", "K", "k"),
    ("L", "l", "L", "l"),
    ("M", "m", "M", "m"),
    ("N", "n", "N", "n"),
    ("O", "o", "O", "o"),
    ("P", "p", "P", "p"),
    ("Q", "q", "Q", "q"),
    ("R", "r", "R", "r"),
    ("S", "s", "S", "s"),
    ("T", "t", "T", "t"),
    ("U", "u", "U", "u"),
    ("V", "v", "V", "v"),
    ("X", "x", "X", "x"),
    ("Y", "y", "Y", "y"),
    ("Z", "z", "Z", "z"),
    ("Ö", "ö", "O" + OKINA, "o" + OKINA),
    ("Ç", "ç", "Ch", "ch"),
    ("Ş", "ş", "Sh", "sh"),
)

#: alifbo tarkibidagi harflar soni (tutuq belgisisiz)
ALPHABET_SIZE = len(ALPHABET)

#: alifbodan çiqarilgan, ammo sözlarda saqlanadigan harflar birikmasi
REMOVED_DIGRAPH = "ng"

# --------------------------------------------------------------- unlilar
LAT_VOWELS = "aeiouöAEIOUÖ"
CYR_VOWELS = "аеёиоуэюяўыАЕЁИОУЭЮЯЎЫ"

# ------------------------------------------------------- kirill → lotin
#: yangi alifbodagi qiymatlar; eski alifboga keyin qayta ötkaziladi
CYR_TO_LAT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d",
    "ж": "j", "з": "z", "и": "i", "й": "y", "к": "k",
    "л": "l", "м": "m", "н": "n", "о": "o", "п": "p",
    "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f",
    "х": "x", "ч": "ç", "ш": "ş", "ъ": TUTUQ, "ы": "i",
    "ь": "", "э": "e", "ё": "yo", "ю": "yu", "я": "ya",
    "ў": "ö", "қ": "q", "ғ": "ğ", "ҳ": "h", "щ": "şç",
    "е": "e", "ц": "s",
    # qörşi alifbolardan kirib qolgan belgilar
    "ї": "i", "і": "i", "ђ": "d", "є": "e",
}

# ------------------------------------------------------- lotin → kirill
LAT_DIGRAPH_TO_CYR = [
    # ruscha ösimlaşmalar: «ts» faqat işonçli naqşlarda «ц» böladi
    # (aks holda «ketsa → кеца» kabi yolğon ijobiy çiqadi)
    ("tsiya", "ция"), ("tsion", "цион"), ("tss", "цц"),
    ("yo", "ё"), ("yu", "ю"), ("ya", "я"), ("ye", "е"),
    ("sh", "ш"), ("ch", "ч"),
    ("o" + OKINA, "ў"), ("g" + OKINA, "ғ"),
]
LAT_TO_CYR = {
    "a": "а", "b": "б", "v": "в", "g": "г", "d": "д",
    "j": "ж", "z": "з", "i": "и", "y": "й", "k": "к",
    "l": "л", "m": "м", "n": "н", "o": "о", "p": "п",
    "r": "р", "s": "с", "t": "т", "u": "у", "f": "ф",
    "x": "х", "h": "ҳ", "q": "қ", "c": "с", "w": "в",
    "ç": "ч", "ş": "ш", "ö": "ў", "ğ": "ғ",
    "e": "е", TUTUQ: "ъ", "ʼ": "ъ",
}
