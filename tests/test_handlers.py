"""Uçidan-uçiga test: soxta Telegram sessiyasi bilan haqiqiy handlerlar."""
from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.update(BOT_TOKEN="123456:TEST", ADMINS="777", THROTTLE="0", LOG_LEVEL="WARNING")

from aiogram import Bot, Dispatcher  # noqa: E402
from aiogram.client.default import DefaultBotProperties  # noqa: E402
from aiogram.client.session.base import BaseSession  # noqa: E402
from aiogram.enums import ParseMode  # noqa: E402
from aiogram.methods import TelegramMethod  # noqa: E402
from aiogram.types import (  # noqa: E402
    CallbackQuery, Chat, ChatMemberBanned, ChatMemberLeft, ChatMemberMember,
    ChatMemberUpdated, Document, InlineQuery, Message, MessageId, Update,
    User as TgUser,
)

from bot import broadcast as bc_engine  # noqa: E402
from bot import db  # noqa: E402
from bot.handlers import build_router  # noqa: E402
from bot.middlewares import UserMiddleware  # noqa: E402

fails = 0
ME = TgUser(id=42, is_bot=True, first_name="Yozuv", username="YozuvBot")
CHAT = Chat(id=777, type="private")
ALI = TgUser(id=777, is_bot=False, first_name="Ali", username="ali")


def check(cond, label, extra=""):
    global fails
    if not cond:
        fails += 1
    print(f"[{'OK ' if cond else 'XATO'}] {label}{(' — ' + str(extra)) if not cond else ''}")


class FakeSession(BaseSession):
    """Telegram API ni taqlid qiladi: har bir çaqiruvni yozib boradi."""

    def __init__(self) -> None:
        super().__init__()
        self.calls: list[TelegramMethod] = []
        self._mid = 100

    async def close(self) -> None:
        pass

    async def stream_content(self, *a, **kw):  # pragma: no cover
        yield b""

    def _message(self, method) -> Message:
        self._mid += 1
        return Message(
            message_id=self._mid,
            date=datetime.now(timezone.utc),
            chat=CHAT,
            from_user=ME,
            text=getattr(method, "text", None) or getattr(method, "caption", None) or "",
        ).as_(self.bot)

    async def make_request(self, bot, method, timeout=None):
        self.bot = bot
        self.calls.append(method)
        name = type(method).__name__
        if name == "GetMe":
            return ME
        if name == "CopyMessage":
            self._mid += 1
            return MessageId(message_id=self._mid)
        if name in ("SendMessage", "EditMessageText", "SendDocument"):
            return self._message(method)
        return True

    # --- qulaylik uçun ---
    def sent(self) -> list[str]:
        return [m.text for m in self.calls if type(m).__name__ == "SendMessage"]

    def edits(self) -> list[str]:
        return [m.text for m in self.calls if type(m).__name__ == "EditMessageText"]

    def last_kb(self):
        for m in reversed(self.calls):
            kb = getattr(m, "reply_markup", None)
            if kb is not None and getattr(kb, "inline_keyboard", None):
                return kb
        return None

    def clear(self) -> None:
        self.calls.clear()


def msg(text: str, mid: int = 1, chat: Chat = CHAT, user: TgUser = ALI) -> Update:
    return Update(update_id=mid, message=Message(
        message_id=mid, date=datetime.now(timezone.utc), chat=chat,
        from_user=user, text=text))


async def main() -> None:
    tmp = Path(tempfile.mkdtemp()) / "t.sqlite3"
    await db.init(tmp)

    session = FakeSession()
    bot = Bot(token="123456:TEST", session=session,
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.update.outer_middleware(UserMiddleware())
    dp.include_router(build_router())
    caster = bc_engine.setup(bot, rate=500)

    async def feed(update: Update):
        session.clear()
        await dp.feed_update(bot, update)
        return session

    # ---------------------------------------------------------- /start
    s = await feed(msg("/start"))
    out = s.sent()
    check(out and "Assalomu alaykum" in out[0], "/start salomlaşdi", out[:1])
    check(any("YozuvBot" in x for x in out), "/start bot nomini körsatdi")

    # ---------------------------------------------- oddiy matn o'girish
    s = await feed(msg("O'zbekiston Respublikasi shahri", 2))
    out = s.sent()
    check(out and out[0] == "Özbekiston Respublikasi şahri", "matn ötkazildi", out)
    kb = s.last_kb()
    check(kb is not None and len(kb.inline_keyboard[0]) == 2, "natija tugmalari bor")

    # ------------------------------------------------- tugma bilan qayta
    cb_data = kb.inline_keyboard[0][0].callback_data
    base = Message(message_id=101, date=datetime.now(timezone.utc), chat=CHAT,
                   from_user=ME, text="Özbekiston Respublikasi şahri")
    s = await feed(Update(update_id=3, callback_query=CallbackQuery(
        id="cb1", from_user=ALI, chat_instance="x", message=base, data=cb_data)))
    check(s.edits() and "Oʻzbekiston" in s.edits()[0], "tugma: eski alifboga ötdi", s.edits())

    s = await feed(Update(update_id=4, callback_query=CallbackQuery(
        id="cb2", from_user=ALI, chat_instance="x", message=base,
        data=cb_data.rsplit("|", 2)[0] + "|k|p")))
    check(s.edits() and "Ўзбекистон" in s.edits()[0], "tugma: kirillga ötdi", s.edits())

    s = await feed(Update(update_id=5, callback_query=CallbackQuery(
        id="cb3", from_user=ALI, chat_instance="x", message=base,
        data=cb_data.rsplit("|", 2)[0] + "|a|p")))
    check(s.edits() and s.edits()[0] == "O'zbekiston Respublikasi shahri", "tugma: asl matn", s.edits())

    s = await feed(Update(update_id=6, callback_query=CallbackQuery(
        id="cb4", from_user=ALI, chat_instance="x", message=base,
        data=cb_data.rsplit("|", 2)[0] + "|y|c")))
    check(s.edits() and s.edits()[0].startswith("<code>"), "tugma: nusxalaş körinişi", s.edits())

    # ------------------------------------------------------- rejimlar
    s = await feed(msg("/kirill Toshkent shahri", 7))
    out = s.sent()
    check(any("Тошкент шаҳри" in x for x in out), "/kirill argument bilan", out)
    u = await db.get_user(777)
    check(u.mode == "kirill", "rejim saqlandi")

    s = await feed(msg("/yangi", 8))
    check((await db.get_user(777)).mode == "yangi", "/yangi rejimga qaytdi")

    # --------------------------------------------------- pastki tugmalar
    s = await feed(msg("🇺🇿 Kirill", 9))
    check((await db.get_user(777)).mode == "kirill", "klaviatura tugmasi rejimni almaştirdi")
    await db.set_field(777, "mode", "yangi")

    # -------------------------------------------- alifbo va misollar
    s = await feed(msg("/alifbo", 91))
    out = s.sent()
    check(out and "<pre>" in out[0] and "28  Ş ş" in out[0] and "tutuq belgisi" in out[0],
          "/alifbo jadvali", out[:1])
    check(out and "Gʻ gʻ" in out[0] and "Oʻ oʻ" in out[0], "/alifbo amaldagi ustuni")
    check(out and "ng" in out[0] and "alifbodan" in out[0], "/alifbo ng izohi")

    s = await feed(msg("/misol", 92))
    out = s.sent()
    check(out and "Oʻzbekiston → Özbekiston" in out[0], "/misol Oʻ→Ö", out[:1])
    check(out and "yomgʻir → yomğir" in out[0], "/misol Gʻ→Ğ")
    check(out and "koʻngil → köngil" in out[0], "/misol ng saqlanadi")

    # tutuq belgisi rasmiy U+2019 bo'lsin
    s = await feed(msg("ma'no va san'at", 93))
    check(s.sent() and s.sent()[0] == "ma\u2019no va san\u2019at", "tutuq belgisi U+2019", s.sent())

    # ------------------------------------------------------- sozlamalar
    s = await feed(msg("/sozlama", 10))
    kb = s.last_kb()
    check(kb is not None and len(kb.inline_keyboard) == 5, "sozlama menyusi")
    s = await feed(Update(update_id=11, callback_query=CallbackQuery(
        id="cb5", from_user=ALI, chat_instance="x", message=base, data="st|smart|toggle")))
    check((await db.get_user(777)).smart == 0, "aqlli himoya öçirildi")
    s = await feed(Update(update_id=12, callback_query=CallbackQuery(
        id="cb6", from_user=ALI, chat_instance="x", message=base, data="st|ui|next")))
    check((await db.get_user(777)).ui == "eski", "interfeys yozuvi almaşdi")
    await db.set_field(777, "ui", "yangi")
    await db.set_field(777, "smart", 1)

    # ------------------------------------------------------------ inline
    s = await feed(Update(update_id=13, inline_query=InlineQuery(
        id="iq1", from_user=ALI, query="Toshkent shahri", offset="")))
    ans = [m for m in s.calls if type(m).__name__ == "AnswerInlineQuery"]
    check(ans and len(ans[0].results) == 3, "inline: uçta natija", len(ans[0].results) if ans else 0)
    texts = [r.input_message_content.message_text for r in ans[0].results]
    check("Toşkent şahri" in texts and "Тошкент шаҳри" in texts, "inline natijalari töğri", texts)

    s = await feed(Update(update_id=131, inline_query=InlineQuery(
        id="iq2", from_user=ALI, query="", offset="")))
    ans = [m for m in s.calls if type(m).__name__ == "AnswerInlineQuery"]
    check(ans and ans[0].button is not None and not ans[0].results,
          "inline: böş söro'vda tugma körsatildi")

    # --------------------------------------------------- nomaʼlum fayl
    doc = Document(file_id="f1", file_unique_id="u1", file_name="rasm.pdf", file_size=1024)
    s = await feed(Update(update_id=132, message=Message(
        message_id=40, date=datetime.now(timezone.utc), chat=CHAT, from_user=ALI,
        document=doc)))
    check(any("qöllab" in x.lower() or "o'qiy olmayman" in x or "öqiy olmayman" in x
              for x in s.sent()), "nomaʼlum fayl turi rad etildi", s.sent())

    big = Document(file_id="f2", file_unique_id="u2", file_name="katta.txt",
                   file_size=99 * 1024 * 1024)
    s = await feed(Update(update_id=133, message=Message(
        message_id=41, date=datetime.now(timezone.utc), chat=CHAT, from_user=ALI,
        document=big)))
    check(any("MB" in x for x in s.sent()), "katta fayl rad etildi", s.sent())

    # -------------------------------------------------------- statistika
    s = await feed(msg("/mening", 14))
    check(any("statistika" in x.lower() for x in s.sent()), "/mening", s.sent())
    s = await feed(msg("/stat", 15))
    check(any("Foydalanuvçilar" in x for x in s.sent()), "/stat (admin)", s.sent())

    # ------------------------------------------------ admin bo'lmaganda
    bek = TgUser(id=888, is_bot=False, first_name="Bek")
    s = await feed(Update(update_id=16, message=Message(
        message_id=16, date=datetime.now(timezone.utc),
        chat=Chat(id=888, type="private"), from_user=bek, text="/stat")))
    check(not any("Foydalanuvçilar" in x for x in s.sent()), "/stat oddiy foydalanuvçiga yopiq", s.sent())

    # ------------------------------------------------------------ guruh
    grp = Chat(id=-1001, type="supergroup", title="Test guruh")
    reply = Message(message_id=20, date=datetime.now(timezone.utc), chat=grp,
                    from_user=ALI, text="Bugun havo juda yaxshi, choy ichamiz")
    s = await feed(Update(update_id=17, message=Message(
        message_id=21, date=datetime.now(timezone.utc), chat=grp, from_user=ALI,
        text="/yoz", reply_to_message=reply)))
    check(any("yaxşi, çoy içamiz" in x for x in s.sent()), "guruhda /yoz", s.sent())

    # guruhda oddiy matn — avto o'çiq bo'lsa javob bermaydi
    s = await feed(Update(update_id=18, message=Message(
        message_id=22, date=datetime.now(timezone.utc), chat=grp, from_user=ALI,
        text="oddiy xabar shu yerda")))
    check(not s.sent(), "guruhda avto öçiq — javob yöq", s.sent())

    await db.set_chat_auto(grp.id, True, "yangi")
    s = await feed(Update(update_id=19, message=Message(
        message_id=23, date=datetime.now(timezone.utc), chat=grp, from_user=ALI,
        text="oddiy xabar shu yerda")))
    check(any("şu" in x for x in s.sent()), "guruhda avto yoqilgan", s.sent())

    # --------------------------------------------------------- uzun matn
    long_text = "Toshkent shahri juda go'zal. " * 200
    s = await feed(msg(long_text, 24))
    check(len(s.sent()) >= 2, "uzun matn bölaklarga ajratildi", len(s.sent()))
    check(all(len(x) <= 4096 for x in s.sent()), "har bir bölak çegaradan oşmadi")

    # ------------------------------------------------- havola tegilmaydi
    s = await feed(msg("Batafsil: https://example.uz/shop va @YozuvBot orqali choy", 25))
    check(s.sent() and "https://example.uz/shop" in s.sent()[0] and "@YozuvBot" in s.sent()[0]
          and "çoy" in s.sent()[0], "havola va username saqlandi", s.sent())

    # ------------------------------------------------ tahrirlangan xabar
    s = await feed(Update(update_id=26, edited_message=Message(
        message_id=2, date=datetime.now(timezone.utc), chat=CHAT, from_user=ALI,
        text="yangilangan choy")))
    check(any("çoy" in x for x in s.sent()), "tahrirlangan xabar ötkazildi", s.sent())

    # ==================================================== tarqatma va adminlik
    for uid, name in ((901, "Anvar"), (902, "Bobur"), (903, "Dilnoza")):
        await db.get_user(uid, f"user{uid}", name)

    s = await feed(msg("/obuna", 60))
    check(any("tarqatma" in x for x in s.sent()), "/obuna öçirdi", s.sent())
    check((await db.get_user(777)).subscribed is False, "obuna bazada öçdi")
    s = await feed(msg("/obuna", 61))
    check((await db.get_user(777)).subscribed is True, "/obuna qayta yoqdi")

    s = await feed(msg("/kim @user901", 62))
    check(any("Anvar" in x for x in s.sent()), "/kim topdi", s.sent())
    s = await feed(msg("/kim @yoq_bunday", 63))
    check(any("topilmadi" in x for x in s.sent()), "/kim topmadi", s.sent())

    s = await feed(msg("/yubor 901 Assalomu alaykum", 64))
    check(any("Yuborildi" in x for x in s.sent()), "/yubor işladi", s.sent())
    sent_to = [m.chat_id for m in s.calls if type(m).__name__ == "SendMessage"]
    check(901 in sent_to, "/yubor töğri manzilga ketdi", sent_to)
    s = await feed(msg("/yubor", 65))
    check(any("Bitta manzilga xabar" in x for x in s.sent()), "/yubor yöriqnoma", s.sent())

    # ---------------------------------------------- guruhga alohida xabar
    s = await feed(msg("/guruhlar", 80))
    check(any("-1001" in x for x in s.sent()), "/guruhlar mavjud guruhni körsatdi", s.sent())

    # bot guruhga qöşildi — hеç kim buyruq yozmasdan röyxatga tuşişi kerak
    yangi = Chat(id=-1002222, type="supergroup", title="Yangi guruh")
    s = await feed(Update(update_id=81, my_chat_member=ChatMemberUpdated(
        chat=yangi, from_user=ALI, date=datetime.now(timezone.utc),
        old_chat_member=ChatMemberLeft(user=ME),
        new_chat_member=ChatMemberMember(user=ME))))
    check(-1002222 in [c.chat_id for c in await db.list_chats()],
          "bot qöşilganda guruh özi röyxatga tuşdi",
          [c.chat_id for c in await db.list_chats()])

    s = await feed(msg("/guruhlar", 82))
    check(any("Yangi guruh" in x and "-1002222" in x for x in s.sent()),
          "/guruhlar guruhni va ID sini körsatdi", s.sent())

    s = await feed(msg("/yubor -1002222 Guruhga salom", 83))
    check(any("Yuborildi" in x for x in s.sent()), "/yubor guruhga işladi", s.sent())
    to_group = [m.chat_id for m in s.calls if type(m).__name__ == "SendMessage"]
    check(-1002222 in to_group, "/yubor guruh ID siga ketdi", to_group)
    check(any("Yangi guruh" in x for x in s.sent()), "/yubor guruh nomini körsatdi", s.sent())

    # bazada yöq manfiy ID ham qabul qilinadi
    s = await feed(msg("/yubor -1009999 sinov", 84))
    to_group = [m.chat_id for m in s.calls if type(m).__name__ == "SendMessage"]
    check(-1009999 in to_group, "nomaʼlum guruh ID si ham yuboriladi", to_group)

    # bot guruhdan çiqarildi — auditoriyadan tuşib qolsin
    s = await feed(Update(update_id=85, my_chat_member=ChatMemberUpdated(
        chat=yangi, from_user=ALI, date=datetime.now(timezone.utc),
        old_chat_member=ChatMemberMember(user=ME),
        new_chat_member=ChatMemberLeft(user=ME))))
    left = await db.audience_ids("guruhlar")
    check(-1002222 not in left and -1001 in left,
          "çiqarilgan guruh auditoriyadan çiqdi, qolgani joyida", left)

    # foydalanuvçi botni bloklagani — şaxsiy çatdagi my_chat_member
    bek2 = TgUser(id=904, is_bot=False, first_name="Bek")
    await db.get_user(904, "bek904", "Bek")
    s = await feed(Update(update_id=86, my_chat_member=ChatMemberUpdated(
        chat=Chat(id=904, type="private"), from_user=bek2,
        date=datetime.now(timezone.utc),
        old_chat_member=ChatMemberMember(user=ME),
        new_chat_member=ChatMemberBanned(user=ME, until_date=0))))
    check((await db.find_user(904)).blocked is True,
          "botni bloklagan foydalanuvçi belgilandi")
    check(904 not in await db.audience_ids("barça"), "u tarqatmaga tuşmaydi")

    # --- tarqatma sehrgari ---
    s = await feed(msg("/xabar", 66))
    check(any("javob qilib" in x for x in s.sent()), "/xabar javobsiz yöriqnoma", s.sent())

    source = Message(message_id=70, date=datetime.now(timezone.utc), chat=CHAT,
                     from_user=ALI, text="Yangilik: bot yangilandi")
    s = await feed(Update(update_id=67, message=Message(
        message_id=71, date=datetime.now(timezone.utc), chat=CHAT, from_user=ALI,
        text="/xabar", reply_to_message=source)))
    kb = s.last_kb()
    check(kb is not None and any("Hamma" in b.text or "Ҳамма" in b.text
                                 for row in kb.inline_keyboard for b in row),
          "tarqatma: auditoriya tugmalari", [b.text for r in (kb.inline_keyboard if kb else []) for b in r])
    aud_btn = next(b for row in kb.inline_keyboard for b in row
                   if b.callback_data.startswith("bc|"))
    check("· 5" in aud_btn.text, "tarqatma: auditoriya soni körsatildi", aud_btn.text)
    bid = int(aud_btn.callback_data.split("|")[1])

    base2 = Message(message_id=72, date=datetime.now(timezone.utc), chat=CHAT,
                    from_user=ME, text="tanlang")
    s = await feed(Update(update_id=68, callback_query=CallbackQuery(
        id="bc1", from_user=ALI, chat_instance="x", message=base2,
        data=aud_btn.callback_data)))
    check(any("Yuborilsinmi" in x for x in s.edits()), "tarqatma: tasdiq sörovi", s.edits())
    row = await db.get_broadcast(bid)
    check(row.total == 5, "tarqatma: manzillar navbatga tuşdi", row.total)

    s = await feed(Update(update_id=69, callback_query=CallbackQuery(
        id="bc2", from_user=ALI, chat_instance="x", message=base2, data=f"bcgo|{bid}")))
    task = bc_engine.get()._tasks.get(bid)
    if task:
        await task
    row = await db.get_broadcast(bid)
    check(row.status == "tugadi" and row.sent == 5, "tarqatma yuborildi",
          (row.status, row.sent, row.total))
    copies = [m.chat_id for m in session.calls if type(m).__name__ == "CopyMessage"]
    check(sorted(copies) == [777, 888, 901, 902, 903], "tarqatma manzillari", copies)

    s = await feed(msg("/xabarlar", 73))
    check(any(f"#{bid}" in x for x in s.sent()), "/xabarlar röyxati", s.sent())
    s = await feed(msg(f"/toxtat {bid}", 74))
    check(any("işlamayapti" in x or "ishlamayapti" in x for x in s.sent()),
          "/toxtat tugagan tarqatma", s.sent())

    s = await feed(msg("/stat", 75))
    check(any("Xabar oliși mumkin" in x or "Xabar olişi mumkin" in x for x in s.sent()),
          "/stat kengaytirilgan", s.sent())

    await bot.session.close()
    await db.close()
    print("\n" + ("BARÇASI OʻTDI" if not fails else f"{fails} ta test yiqildi"))
    raise SystemExit(1 if fails else 0)


async def _run():
    try:
        await main()
    finally:
        await db.close()


try:
    asyncio.run(_run())
except SystemExit as exc:
    raise
