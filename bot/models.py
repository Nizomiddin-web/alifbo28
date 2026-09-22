"""SQLAlchemy modellari (MySQL / SQLite)."""
from __future__ import annotations

import datetime as dt
import enum

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

#: MySQL da özbek/kirill matni uçun şart
MYSQL_ARGS = {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"}


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class WithDefaults:
    """Standart qiymatlarni obyekt YARATILGANDA qöyadi.

    SQLAlchemy ning `default=` qiymati faqat INSERT paytida işlaydi, şu
    sababli bazaga yozilmagan obyektda maydonlar `None` böladi. Bu
    aralaştirgiç ularni darhol töldiradi.
    """

    _DEFAULTS: dict = {}

    def __init__(self, **kw):
        for key, value in self._DEFAULTS.items():
            kw.setdefault(key, value() if callable(value) else value)
        super().__init__(**kw)


class Script(str, enum.Enum):
    NEW = "yangi"
    OLD = "eski"
    CYR = "kirill"
    AUTO = "avto"


class Audience(str, enum.Enum):
    """Tarqatma kimga yuboriladi."""
    ALL = "barça"            # obuna bölgan barça foydalanuvçilar
    ACTIVE = "faol"          # oxirgi N kunda faol bölganlar
    NEW_UI = "yangi_ui"      # interfeysi yangi alifboda bölganlar
    OLD_UI = "eski_ui"
    CYR_UI = "kirill_ui"
    CHATS = "guruhlar"       # guruh va kanallar
    CUSTOM = "tanlangan"     # qölda berilgan ID lar


class BroadcastStatus(str, enum.Enum):
    DRAFT = "tayyorlanmoqda"
    RUNNING = "yuborilmoqda"
    DONE = "tugadi"
    CANCELLED = "bekor qilindi"
    FAILED = "xato"


class TargetStatus(str, enum.Enum):
    PENDING = "navbatda"
    SENT = "yuborildi"
    BLOCKED = "bloklagan"
    FAILED = "xato"


class User(WithDefaults, Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_last_seen", "last_seen"),
        Index("ix_users_reach", "subscribed", "blocked"),
        MYSQL_ARGS,
    )

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    username: Mapped[str | None] = mapped_column(String(64))
    full_name: Mapped[str | None] = mapped_column(String(255))

    # --- sozlamalar ---
    mode: Mapped[str] = mapped_column(String(16), default=Script.NEW.value, server_default="yangi")
    ui: Mapped[str] = mapped_column(String(16), default=Script.NEW.value, server_default="yangi")
    smart: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    keep_foreign: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    fmt: Mapped[str] = mapped_column(String(16), default="oddiy", server_default="oddiy")

    # --- xabar yuboriş ---
    subscribed: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    blocked: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")

    # --- statistika ---
    conv: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    chars: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")

    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow,
                                                    server_default=func.now())
    last_seen: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow,
                                                   server_default=func.now())

    _DEFAULTS = {
        "mode": Script.NEW.value, "ui": Script.NEW.value, "fmt": "oddiy",
        "smart": True, "keep_foreign": True, "subscribed": True, "blocked": False,
        "conv": 0, "chars": 0, "created_at": utcnow, "last_seen": utcnow,
    }

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.user_id} @{self.username}>"


class Chat(WithDefaults, Base):
    """Guruh va kanallar."""
    __tablename__ = "chats"
    __table_args__ = (Index("ix_chats_active", "active"), MYSQL_ARGS)

    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    type: Mapped[str | None] = mapped_column(String(32))
    title: Mapped[str | None] = mapped_column(String(255))
    username: Mapped[str | None] = mapped_column(String(64))
    auto: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    mode: Mapped[str] = mapped_column(String(16), default=Script.NEW.value, server_default="yangi")
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    added_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow,
                                                  server_default=func.now())

    _DEFAULTS = {"auto": False, "mode": Script.NEW.value, "active": True,
                 "added_at": utcnow}


class Broadcast(WithDefaults, Base):
    """Bir marta yuborilgan tarqatma."""
    __tablename__ = "broadcasts"
    __table_args__ = (Index("ix_broadcasts_status", "status"), MYSQL_ARGS)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    admin_id: Mapped[int] = mapped_column(BigInteger)
    audience: Mapped[str] = mapped_column(String(32), default=Audience.ALL.value)
    audience_arg: Mapped[str | None] = mapped_column(String(255))

    #: nusxalanadigan xabar (copy_message) — yoki tövridan-tögri matn
    from_chat_id: Mapped[int | None] = mapped_column(BigInteger)
    message_id: Mapped[int | None] = mapped_column(BigInteger)
    text: Mapped[str | None] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(16), default="nusxa")   # nusxa | matn | yönaltiriş

    status: Mapped[str] = mapped_column(String(24), default=BroadcastStatus.DRAFT.value)
    total: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    sent: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    failed: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    blocked: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow,
                                                    server_default=func.now())
    started_at: Mapped[dt.datetime | None] = mapped_column(DateTime)
    finished_at: Mapped[dt.datetime | None] = mapped_column(DateTime)

    targets: Mapped[list["BroadcastTarget"]] = relationship(
        back_populates="broadcast", cascade="all, delete-orphan", lazy="selectin",
    )

    _DEFAULTS = {
        "audience": Audience.ALL.value, "kind": "nusxa",
        "status": BroadcastStatus.DRAFT.value,
        "total": 0, "sent": 0, "failed": 0, "blocked": 0, "created_at": utcnow,
    }

    @property
    def done(self) -> int:
        return (self.sent or 0) + (self.failed or 0) + (self.blocked or 0)


class BroadcastTarget(WithDefaults, Base):
    """Tarqatmaning bitta manzili — qayta işga tuşirilsa davom ettiriladi."""
    __tablename__ = "broadcast_targets"
    __table_args__ = (
        UniqueConstraint("broadcast_id", "chat_id", name="uq_target"),
        Index("ix_target_queue", "broadcast_id", "status"),
        MYSQL_ARGS,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # alohida index=True kerak emas: ix_target_queue ning birinçi ustuni
    # aynan şu maydon, MySQL FK talabini ham öşa qondiradi
    broadcast_id: Mapped[int] = mapped_column(
        ForeignKey("broadcasts.id", ondelete="CASCADE"))
    chat_id: Mapped[int] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(16), default=TargetStatus.PENDING.value)
    error: Mapped[str | None] = mapped_column(String(255))
    sent_at: Mapped[dt.datetime | None] = mapped_column(DateTime)

    broadcast: Mapped[Broadcast] = relationship(back_populates="targets")

    _DEFAULTS = {"status": TargetStatus.PENDING.value}


class DirectMessage(Base):
    """Adminning bitta foydalanuvçiga yozgan xabari (tarix uçun)."""
    __tablename__ = "direct_messages"
    __table_args__ = (MYSQL_ARGS,)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    admin_id: Mapped[int] = mapped_column(BigInteger)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    text: Mapped[str] = mapped_column(Text)
    ok: Mapped[bool] = mapped_column(Boolean, default=True)
    error: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow,
                                                    server_default=func.now())
