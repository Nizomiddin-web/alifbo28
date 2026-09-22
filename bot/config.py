from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote_plus

try:
    from dotenv import load_dotenv
    load_dotenv()
except ModuleNotFoundError:  # pragma: no cover
    pass

ROOT = Path(__file__).resolve().parent.parent


def _bool(key: str, default: bool = False) -> bool:
    return os.getenv(key, str(default)).strip().lower() in {"1", "true", "yes", "ha", "on"}


def _ids(key: str) -> set[int]:
    raw = os.getenv(key, "")
    return {int(x) for x in raw.replace(" ", "").split(",") if x.lstrip("-").isdigit()}


def _database_url() -> str:
    """DATABASE_URL, yoki alohida MYSQL_* ösgaruvçilaridan yiğiladi."""
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        return url
    host = os.getenv("MYSQL_HOST", "").strip()
    if not host:
        return ""
    user = quote_plus(os.getenv("MYSQL_USER", "root"))
    password = quote_plus(os.getenv("MYSQL_PASSWORD", ""))
    port = os.getenv("MYSQL_PORT", "3306")
    name = os.getenv("MYSQL_DB", "yozuvbot")
    charset = os.getenv("MYSQL_CHARSET", "utf8mb4")
    auth = f"{user}:{password}@" if password else f"{user}@"
    return f"mysql+aiomysql://{auth}{host}:{port}/{name}?charset={charset}"


@dataclass(frozen=True)
class Config:
    token: str = field(default_factory=lambda: os.getenv("BOT_TOKEN", "").strip())
    admins: frozenset[int] = field(default_factory=lambda: frozenset(_ids("ADMINS")))
    # --- maʼlumotlar bazasi ---
    database_url: str = field(default_factory=lambda: _database_url())
    db_path: Path = field(default_factory=lambda: ROOT / os.getenv("DB_PATH", "data/bot.sqlite3"))
    pool_size: int = field(default_factory=lambda: int(os.getenv("DB_POOL_SIZE", "10")))
    pool_overflow: int = field(default_factory=lambda: int(os.getenv("DB_POOL_OVERFLOW", "20")))
    sql_echo: bool = field(default_factory=lambda: _bool("SQL_ECHO"))
    # --- tarqatma ---
    broadcast_rate: float = field(default_factory=lambda: float(os.getenv("BROADCAST_RATE", "20")))
    channel_auto: bool = field(default_factory=lambda: _bool("CHANNEL_AUTO"))
    throttle: float = field(default_factory=lambda: float(os.getenv("THROTTLE", "0.5")))
    max_file_mb: int = field(default_factory=lambda: int(os.getenv("MAX_FILE_MB", "20")))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper())

    def is_admin(self, user_id: int | None) -> bool:
        return user_id is not None and user_id in self.admins


config = Config()
