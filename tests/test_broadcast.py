"""Tarqatma dvigatelining testlari (soxta bot bilan, Telegram kerak emas)."""
from __future__ import annotations

import asyncio
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aiogram.exceptions import (  # noqa: E402
    TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter,
)
from aiogram.methods import CopyMessage  # noqa: E402

from bot import db  # noqa: E402
from bot.broadcast import Broadcaster  # noqa: E402
from bot.models import Audience, Base, BroadcastStatus, TargetStatus  # noqa: E402

fails = 0
METHOD = CopyMessage(chat_id=1, from_chat_id=1, message_id=1)


def eq(got, want, label):
    global fails
    ok = got == want
    if not ok:
        fails += 1
    print(f"[{'OK ' if ok else 'XATO'}] {label}"
          + ("" if ok else f"\n        kutildi: {want!r}\n        natija : {got!r}"))


class FakeBot:
    """copy_message / send_message / forward_message ni taqlid qiladi."""

    def __init__(self, blocked=(), bad=(), retry_once=()) -> None:
        self.sent: list[int] = []
        self.blocked = set(blocked)
        self.bad = set(bad)
        self.retry_once = set(retry_once)
        self._retried: set[int] = set()
        self.hook = None

    async def _deliver(self, chat_id: int) -> bool:
        if chat_id in self.blocked:
            raise TelegramForbiddenError(METHOD, "bot was blocked by the user")
        if chat_id in self.bad:
            raise TelegramBadRequest(METHOD, "chat not found")
        if chat_id in self.retry_once and chat_id not in self._retried:
            self._retried.add(chat_id)
            raise TelegramRetryAfter(METHOD, "flood", 0)
        self.sent.append(chat_id)
        if self.hook:
            await self.hook(len(self.sent))
        return True

    async def copy_message(self, chat_id, from_chat_id, message_id):
        return await self._deliver(chat_id)

    async def forward_message(self, chat_id, from_chat_id, message_id):
        return await self._deliver(chat_id)

    async def send_message(self, chat_id, text):
        return await self._deliver(chat_id)


async def fresh(users: list[int], chats: list[int] = ()) -> None:
    async with db.engine().begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    for uid in users:
        await db.get_user(uid, f"u{uid}", f"User {uid}")
    for cid in chats:
        await db.remember_chat(cid, "supergroup", f"Chat {cid}")


async def target_map(bid: int) -> dict[int, str]:
    async with db.session() as s:
        from sqlalchemy import select
        rows = await s.execute(
            select(db.BroadcastTarget.chat_id, db.BroadcastTarget.status)
            .where(db.BroadcastTarget.broadcast_id == bid))
        return {cid: st for cid, st in rows}


async def main() -> None:
    tmp = Path(tempfile.mkdtemp()) / "b.sqlite3"
    await db.init(tmp)

    # ---------------------------------------------------- 1. oddiy tarqatma
    await fresh([1, 2, 3, 4, 5])
    bot = FakeBot()
    caster = Broadcaster(bot, rate=500)
    bc = await db.create_broadcast(1, Audience.ALL, from_chat_id=1, message_id=7)
    await db.queue_targets(bc.id, await db.audience_ids(Audience.ALL))
    await caster.start(bc.id)
    row = await db.get_broadcast(bc.id)
    eq(sorted(bot.sent), [1, 2, 3, 4, 5], "1. hammaga yuborildi")
    eq((row.status, row.sent, row.done, row.total),
       (BroadcastStatus.DONE.value, 5, 5, 5), "1. holat va hisoblagiçlar")

    # -------------------------------------------- 2. bloklagan / xato manzil
    await fresh([1, 2, 3, 4])
    bot = FakeBot(blocked=[2], bad=[3], retry_once=[4])
    caster = Broadcaster(bot, rate=500)
    bc = await db.create_broadcast(1, Audience.ALL, from_chat_id=1, message_id=7)
    await db.queue_targets(bc.id, [1, 2, 3, 4])
    await caster.start(bc.id)
    row = await db.get_broadcast(bc.id)
    tmap = await target_map(bc.id)
    eq(tmap[1], TargetStatus.SENT.value, "2. oddiy manzil")
    eq(tmap[2], TargetStatus.BLOCKED.value, "2. bloklagan foydalanuvçi")
    eq(tmap[3], TargetStatus.FAILED.value, "2. xato manzil")
    eq(tmap[4], TargetStatus.SENT.value, "2. flood-wait dan keyin yuborildi")
    eq((row.sent, row.blocked, row.failed), (2, 1, 1), "2. hisoblagiçlar")
    eq((await db.find_user(2)).blocked, True, "2. bloklagan foydalanuvçi bazada belgilandi")
    eq((await db.find_user(1)).blocked, False, "2. boşqalarga tegmadi")
    eq(await db.audience_ids(Audience.ALL), [1, 3, 4], "2. keyingi tarqatmada çiqarildi")

    # ------------------------------------------- 3. guruh — faolsiz qilinadi
    await fresh([1], chats=[-100500])
    bot = FakeBot(blocked=[-100500])
    caster = Broadcaster(bot, rate=500)
    bc = await db.create_broadcast(1, Audience.CHATS, from_chat_id=1, message_id=7)
    await db.queue_targets(bc.id, [-100500])
    await caster.start(bc.id)
    eq(await db.audience_ids(Audience.CHATS), [], "3. bot çiqarilgan guruh faolsiz qilindi")

    # ------------------------------------------------------- 4. töxtatiş
    await fresh(list(range(1, 31)))
    bot = FakeBot()
    caster = Broadcaster(bot, rate=500)
    bc = await db.create_broadcast(1, Audience.ALL, from_chat_id=1, message_id=7)
    await db.queue_targets(bc.id, list(range(1, 31)))

    async def stop_after(n: int) -> None:
        if n == 5:
            caster.cancel(bc.id)

    bot.hook = stop_after
    await caster.start(bc.id)
    row = await db.get_broadcast(bc.id)
    eq(row.status, BroadcastStatus.CANCELLED.value, "4. tarqatma töxtatildi")
    eq(len(bot.sent), 5, "4. töxtaganda yuborilgan soni")
    eq(row.sent, 5, "4. hisoblagiç töğri")
    eq(len(await db.pending_targets(bc.id)), 25, "4. qolgani navbatda qoldi")

    # --------------------------------- 5. qayta işga tuşganda davom ettiriş
    await db.set_broadcast_status(bc.id, BroadcastStatus.RUNNING)
    bot2 = FakeBot()
    caster2 = Broadcaster(bot2, rate=500)          # «yangi jarayon»
    resumed = await caster2.resume_all()
    eq(resumed, 1, "5. tugallanmagan tarqatma topildi")
    await asyncio.gather(*[t for t in caster2._tasks.values()])
    row = await db.get_broadcast(bc.id)
    eq(len(bot2.sent), 25, "5. faqat qolgani yuborildi")
    eq((row.status, row.sent), (BroadcastStatus.DONE.value, 30), "5. tarqatma tugadi")
    eq(len(await db.pending_targets(bc.id)), 0, "5. navbat böşadi")

    # ------------------------------------------------- 6. matnli tarqatma
    await fresh([1, 2])
    bot = FakeBot()
    caster = Broadcaster(bot, rate=500)
    bc = await db.create_broadcast(1, Audience.ALL, text="Salom", kind="matn")
    await db.queue_targets(bc.id, [1, 2])
    await caster.start(bc.id)
    eq(sorted(bot.sent), [1, 2], "6. matnli tarqatma yuborildi")

    # ------------------------------------------------------ 7. şaxsiy xabar
    bot = FakeBot(blocked=[2])
    caster = Broadcaster(bot, rate=500)
    ok, why = await caster.send_direct(1, 1, "salom")
    eq((ok, why), (True, None), "7. şaxsiy xabar yuborildi")
    ok, why = await caster.send_direct(1, 2, "salom")
    eq(ok, False, "7. bloklagan foydalanuvçiga yuborilmadi")
    eq((await db.find_user(2)).blocked, True, "7. bazada belgilandi")
    async with db.session() as s:
        from sqlalchemy import func, select
        n = (await s.execute(select(func.count(db.DirectMessage.id)))).scalar_one()
    eq(n, 2, "7. ikkalasi ham jurnalga yozildi")

    # ----------------------------------------- 8. ikki marta boşlansa bir marta
    await fresh([1, 2, 3])
    bot = FakeBot()
    caster = Broadcaster(bot, rate=200)
    bc = await db.create_broadcast(1, Audience.ALL, from_chat_id=1, message_id=7)
    await db.queue_targets(bc.id, [1, 2, 3])
    t1 = caster.start(bc.id)
    t2 = caster.start(bc.id)
    eq(t1 is t2, True, "8. ikkinçi start yangi vazifa yaratmadi")
    await t1
    eq(sorted(bot.sent), [1, 2, 3], "8. har bir manzilga bir martadan")

    await db.close()
    print("\n" + ("BARÇASI OʻTDI" if not fails else f"{fails} ta test yiqildi"))
    raise SystemExit(1 if fails else 0)


try:
    asyncio.run(main())
except SystemExit:
    raise
