import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from yozuv import Script, Target, convert, detect, options_from, to_cyrillic, to_new, to_old  # noqa: E402

OK = "ʻ"  # ʻ
TU = "’"  # ’


def check(got, want, label):
    status = "OK " if got == want else "XATO"
    if got != want:
        check.failed += 1
    print(f"[{status}] {label}\n        kutildi: {want!r}\n        natija : {got!r}" if got != want
          else f"[{status}] {label}: {got!r}")


check.failed = 0

# ---- eski → yangi -------------------------------------------------------
check(to_new("O'zbek tilida so'zlashamiz"), "Özbek tilida sözlaşamiz", "eski→yangi asosiy")
check(to_new("to'g'ri"), "töğri", "to'g'ri")
check(to_new("Toshkent shahri, barcha uchun"), "Toşkent şahri, barça uçun", "sh/ch")
check(to_new("O'ZBEKISTON RESPUBLIKASI"), "ÖZBEKISTON RESPUBLIKASI", "katta harf")
check(to_new("SHAHAR va CHOY"), "ŞAHAR va ÇOY", "SH/CH katta")
check(to_new("Shahar, Choy"), "Şahar, Çoy", "Sh/Ch bosh harf")
check(to_new("ma'lum va san'at"), f"ma{TU}lum va san{TU}at", "tutuq belgisi")
check(to_new("o‘quvchi, g’isht, o`zi"), "öquvçi, ğişt, özi", "har xil apostroflar")
check(to_new("mashhur tashhis"), "maşhur taşhis", "shh ketma-ketligi")
check(to_new("o'quvchilar"), "öquvçilar", "qöşma")

# ---- yangi → eski -------------------------------------------------------
check(to_old("Özbek tilida sözlaşamiz"), "O'zbek tilida so'zlashamiz".replace("'", OK), "yangi→eski")
check(to_old("ŞAHAR"), "SHAHAR", "Ş all-caps")
check(to_old("Şahar"), "Shahar", "Ş bosh harf")
check(to_old("töğri"), f"to{OK}g{OK}ri", "töğri→toʻgʻri")

# ---- kirill -------------------------------------------------------------
check(to_new("Ўзбекистон Республикаси"), "Özbekiston Respublikasi", "kirill→yangi")
check(to_new("Тошкент шаҳри, барча учун"), "Toşkent şahri, barça uçun", "kirill sh/ch")
check(to_new("Ер юзида ёмғир ёғди"), "Yer yuzida yomğir yoğdi", "е/ё/ю")
check(to_new("объект"), "obyekt", "ъ+е")
check(to_new("конституция"), "konstitutsiya", "ц→ts")
check(to_new("цирк"), "sirk", "ц→s")
check(to_old("Ўзбекистон"), f"O{OK}zbekiston", "kirill→eski")

# ---- lotin → kirill -----------------------------------------------------
check(to_cyrillic("O'zbekiston Respublikasi"), "Ўзбекистон Республикаси", "eski→kirill")
check(to_cyrillic("Özbekiston"), "Ўзбекистон", "yangi→kirill")
check(to_cyrillic("Toshkent shahri"), "Тошкент шаҳри", "sh/h→ш/ҳ")
check(to_cyrillic("yangi yozuv"), "янги ёзув", "ya/yo")
check(to_cyrillic("eshik"), "эшик", "söz boşida e→э")
check(to_cyrillic("keldi"), "келди", "söz içida e→е")
check(to_cyrillic("ketsa"), "кетса", "ts yolğon ijobiy emas")
check(to_cyrillic("tayyor"), "тайёр", "tayyor")

# ---- aqlli himoya -------------------------------------------------------
check(to_new("Havola: https://t.me/share va @YozuvBot"),
      "Havola: https://t.me/share va @YozuvBot", "havola/@username saqlandi")
check(to_new("Pochta: ochil@mail.uz keldi"), "Poçta: ochil@mail.uz keldi", "e-poçta saqlandi")
check(to_new("#toshkent tashkilot"), "#toshkent taşkilot", "hashtag saqlandi")
check(to_new("Chelsea klubi choy ichdi"), "Chelsea klubi çoy içdi", "xorijiy söz saqlandi")
check(to_new("Chelsea klubi", options_from(keep_foreign=False)), "Çelsea klubi", "keep_foreign=False")
check(to_new("`code sh` sharh"), "`code sh` şarh", "kod bloki saqlandi")

# ---- aniqlaş va avto ----------------------------------------------------
check(detect("Ўзбекистон"), Script.CYRILLIC, "detect kirill")
check(detect("Özbekiston"), Script.NEW_LATIN, "detect yangi")
check(detect("O'zbekiston"), Script.OLD_LATIN, "detect eski")
check(convert("Özbek", Target.AUTO).text, f"O{OK}zbek", "avto: yangi→eski")
check(convert("O'zbek", Target.AUTO).text, "Özbek", "avto: eski→yangi")

# ---- idempotentlik ------------------------------------------------------
once = to_new("O'zbekiston shahri")
check(to_new(once), once, "ikki marta ötkazsa ösmaydi")

print("\n" + ("BARÇASI OʻTDI" if not check.failed else f"{check.failed} ta test yiqildi"))
raise SystemExit(1 if check.failed else 0)
