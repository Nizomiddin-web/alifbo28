"""Rasmiy alifbo jadvaliga muvofiqlik testlari."""
from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from yozuv import to_cyrillic, to_new, to_old  # noqa: E402
from yozuv.alphabets import (  # noqa: E402
    ALPHABET, ALPHABET_SIZE, OKINA, REMOVED_DIGRAPH, TUTUQ,
)
from yozuv.tables import EXAMPLES, alphabet_rows, alphabet_table, example_pairs  # noqa: E402

fails = 0
LEGACY_TUTUQ = "ʼ"   # ʼ — eskicha variant, endi çiqmasligi kerak


def check(cond, label, extra=""):
    global fails
    if not cond:
        fails += 1
    print(f"[{'OK ' if cond else 'XATO'}] {label}{(' — ' + str(extra)) if not cond else ''}")


# ---------------------------------------------------- alifbo tarkibi
check(ALPHABET_SIZE == 28, "alifboda 28 ta harf", ALPHABET_SIZE)
lower = [a[1] for a in ALPHABET]
check(len(set(lower)) == 28, "harflar takrorlanmaydi")
check(set("çşğö") <= set(lower), "yangi harflar bor")
check("c" not in lower and "w" not in lower, "alifboda c va w yöq")
check(REMOVED_DIGRAPH == "ng" and "ng" not in lower, "ng alifbo tarkibida emas")

check(ord(TUTUQ) == 0x2019, "tutuq belgisi U+2019", hex(ord(TUTUQ)))
check(ord(OKINA) == 0x02BB, "amaldagi alifbo belgisi U+02BB", hex(ord(OKINA)))
check(unicodedata.name(TUTUQ) == "RIGHT SINGLE QUOTATION MARK", "tutuq belgisi nomi")

# har bir harf jadvalda töğri juftlangan
for new_u, new_l, old_u, old_l in ALPHABET:
    ok = to_new(old_l) == new_l and to_new(old_u + old_l) == new_u + new_l
    if not ok:
        check(False, f"jadval juftligi {old_l} → {new_l}", (to_new(old_l), to_new(old_u + old_l)))
check(all(to_new(o_l) == n_l for _, n_l, _, o_l in ALPHABET), "28 harf: amaldagi → yangi")
check(all(to_old(n_l) == o_l for _, n_l, _, o_l in ALPHABET), "28 harf: yangi → amaldagi")

rows = alphabet_rows()
check(len(rows) == 28 and rows[6][1] == "Ğ ğ" and rows[6][2] == f"G{OKINA} g{OKINA}", "jadval qatori 7")
check(rows[25][1] == "Ö ö" and rows[26][1] == "Ç ç" and rows[27][1] == "Ş ş", "jadval 26-28")
tbl = alphabet_table()
check(tbl.count("\n") + 1 == 33 and "tutuq belgisi" in tbl and "alifbodan" in tbl, "jadval matni")

# ------------------------------------------------ misollar va aylanma
ALLOWED = set(lower) | set(a[0] for a in ALPHABET) | {TUTUQ}
for title, pairs in example_pairs():
    for old, new in pairs:
        back = to_old(new)
        if back != old:
            check(False, f"aylanma: {old} → {new} → {back}")
        strange = {c for c in new if c.isalpha() and c not in ALLOWED}
        if strange:
            check(False, f"«{new}» da alifboga kirmagan harf", strange)
check(all(to_old(n) == o for _, prs in example_pairs() for o, n in prs),
      "barça misollar aylanmadan ötdi")
check(all(c in ALLOWED for _, prs in example_pairs() for _, n in prs
          for c in n if c.isalpha()), "misollarda faqat alifbo harflari")

# ------------------------------------------------------ ng saqlanadi
for w, want in (("ko" + OKINA + "ngil", "köngil"), ("tong", "tong"),
                ("dengiz", "dengiz"), ("singlim", "singlim")):
    check(to_new(w) == want, f"ng saqlandi: {w}", to_new(w))
check(to_cyrillic("köngil") == "кўнгил", "ng kirillda", to_cyrillic("köngil"))
check(to_new("кўнгил") == "köngil", "ng kirilldan", to_new("кўнгил"))

# ------------------------------------------ eskirgan belgi çiqmasligi
corpus = [
    "Oʻzbekiston Respublikasi maʼnaviyat vazirligi",
    "ma'lum, san'at, ta'lim, e'lon, mo''jiza",
    "Ўзбекистон Республикаси маънавият вазирлиги",
    "Özbekiston Respublikasi ma’naviyat vazirligi",
    "SHAHAR, CHOY, O'ZBEK, G'ALABA",
]
for src in corpus:
    for fn, name in ((to_new, "to_new"), (to_old, "to_old")):
        out = fn(src)
        if LEGACY_TUTUQ in out:
            check(False, f"{name} eskirgan ʼ (U+02BC) qaytardi", repr(out))
check(all(LEGACY_TUTUQ not in fn(s) for s in corpus for fn in (to_new, to_old)),
      "hеç qayerda U+02BC çiqmadi")
check(all(OKINA not in to_new(s) for s in corpus), "yangi alifboda ʻ (U+02BB) qolmadi")
check(to_old("Özbekiston") == f"O{OKINA}zbekiston", "amaldagi alifboda ʻ ișlatiladi")
check(to_new("ma" + LEGACY_TUTUQ + "no") == "ma" + TUTUQ + "no", "eskirgan ʼ kiritilsa ham töğrilanadi")

# ------------------------------------------- tutuq belgisi kirillda
check(to_cyrillic("ma’no") == "маъно", "tutuq → ъ", to_cyrillic("ma’no"))
check(to_cyrillic("ma" + LEGACY_TUTUQ + "no") == "маъно", "eskirgan tutuq → ъ")
check(to_new("маъно") == "ma’no", "ъ → tutuq", to_new("маъно"))

print("\n" + ("BARÇASI OʻTDI" if not fails else f"{fails} ta test yiqildi"))
raise SystemExit(1 if fails else 0)
