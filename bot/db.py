"""Maʼlumotlar bazasi qatlami — SQLAlchemy 2.0 (async).

Standart holatda MySQL (`mysql+aiomysql://…`), testlar va lokal işlab
çiqiş uçun SQLite (`sqlite+aiosqlite://…`) işlatiladi.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Iterable, Sequence

from sqlalchemy import event, func, insert, select, update
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .config import config
from .models import (
    Audience,
    Base,
    Broadcast,
    BroadcastStatus,
    BroadcastTarget,
    Chat,
    DirectMessage,
    TargetStatus,
    User,
    utcnow,
)

__all__ = [
    "User", "Chat", "Broadcast", "BroadcastTarget", "DirectMessage",
    "Audience", "BroadcastStatus", "TargetStatus",
    "init", "close", "session", "engine",
    "get_user", "set_field", "bump", "mark_blocked", "set_subscribed",
    "all_user_ids", "audience_ids", "find_user",
    "remember_chat", "chat_auto", "set_chat_auto", "deactivate_chat",
    "find_chat", "list_chats",
    "running_broadcasts",
    "stats", "create_broadcast", "queue_targets", "pending_targets",
    "mark_target", "set_broadcast_status", "get_broadcast", "list_broadcasts",
    "refresh_counters", "count_targets", "save_counters", "log_direct", "schema_diff", "upgrade_schema",
]

_engine: AsyncEngine | None = None
_Session: async_sessionmaker[AsyncSession] | None = None

#: sozlamalarda ösgartirişga ruxsat berilgan maydonlar
_FIELDS = frozenset({"mode", "ui", "smart", "keep_foreign", "fmt", "subscribed"})


# --------------------------------------------------------------------------
# Ulaniş
# --------------------------------------------------------------------------
def _with_charset(dsn: str) -> str:
    """MySQL DSN da utf8mb4 kafolatlanadi (kirill va ö/ğ/ş/ç uçun şart)."""
    if not dsn.startswith("mysql") or "charset=" in dsn:
        return dsn
    return dsn + ("&" if "?" in dsn else "?") + "charset=utf8mb4"


def _resolve(url: str | Path | None) -> str:
    if isinstance(url, Path):
        return f"sqlite+aiosqlite:///{url}"
    if url:
        return _with_charset(str(url))
    if config.database_url:
        return _with_charset(config.database_url)
    config.db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite+aiosqlite:///{config.db_path}"


async def init(url: str | Path | None = None, *, create: bool = True) -> AsyncEngine:
    """Dvigatelni yaratadi va (kerak bölsa) jadvallarni quradi."""
    global _engine, _Session
    dsn = _resolve(url)
    kwargs: dict = {"echo": config.sql_echo, "future": True}
    if not dsn.startswith("sqlite"):
        # MySQL uzoq turgan ulanişni özi uzadi — pool_recycle şu sababli
        kwargs.update(pool_pre_ping=True, pool_recycle=3600,
                      pool_size=config.pool_size, max_overflow=config.pool_overflow)
    _engine = create_async_engine(dsn, **kwargs)
    if not dsn.startswith("sqlite"):
        _use_utc(_engine)
    if dsn.startswith("sqlite"):
        _tune_sqlite(_engine)
    _Session = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)
    if create:
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        diff = await schema_diff()
        if diff["columns"]:
            import logging
            logging.getLogger("yozuvbot.db").warning(
                "Bazada yetişmayotgan ustunlar: %s — `python -m bot.db --upgrade` "
                "buyruği bilan qöşing", ", ".join(diff["columns"]))
    return _engine


#: SQLite ni köp öqiş/yoziş uçun sozlaydigan pragmalar
_SQLITE_PRAGMAS = (
    "PRAGMA journal_mode=WAL",      # öqiş yoziş bilan bloklaşmaydi
    "PRAGMA synchronous=NORMAL",    # WAL bilan xavfsiz, ammo tezroq
    "PRAGMA foreign_keys=ON",       # ON DELETE CASCADE işlaşi uçun şart
    "PRAGMA busy_timeout=10000",    # band bölsa 10 soniya kutadi
    "PRAGMA cache_size=-32000",     # 32 MB sahifa keşi
    "PRAGMA temp_store=MEMORY",
)


def _tune_sqlite(eng: AsyncEngine) -> None:
    """Har bir SQLite ulanişiga pragmalarni qöyadi.

    Standart holat (rollback journal + synchronous=FULL) yoziş oqimini
    keskin çeklaydi va `foreign_keys` umuman öçiq böladi.
    """
    @event.listens_for(eng.sync_engine, "connect")
    def _set(dbapi_conn, _record):               # pragma: no cover - drayver içida
        cur = dbapi_conn.cursor()
        try:
            for pragma in _SQLITE_PRAGMAS:
                cur.execute(pragma)
        finally:
            cur.close()


def _use_utc(eng: AsyncEngine) -> None:
    """Har bir MySQL ulanişini UTC ga qöyadi.

    Dastur vaqtni Python tomonda UTC da yozadi; server vaqt mintaqasi
    boşqaça bölsa, `now()` va sana taqqoslaşlari nomuvofiq bölib qolardi.
    """
    @event.listens_for(eng.sync_engine, "connect")
    def _set_tz(dbapi_conn, _record):            # pragma: no cover - drayver içida
        cur = dbapi_conn.cursor()
        try:
            cur.execute("SET time_zone = '+00:00'")
        finally:
            cur.close()


async def schema_diff() -> dict[str, list[str]]:
    """Modellarda bor, ammo bazada yöq jadval/ustunlarni topadi.

    `create_all` mavjud jadvalga yangi ustun QOŞMAYDI — şu sababli eski
    sxemali baza jimgina buzilib qolmasligi uçun tekşirib turamiz.
    """
    from sqlalchemy import inspect as sa_inspect

    async with engine().connect() as conn:
        tables = await conn.run_sync(lambda c: sa_inspect(c).get_table_names())
        existing: dict[str, set[str]] = {}
        for name in tables:
            cols = await conn.run_sync(lambda c, n=name: sa_inspect(c).get_columns(n))
            existing[name] = {c["name"] for c in cols}

    report: dict[str, list[str]] = {"tables": [], "columns": []}
    for name, table in Base.metadata.tables.items():
        if name not in existing:
            report["tables"].append(name)
            continue
        for col in table.columns:
            if col.name not in existing[name]:
                report["columns"].append(f"{name}.{col.name}")
    return report


async def upgrade_schema(apply: bool = False) -> list[str]:
    """Yetişmayotgan ustunlarni qöşiş uçun ALTER TABLE larni qaytaradi.

    Faqat QOŞIŞ amalga oşiriladi — hеç narsa öçirilmaydi yoki ösgarmaydi.
    Murakkabroq ösgarişlar uçun Alembic işlatiş tavsiya etiladi.
    """
    from sqlalchemy import text as sa_text

    diff = await schema_diff()
    if diff["tables"] and apply:
        async with engine().begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    if not diff["columns"]:
        return []

    dialect = engine().dialect
    statements: list[str] = []
    for ref in diff["columns"]:
        tname, cname = ref.split(".", 1)
        col = Base.metadata.tables[tname].columns[cname]
        spec = f"{col.name} {col.type.compile(dialect)}"
        if col.server_default is not None:
            spec += f" DEFAULT {col.server_default.arg}"
        elif not col.nullable:
            spec += " NULL"          # mavjud qatorlar uçun NULL ga ruxsat
        statements.append(f"ALTER TABLE {tname} ADD COLUMN {spec}")

    if apply:
        async with engine().begin() as conn:
            for stmt in statements:
                await conn.execute(sa_text(stmt))
    return statements


async def close() -> None:
    global _engine, _Session
    if _engine is not None:
        await _engine.dispose()
    _engine, _Session = None, None


def engine() -> AsyncEngine:
    if _engine is None:
        raise RuntimeError("db.init() çaqirilmagan")
    return _engine


def session() -> AsyncSession:
    if _Session is None:
        raise RuntimeError("db.init() çaqirilmagan")
    return _Session()


# --------------------------------------------------------------------------
# Foydalanuvçilar
# --------------------------------------------------------------------------
async def get_user(user_id: int, username: str | None = None,
                   full_name: str | None = None) -> User:
    """Foydalanuvçini qaytaradi, yöq bölsa yaratadi; `last_seen` ni yangilaydi."""
    async with session() as s:
        user = await s.get(User, user_id)
        now = utcnow()
        if user is None:
            user = User(user_id=user_id, username=username, full_name=full_name,
                        created_at=now, last_seen=now)
            s.add(user)
        else:
            user.last_seen = now
            user.blocked = False
            if username is not None:
                user.username = username
            if full_name is not None:
                user.full_name = full_name
        await s.commit()
        return user


async def find_user(key: str | int) -> User | None:
    """ID yoki @username böyiça qidiradi."""
    async with session() as s:
        if isinstance(key, int) or str(key).lstrip("-").isdigit():
            return await s.get(User, int(key))
        name = str(key).lstrip("@")
        return (await s.execute(
            select(User).where(func.lower(User.username) == name.lower())
        )).scalar_one_or_none()


async def set_field(user_id: int, field: str, value) -> None:
    if field not in _FIELDS:
        raise ValueError(f"nomaʼlum maydon: {field}")
    if field in ("smart", "keep_foreign", "subscribed"):
        value = bool(value)
    async with session() as s:
        await s.execute(update(User).where(User.user_id == user_id).values(**{field: value}))
        await s.commit()


async def bump(user_id: int, chars: int) -> None:
    async with session() as s:
        await s.execute(
            update(User).where(User.user_id == user_id).values(
                conv=User.conv + 1, chars=User.chars + chars, last_seen=utcnow())
        )
        await s.commit()


async def mark_blocked(user_id: int, blocked: bool = True) -> None:
    async with session() as s:
        await s.execute(update(User).where(User.user_id == user_id).values(blocked=blocked))
        await s.commit()


async def set_subscribed(user_id: int, value: bool) -> None:
    await set_field(user_id, "subscribed", value)


async def all_user_ids() -> list[int]:
    """Xabar yuborsa böladigan barça foydalanuvçilar."""
    return await audience_ids(Audience.ALL)


async def audience_ids(audience: str | Audience, arg: str | None = None) -> list[int]:
    """Tanlangan auditoriya uçun chat ID lar röyxati."""
    audience = Audience(audience)
    async with session() as s:
        if audience is Audience.CHATS:
            rows = await s.execute(select(Chat.chat_id).where(Chat.active.is_(True)))
            return [r[0] for r in rows]
        if audience is Audience.CUSTOM:
            ids = [int(x) for x in (arg or "").replace(",", " ").split() if
                   x.lstrip("-").isdigit()]
            return ids
        q = select(User.user_id).where(User.subscribed.is_(True), User.blocked.is_(False))
        if audience is Audience.ACTIVE:
            days = int(arg or 30)
            since = utcnow() - dt.timedelta(days=days)
            q = q.where(User.last_seen >= since)
        elif audience is Audience.NEW_UI:
            q = q.where(User.ui == "yangi")
        elif audience is Audience.OLD_UI:
            q = q.where(User.ui == "eski")
        elif audience is Audience.CYR_UI:
            q = q.where(User.ui == "kirill")
        rows = await s.execute(q)
        return [r[0] for r in rows]


# --------------------------------------------------------------------------
# Guruh va kanallar
# --------------------------------------------------------------------------
async def remember_chat(chat_id: int, ctype: str | None, title: str | None,
                        username: str | None = None) -> None:
    async with session() as s:
        chat = await s.get(Chat, chat_id)
        if chat is None:
            s.add(Chat(chat_id=chat_id, type=ctype, title=title, username=username))
        else:
            chat.type, chat.title, chat.active = ctype, title, True
            if username is not None:
                chat.username = username
        await s.commit()


async def find_chat(key: str | int) -> Chat | None:
    """Guruh/kanalni ID yoki @username böyiça topadi."""
    async with session() as s:
        if isinstance(key, int) or str(key).lstrip("-").isdigit():
            return await s.get(Chat, int(key))
        name = str(key).lstrip("@")
        return (await s.execute(
            select(Chat).where(func.lower(Chat.username) == name.lower())
        )).scalar_one_or_none()


async def list_chats(limit: int = 50, only_active: bool = True) -> Sequence[Chat]:
    async with session() as s:
        q = select(Chat).order_by(Chat.added_at.desc()).limit(limit)
        if only_active:
            q = q.where(Chat.active.is_(True))
        return (await s.execute(q)).scalars().all()


async def deactivate_chat(chat_id: int) -> None:
    """Bot çiqarilgan guruh/kanalni faolsiz deb belgilaydi."""
    async with session() as s:
        await s.execute(update(Chat).where(Chat.chat_id == chat_id).values(active=False))
        await s.commit()


async def chat_auto(chat_id: int) -> tuple[bool, str]:
    async with session() as s:
        chat = await s.get(Chat, chat_id)
        return (bool(chat.auto), chat.mode) if chat else (False, "yangi")


async def set_chat_auto(chat_id: int, auto: bool, mode: str = "yangi") -> None:
    async with session() as s:
        chat = await s.get(Chat, chat_id)
        if chat is None:
            s.add(Chat(chat_id=chat_id, auto=auto, mode=mode))
        else:
            chat.auto, chat.mode = auto, mode
        await s.commit()


# --------------------------------------------------------------------------
# Statistika
# --------------------------------------------------------------------------
async def stats() -> dict[str, int]:
    today = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    week = utcnow() - dt.timedelta(days=7)
    async with session() as s:
        row = (await s.execute(select(
            func.count(User.user_id),
            func.coalesce(func.sum(User.conv), 0),
            func.coalesce(func.sum(User.chars), 0),
        ))).one()
        today_n = (await s.execute(select(func.count(User.user_id))
                                   .where(User.last_seen >= today))).scalar_one()
        week_n = (await s.execute(select(func.count(User.user_id))
                                  .where(User.last_seen >= week))).scalar_one()
        subs = (await s.execute(select(func.count(User.user_id))
                                .where(User.subscribed.is_(True),
                                       User.blocked.is_(False)))).scalar_one()
        blocked = (await s.execute(select(func.count(User.user_id))
                                   .where(User.blocked.is_(True)))).scalar_one()
        chats = (await s.execute(select(func.count(Chat.chat_id)))).scalar_one()
    return {"users": int(row[0]), "conv": int(row[1]), "chars": int(row[2]),
            "today": int(today_n), "week": int(week_n), "subs": int(subs),
            "blocked": int(blocked), "chats": int(chats)}


# --------------------------------------------------------------------------
# Tarqatmalar
# --------------------------------------------------------------------------
async def create_broadcast(admin_id: int, audience: str | Audience,
                           audience_arg: str | None = None, *,
                           from_chat_id: int | None = None,
                           message_id: int | None = None,
                           text: str | None = None,
                           kind: str = "nusxa") -> Broadcast:
    async with session() as s:
        bc = Broadcast(admin_id=admin_id, audience=Audience(audience).value,
                       audience_arg=audience_arg, from_chat_id=from_chat_id,
                       message_id=message_id, text=text, kind=kind,
                       status=BroadcastStatus.DRAFT.value)
        s.add(bc)
        await s.commit()
        return bc


async def queue_targets(broadcast_id: int, chat_ids: Iterable[int]) -> int:
    """Manzillarni navbatga qöyadi va umumiy sonni qaytaradi."""
    ids = list(dict.fromkeys(chat_ids))
    if not ids:
        return 0
    pending = TargetStatus.PENDING.value
    rows = [{"broadcast_id": broadcast_id, "chat_id": cid, "status": pending}
            for cid in ids]
    async with session() as s:
        # ORM obyektlari örniga töplab INSERT — katta tarqatmada ançayin tezroq
        for i in range(0, len(rows), 5000):
            await s.execute(insert(BroadcastTarget), rows[i:i + 5000])
        await s.execute(update(Broadcast).where(Broadcast.id == broadcast_id)
                        .values(total=len(ids)))
        await s.commit()
    return len(ids)


async def pending_targets(broadcast_id: int, limit: int = 200) -> Sequence[BroadcastTarget]:
    async with session() as s:
        rows = await s.execute(
            select(BroadcastTarget)
            .where(BroadcastTarget.broadcast_id == broadcast_id,
                   BroadcastTarget.status == TargetStatus.PENDING.value)
            .order_by(BroadcastTarget.id).limit(limit)
        )
        return rows.scalars().all()


async def mark_target(target_id: int, status: str | TargetStatus,
                      error: str | None = None) -> None:
    async with session() as s:
        await s.execute(
            update(BroadcastTarget).where(BroadcastTarget.id == target_id)
            .values(status=TargetStatus(status).value, error=(error or "")[:255],
                    sent_at=utcnow())
        )
        await s.commit()


async def count_targets(broadcast_id: int) -> dict[str, int]:
    """Manzillarni holati böyiça sanaydi (qimmat — kamdan-kam çaqiriladi)."""
    async with session() as s:
        rows = await s.execute(
            select(BroadcastTarget.status, func.count())
            .where(BroadcastTarget.broadcast_id == broadcast_id)
            .group_by(BroadcastTarget.status)
        )
        return {status: int(n) for status, n in rows}


async def save_counters(broadcast_id: int, sent: int, failed: int, blocked: int) -> None:
    """Hisoblagiçlarni tögridan-tögri yozadi — jadvalni qayta sanamasdan.

    Tarqatma davomida yüz minglab qatorni har safar GROUP BY qiliş
    jarayonni butunlay töxtatib qöyardi.
    """
    async with session() as s:
        await s.execute(update(Broadcast).where(Broadcast.id == broadcast_id)
                        .values(sent=sent, failed=failed, blocked=blocked))
        await s.commit()


async def refresh_counters(broadcast_id: int) -> Broadcast | None:
    """Manzillar jadvalidan hisoblagiçlarni qayta hisoblaydi."""
    counts = await count_targets(broadcast_id)
    async with session() as s:
        bc = await s.get(Broadcast, broadcast_id)
        if bc is None:
            return None
        bc.sent = counts.get(TargetStatus.SENT.value, 0)
        bc.failed = counts.get(TargetStatus.FAILED.value, 0)
        bc.blocked = counts.get(TargetStatus.BLOCKED.value, 0)
        await s.commit()
        return bc


async def set_broadcast_status(broadcast_id: int, status: str | BroadcastStatus) -> None:
    status = BroadcastStatus(status)
    values: dict = {"status": status.value}
    if status is BroadcastStatus.RUNNING:
        values["started_at"] = utcnow()
    elif status in (BroadcastStatus.DONE, BroadcastStatus.CANCELLED, BroadcastStatus.FAILED):
        values["finished_at"] = utcnow()
    async with session() as s:
        await s.execute(update(Broadcast).where(Broadcast.id == broadcast_id).values(**values))
        await s.commit()


async def get_broadcast(broadcast_id: int) -> Broadcast | None:
    async with session() as s:
        return await s.get(Broadcast, broadcast_id)


async def list_broadcasts(limit: int = 10) -> Sequence[Broadcast]:
    async with session() as s:
        rows = await s.execute(
            select(Broadcast).order_by(Broadcast.id.desc()).limit(limit))
        return rows.scalars().all()


async def running_broadcasts() -> Sequence[Broadcast]:
    async with session() as s:
        rows = await s.execute(
            select(Broadcast).where(Broadcast.status == BroadcastStatus.RUNNING.value))
        return rows.scalars().all()


async def log_direct(admin_id: int, user_id: int, text: str, ok: bool,
                     error: str | None = None) -> None:
    async with session() as s:
        s.add(DirectMessage(admin_id=admin_id, user_id=user_id, text=text[:4000],
                            ok=ok, error=(error or None)))
        await s.commit()


# --------------------------------------------------------------------------
# Buyruq qatori:  python -m bot.db --create | --drop | --url
# --------------------------------------------------------------------------
async def _cli() -> int:
    import argparse
    import sys

    p = argparse.ArgumentParser(prog="bot.db", description="Baza jadvallarini boşqariş")
    p.add_argument("--url", help="ulaniş satri (standart: .env dan)")
    p.add_argument("--create", action="store_true", help="jadvallarni yaratiş")
    p.add_argument("--drop", action="store_true", help="jadvallarni ÖÇIRIŞ")
    p.add_argument("--show", action="store_true", help="ulaniş satrini körsatiş")
    p.add_argument("--check", action="store_true", help="sxemani modellar bilan solıştiriş")
    p.add_argument("--upgrade", action="store_true",
                   help="yetişmayotgan jadval/ustunlarni qöşiş (faqat QOŞIŞ)")
    a = p.parse_args()

    dsn = _resolve(a.url)
    safe = dsn.split("@")[-1] if "@" in dsn else dsn
    if a.check or a.upgrade:
        await init(dsn, create=False)
        diff = await schema_diff()
        if not diff["tables"] and not diff["columns"]:
            print("Sxema modellarga mos.")
            await close()
            return 0
        if diff["tables"]:
            print("Yöq jadvallar :", ", ".join(diff["tables"]))
        if diff["columns"]:
            print("Yöq ustunlar  :", ", ".join(diff["columns"]))
        stmts = await upgrade_schema(apply=a.upgrade)
        for stmt in stmts:
            print(("BAJARILDI: " if a.upgrade else "KERAK: ") + stmt)
        if not a.upgrade:
            print("\nQöşiş uçun: python -m bot.db --upgrade")
        await close()
        return 0

    if a.show or not (a.create or a.drop):
        print("DSN:", safe)
        print("Jadvallar:", ", ".join(Base.metadata.tables))
        return 0

    eng = await init(dsn, create=False)
    if a.drop:
        confirm = input(f"«{safe}» dagi BARÇA jadval öçirilsinmi? (ha/yöq): ")
        if confirm.strip().lower() not in ("ha", "yes", "y"):
            print("Bekor qilindi.")
            await close()
            return 1
        async with eng.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        print("Jadvallar öçirildi.")
    if a.create:
        async with eng.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Jadvallar yaratildi:", ", ".join(Base.metadata.tables))
    await close()
    return 0


if __name__ == "__main__":
    import asyncio as _asyncio

    raise SystemExit(_asyncio.run(_cli()))
