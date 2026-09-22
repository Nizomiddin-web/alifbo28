"""SQLAlchemy baza qatlamining testlari.

Standart holatda SQLite da işlaydi. MySQL da ham sinaş uçun:
    TEST_DATABASE_URL="mysql+aiomysql://user:pass@127.0.0.1/yozuvbot_test" \
        ./.venv/bin/python tests/test_db.py
"""
from __future__ import annotations

import asyncio
import datetime as dt
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bot import db  # noqa: E402
from bot.models import Audience, Base, BroadcastStatus, TargetStatus, utcnow  # noqa: E402

fails = 0


def eq(got, want, label):
    global fails
    ok = got == want
    if not ok:
        fails += 1
    print(f"[{'OK ' if ok else 'XATO'}] {label}"
          + ("" if ok else f"\n        kutildi: {want!r}\n        natija : {got!r}"))


def ok_(cond, label, extra=""):
    eq(bool(cond), True, label if not extra else f"{label} — {extra}")


async def scenario(url, tag: str) -> None:
    url_is_sqlite = not isinstance(url, str) or url.startswith("sqlite")
    await db.init(url)
    # toza boşlaş
    async with db.engine().begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    print(f"\n──────── {tag} ────────")

    # ---- foydalanuvçilar -------------------------------------------------
    u = await db.get_user(101, "ali", "Ali Valiyev")
    eq((u.mode, u.ui, u.subscribed, u.blocked), ("yangi", "yangi", True, False),
       f"{tag}: standart sozlamalar")
    eq(u.conv, 0, f"{tag}: yangi foydalanuvçi hisobi")

    await db.set_field(101, "ui", "kirill")
    await db.set_field(101, "smart", 0)
    u = await db.get_user(101)
    eq((u.ui, u.smart), ("kirill", False), f"{tag}: sozlama saqlandi")

    await db.bump(101, 120)
    await db.bump(101, 30)
    u = await db.get_user(101)
    eq((u.conv, u.chars), (2, 150), f"{tag}: statistika ösdi")

    eq((await db.find_user("@ali")).user_id, 101, f"{tag}: @username böyiça qidiruv")
    eq((await db.find_user("ALI")).user_id, 101, f"{tag}: katta-kiçik harfga sezgir emas")
    eq((await db.find_user(101)).user_id, 101, f"{tag}: ID böyiça qidiruv")
    eq(await db.find_user("yoq_bunday"), None, f"{tag}: topilmadi")

    # ---- auditoriyalar ---------------------------------------------------
    await db.get_user(102, "bek", "Bek")
    await db.get_user(103, "dil", "Dil")
    await db.set_field(103, "ui", "eski")
    await db.set_subscribed(102, False)
    await db.mark_blocked(103, True)

    eq(sorted(await db.audience_ids(Audience.ALL)), [101], f"{tag}: hamma (obuna + bloklanmagan)")
    eq(await db.audience_ids(Audience.CYR_UI), [101], f"{tag}: kirill interfeysi")
    eq(await db.audience_ids(Audience.OLD_UI), [], f"{tag}: eski interfeys (bloklangan çiqdi)")
    eq(sorted(await db.audience_ids(Audience.CUSTOM, "101, 999 -100500")),
       [-100500, 101, 999], f"{tag}: qölda berilgan ID lar")

    await db.mark_blocked(103, False)
    eq(sorted(await db.audience_ids(Audience.OLD_UI)), [103], f"{tag}: blok olingandan keyin")

    # faollik böyiça
    async with db.session() as s:
        old = await s.get(db.User, 103)
        old.last_seen = utcnow() - dt.timedelta(days=90)
        await s.commit()
    eq(sorted(await db.audience_ids(Audience.ACTIVE, "30")), [101], f"{tag}: faol (30 kun)")
    eq(sorted(await db.audience_ids(Audience.ACTIVE, "120")), [101, 103], f"{tag}: faol (120 kun)")

    # ---- guruh va kanallar ----------------------------------------------
    await db.remember_chat(-1001, "supergroup", "Test guruh")
    await db.set_chat_auto(-1001, True, "kirill")
    eq(await db.chat_auto(-1001), (True, "kirill"), f"{tag}: kanal avto-rejimi")
    eq(await db.audience_ids(Audience.CHATS), [-1001], f"{tag}: guruhlar auditoriyasi")
    await db.deactivate_chat(-1001)
    eq(await db.audience_ids(Audience.CHATS), [], f"{tag}: faolsiz guruh çiqarildi")
    await db.remember_chat(-1001, "supergroup", "Test guruh")
    eq(await db.audience_ids(Audience.CHATS), [-1001], f"{tag}: qayta qöşilganda tiklandi")

    # ---- statistika ------------------------------------------------------
    st = await db.stats()
    eq((st["users"], st["conv"], st["chars"], st["chats"]), (3, 2, 150, 1), f"{tag}: umumiy hisob")
    eq(st["subs"], 2, f"{tag}: xabar olişi mumkin bölganlar")
    ok_(st["today"] >= 1, f"{tag}: bugun faol")

    # ---- tarqatma --------------------------------------------------------
    bc = await db.create_broadcast(101, Audience.ALL, from_chat_id=101, message_id=55)
    eq(bc.status, BroadcastStatus.DRAFT.value, f"{tag}: tarqatma qoralama")
    total = await db.queue_targets(bc.id, [101, 102, 103, 101])   # takrorlangan ID
    eq(total, 3, f"{tag}: takrorlangan manzil bir marta navbatga tuşdi")

    pend = await db.pending_targets(bc.id)
    eq(len(pend), 3, f"{tag}: navbatdagi manzillar")
    await db.mark_target(pend[0].id, TargetStatus.SENT)
    await db.mark_target(pend[1].id, TargetStatus.BLOCKED, "bot bloklangan")
    eq(len(await db.pending_targets(bc.id)), 1, f"{tag}: qolgan navbat")

    fresh = await db.refresh_counters(bc.id)
    eq((fresh.sent, fresh.blocked, fresh.failed, fresh.done, fresh.total),
       (1, 1, 0, 2, 3), f"{tag}: hisoblagiçlar")

    await db.set_broadcast_status(bc.id, BroadcastStatus.RUNNING)
    eq(len(await db.running_broadcasts()), 1, f"{tag}: işlab turgan tarqatma")
    await db.set_broadcast_status(bc.id, BroadcastStatus.DONE)
    done = await db.get_broadcast(bc.id)
    eq(done.status, BroadcastStatus.DONE.value, f"{tag}: tugadi")
    ok_(done.finished_at is not None, f"{tag}: tugaş vaqti yozildi")
    eq(len(await db.running_broadcasts()), 0, f"{tag}: işlab turgani qolmadi")

    await db.create_broadcast(101, Audience.CHATS, text="salom", kind="matn")
    rows = await db.list_broadcasts(10)
    eq(len(rows), 2, f"{tag}: tarqatmalar röyxati")
    eq(rows[0].id > rows[1].id, True, f"{tag}: yangisi birinçi")

    # ---- şaxsiy xabar ----------------------------------------------------
    await db.log_direct(101, 102, "salom", True)
    await db.log_direct(101, 103, "salom", False, "bloklagan")
    async with db.session() as s:
        from sqlalchemy import func, select
        n = (await s.execute(select(func.count(db.DirectMessage.id)))).scalar_one()
    eq(n, 2, f"{tag}: şaxsiy xabarlar jurnali")

    # ---- get_user bloklanganni tiklaydi ----------------------------------
    await db.mark_blocked(102, True)
    await db.get_user(102)
    eq((await db.find_user(102)).blocked, False, f"{tag}: qayta yozgan foydalanuvçi tiklandi")

    # ---- sxema tekşiruvi va qöşimça migratsiya --------------------------
    diff = await db.schema_diff()
    eq((diff["tables"], diff["columns"]), ([], []), f"{tag}: sxema modellarga mos")

    if url_is_sqlite:
        # eski sxemani taqlid qilamiz: ustun va jadval öçiramiz
        from sqlalchemy import text as sa_text
        async with db.engine().begin() as conn:
            await conn.execute(sa_text("DROP INDEX IF EXISTS ix_users_reach"))
            await conn.execute(sa_text("ALTER TABLE users DROP COLUMN subscribed"))
            await conn.execute(sa_text("DROP TABLE direct_messages"))
        diff = await db.schema_diff()
        eq(diff["tables"], ["direct_messages"], f"{tag}: yöq jadval topildi")
        eq(diff["columns"], ["users.subscribed"], f"{tag}: yöq ustun topildi")

        # apply=False hеç narsani ösgartirmasligi kerak
        stmts = await db.upgrade_schema(apply=False)
        eq(len(stmts), 1, f"{tag}: ALTER taklif qilindi")
        eq((await db.schema_diff())["tables"], ["direct_messages"],
           f"{tag}: --check hеç narsa yaratmadi")

        await db.upgrade_schema(apply=True)
        diff = await db.schema_diff()
        eq((diff["tables"], diff["columns"]), ([], []), f"{tag}: sxema tiklandi")
        u = await db.find_user(101)
        eq((u.conv, u.subscribed), (2, True), f"{tag}: eski maʼlumot saqlanib qoldi")

    await db.close()


async def main() -> None:
    tmp = Path(tempfile.mkdtemp()) / "t.sqlite3"
    await scenario(tmp, "SQLite")

    mysql = os.getenv("TEST_DATABASE_URL", "").strip()
    if mysql:
        await scenario(mysql, "MySQL")
    else:
        print("\n[SKIP] MySQL testi — TEST_DATABASE_URL berilmagan")

    print("\n" + ("BARÇASI OʻTDI" if not fails else f"{fails} ta test yiqildi"))
    raise SystemExit(1 if fails else 0)


try:
    asyncio.run(main())
except SystemExit:
    raise
