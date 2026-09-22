"""Interfeys matnlari.

Barcha matnlar ESKI lotin alifbosida yoziladi va foydalanuvchining
tanlagan yozuviga `render()` orqali avtomatik o'giriladi. Shu sababli
interfeys uchun uchta alohida tarjima fayli saqlanmaydi.
"""
from __future__ import annotations

import re

from yozuv import Target, convert, options_from

_UI_OPTS = options_from(protect_commands=True, protect_hashtags=True)

#: [[raw]]...[[/raw]] orasidagi matn hech qachon o'girilmaydi
_RAW = re.compile(r"\[\[raw\]\](.*?)\[\[/raw\]\]", re.S)


#: konvertor hеç qaçon tegmaydigan belgilar (Unicode private use area)
_MARK = "\ue000%d\ue001"


def render(text: str, ui: str = "yangi") -> str:
    """Interfeys matnini foydalanuvchi tanlagan yozuvga o'tkazadi.

    «eski» rejimda ham konvertordan o'tkaziladi — shunda ASCII apostrof
    kanonik `ʻ` / `’` ko'rinishiga keladi.
    """
    keep: list[str] = []

    def _stash(m: re.Match[str]) -> str:
        keep.append(m.group(1))
        return _MARK % (len(keep) - 1)

    text = _RAW.sub(_stash, text)
    text = convert(text, Target(ui), _UI_OPTS).text
    for i, chunk in enumerate(keep):
        text = text.replace(_MARK % i, chunk)
    return text


T = {
    "start": (
        "👋 <b>Assalomu alaykum, {name}!</b>\n\n"
        "Men matnlaringizni <b>eski lotin</b>, <b>yangi lotin</b> va <b>kirill</b> "
        "yozuvlari orasida o'tkazaman.\n\n"
        "<b>O'zgarishlar:</b>\n"
        "[[raw]]<code>oʻ → ö</code>   <code>gʻ → ğ</code>\n"
        "<code>sh → ş</code>   <code>ch → ç</code>[[/raw]]\n"
        "[[raw]]<code>ng</code>[[/raw]] alifbodan chiqdi, so'zlarda saqlanadi.\n\n"
        "✍️ Shunchaki matn yuboring — men uni o'giraman.\n"
        "📎 Fayl [[raw]](.txt, .docx, .srt)[[/raw]] ham yuborishingiz mumkin.\n"
        "🔎 Istalgan chatda [[raw]]<code>@{bot} matn</code>[[/raw]] deb yozib ham ishlatsangiz bo'ladi.\n\n"
        "⚙️ Sozlamalar uchun /sozlama, yordam uchun /yordam."
    ),
    "help": (
        "<b>📖 Yo'riqnoma</b>\n\n"
        "<b>Buyruqlar</b>\n"
        "/start — botni qayta ishga tushirish\n"
        "/yangi — matnni yangi alifboga o'tkazish rejimi\n"
        "/eski — matnni eski alifboga o'tkazish rejimi\n"
        "/kirill — matnni kirillga o'tkazish rejimi\n"
        "/avto — manbaga qarab avtomatik tanlash\n"
        "/alifbo — rasmiy alifbo jadvali (28 harf)\n"
        "/misol — so'zlar yangi alifboda qanday yoziladi\n"
        "/sozlama — sozlamalar\n"
        "/mening — shaxsiy statistikangiz\n"
        "/obuna — bot yangiliklariga obuna bo'lish yoki bekor qilish\n"
        "/yordam — shu yo'riqnoma\n\n"
        "<b>Guruh va kanallarda</b>\n"
        "/yoz — xabarga javob qilib yozsangiz, o'sha matn o'giriladi\n"
        "/avtokanal — kanal postlarini avtomatik o'girish (admin uchun)\n\n"
        "<b>Aqlli himoya</b>\n"
        "Havolalar, e-pochta manzillari, @username, #hashtag va kod bo'laklari "
        "o'zgarishsiz qoladi. Xalqaro brend nomlari ham saqlanadi.\n\n"
        "<b>Fayllar</b>\n"
        "Matnli fayl yuboring — o'girilgan nusxasini qaytaraman "
        "[[raw]](.txt, .md, .csv, .srt, .docx)[[/raw]]."
    ),
    "about": (
        "<b>ℹ️ Bot haqida</b>\n\n"
        "Bu bot o'zbek alifbosidagi yangilanishga moslashish uchun yaratilgan.\n"
        "Matnni uchta yozuv orasida o'tkazadi, imlo qoidalarini hisobga oladi:\n"
        "• [[raw]]«е», «ц», «ъ»[[/raw]] kabi kirill harflari qoida bo'yicha o'giriladi\n"
        "• bosh harf va bosh-harfli so'zlar to'g'ri saqlanadi\n"
        "• tutuq belgisi [[raw]](’)[[/raw]] va qo'shimcha belgi [[raw]](ʻ)[[/raw]] farqlanadi\n\n"
        "Versiya: [[raw]]<code>{ver}</code>[[/raw]]"
    ),
    "settings": (
        "<b>⚙️ Sozlamalar</b>\n\n"
        "Joriy rejim: <b>{mode}</b>\n"
        "Interfeys yozuvi: <b>{ui}</b>\n"
        "Aqlli himoya: <b>{smart}</b>\n"
        "Xalqaro so'zlar: <b>{foreign}</b>\n"
        "Natija ko'rinishi: <b>{fmt}</b>"
    ),
    "alphabet_note": (
        "Yangi alifboda <b>{size} ta harf</b> va 1 ta tutuq belgisi bor.\n"
        "Qo'shma harflar ({old}) o'rniga yaxlit {new} joriy etildi.\n"
        "«{ng}» alifbodan chiqarildi, ammo so'zlar ichida "
        "({ng_misol}) saqlanaveradi."
    ),
    "mode_set": "✅ Rejim o'zgartirildi: <b>{mode}</b>",
    "empty": "✍️ Menga matn yuboring.",
    "too_long": "⚠️ Matn juda uzun. Iltimos, fayl ko'rinishida yuboring.",
    "nothing_changed": "ℹ️ Matn allaqachon tanlangan yozuvda ekan.",
    "file_big": "⚠️ Fayl hajmi {mb} MB dan oshmasligi kerak.",
    "file_bad": ("⚠️ Bu turdagi faylni o'qiy olmayman.\n"
                 "Qo'llab-quvvatlanadi: [[raw]].txt, .md, .csv, .srt, .docx[[/raw]]"),
    "file_done": "✅ Tayyor. Belgilar soni: <b>{chars}</b>",
    "file_wait": "⏳ Fayl o'girilmoqda...",
    "reply_needed": "↩️ Biror xabarga javob qilib /yoz deb yozing.",
    "my_stats": (
        "<b>📊 Sizning statistikangiz</b>\n\n"
        "O'girishlar: <b>{conv}</b>\n"
        "Belgilar: <b>{chars}</b>\n"
        "Qo'shilgan sana: <b>{joined}</b>"
    ),
    "admin_stats": (
        "<b>📈 Umumiy statistika</b>\n\n"
        "👥 Foydalanuvchilar: <b>{users}</b>\n"
        "📬 Xabar olishi mumkin: <b>{subs}</b>\n"
        "🚫 Bloklaganlar: <b>{blocked}</b>\n"
        "🟢 Bugun faol: <b>{today}</b>\n"
        "📅 Haftalik faol: <b>{week}</b>\n"
        "💬 Guruh va kanallar: <b>{chats}</b>\n\n"
        "🔁 Jami o'girishlar: <b>{conv}</b>\n"
        "🔤 Jami belgilar: <b>{chars}</b>"
    ),
    "bc_pick": (
        "<b>📣 Tarqatma #{id}</b>\n\n"
        "Xabar tayyor. Endi kimga yuborishni tanlang:"
    ),
    "bc_confirm": (
        "<b>📣 Tarqatma #{id}</b>\n\n"
        "Auditoriya: <b>{audience}</b>\n"
        "Manzillar soni: <b>{total}</b>\n\n"
        "Yuborilsinmi?"
    ),
    "bc_empty": "⚠️ Bu auditoriyada bironta ham manzil yo'q.",
    "bc_progress": (
        "<b>📣 Tarqatma #{id}</b> — {status}\n\n"
        "✅ Yuborildi: <b>{sent}</b>\n"
        "🚫 Bloklagan: <b>{blocked}</b>\n"
        "⚠️ Xato: <b>{failed}</b>\n"
        "📊 Jami: <b>{done}</b> / <b>{total}</b>"
    ),
    "bc_started": "🚀 Tarqatma boshlandi. To'xtatish uchun: /toxtat {id}",
    "bc_cancelled": "🛑 Tarqatma #{id} to'xtatildi.",
    "bc_not_running": "ℹ️ Tarqatma #{id} ishlamayapti.",
    "bc_list_empty": "📭 Hali tarqatma bo'lmagan.",
    "bc_list_head": "<b>📣 So'nggi tarqatmalar</b>",
    "bc_row": "#{id} · {status} · {sent}/{total} · {when}",
    "dm_usage": (
        "✍️ <b>Bitta manzilga xabar</b>\n\n"
        "<code>/yubor 123456789 salom</code> — foydalanuvchiga\n"
        "<code>/yubor @username salom</code> — foydalanuvchiga\n"
        "<code>/yubor -1001234567890 salom</code> — guruh yoki kanalga\n"
        "<code>/yubor @kanalim salom</code> — ochiq kanalga\n\n"
        "Xabarga javob qilib <code>/yubor &lt;manzil&gt;</code> deb ham yozsangiz bo'ladi.\n"
        "Guruh ID larini /guruhlar ko'rsatadi."
    ),
    "dm_no_user": "⚠️ Bunday manzil topilmadi: <code>{key}</code>",
    "chats_empty": (
        "📭 Hali bironta guruh yoki kanal yo'q.\n"
        "Botni guruhga qo'shsangiz, o'zi ro'yxatga tushadi."
    ),
    "chats_head": "<b>💬 Guruh va kanallar ({n})</b>",
    "chats_row": "{auto} {title} — <code>{id}</code> · {kind}",
    "dm_ok": "✅ Yuborildi: <b>{who}</b>",
    "dm_fail": "⚠️ Yuborilmadi: {why}",
    "who_usage": "✍️ Foydalanish: <code>/kim &lt;id yoki @username&gt;</code>",
    "who_card": (
        "<b>👤 {name}</b>\n"
        "ID: <code>{id}</code>\n"
        "Username: {username}\n"
        "Rejim: <b>{mode}</b> · Interfeys: <b>{ui}</b>\n"
        "Obuna: <b>{subscribed}</b> · Bloklagan: <b>{blocked}</b>\n"
        "O'girishlar: <b>{conv}</b> · Belgilar: <b>{chars}</b>\n"
        "Qo'shilgan: {created} · Oxirgi faollik: {seen}"
    ),
    "sub_on": "🔔 Endi bot yangiliklaridan xabardor bo'lasiz.",
    "sub_off": "🔕 Endi sizga tarqatma xabarlari kelmaydi.",
    "mode_set": "✅ Rejim o'zgartirildi: <b>{mode}</b>",
    "not_admin": "⛔️ Bu buyruq faqat adminlar uchun.",
    "bc_usage": (
        "📣 Tarqatiladigan xabarga <b>javob qilib</b> /xabar deb yozing.\n"
        "Xabar qanday bo'lsa, shundayligicha (rasm, video, tugmalar bilan) "
        "yuboriladi."
    ),
    "auto_on": "✅ Bu chatda avtomatik o'girish yoqildi.",
    "auto_off": "🚫 Bu chatda avtomatik o'girish o'chirildi.",
    "ocr_off": ("🖼 Rasmdan matn o'qish yoqilmagan. "
                "[[raw]]README[[/raw]] dagi [[raw]]OCR[[/raw]] bo'limiga qarang."),
    "ocr_fail": "🖼 Rasmdan matn topilmadi.",
    "throttled": "⏱ Sekinroq, iltimos.",
}

BTN = {
    "yangi": "🆕 Yangi alifbo",
    "eski": "🔙 Eski alifbo",
    "kirill": "🇺🇿 Kirill",
    "avto": "🔁 Avto",
    "orig": "♻️ Asl matn",
    "code": "📋 Nusxalash uchun",
    "settings": "⚙️ Sozlamalar",
    "help": "❓ Yordam",
    "back": "⬅️ Orqaga",
    "smart": "🛡 Aqlli himoya: {v}",
    "foreign": "🌍 Xalqaro so'zlar: {v}",
    "fmt": "📐 Ko'rinish: {v}",
    "ui": "🔤 Interfeys: {v}",
    "mode": "🎯 Rejim: {v}",
    "on": "yoqilgan",
    "off": "o'chirilgan",
    "plain": "oddiy",
    "codefmt": "nusxalanadigan",
}

AUDIENCE_NAME = {
    "barça": "👥 Hamma",
    "faol": "🟢 Faol (30 kun)",
    "yangi_ui": "🆕 Yangi alifbo",
    "eski_ui": "🔙 Eski alifbo",
    "kirill_ui": "🇺🇿 Kirill",
    "guruhlar": "💬 Guruh va kanallar",
    "tanlangan": "🎯 Tanlangan",
}

MODE_NAME = {
    "yangi": "yangi alifbo",
    "eski": "eski alifbo",
    "kirill": "kirill",
    "avto": "avto",
}


def t(key: str, ui: str = "yangi", /, **kwargs) -> str:
    return render(T[key], ui).format(**kwargs)


def b(key: str, ui: str = "yangi", /, **kwargs) -> str:
    return render(BTN[key], ui).format(**kwargs)
