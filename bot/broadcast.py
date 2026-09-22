"""Tarqatma dvigateli.

Xususiyatlari:
  * tezlik çegarasi (Telegram sekundiga ~30 xabarga ruxsat beradi);
  * `RetryAfter` ni hurmat qiladi — flood-wait da kutadi va qaytadan uradi;
  * botni bloklagan foydalanuvçini bazada belgilaydi;
  * har bir manzil bazada saqlanadi — bot qayta işga tuşsa, tarqatma
    töxtagan joyidan davom etadi;
  * istalgan payt töxtatsa böladi.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from aiogram import Bot
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramRetryAfter,
)

from . import db
from .models import Broadcast, BroadcastStatus, TargetStatus

log = logging.getLogger("yozuvbot.broadcast")


@dataclass
class Progress:
    """Tarqatma holati — jadvalni qayta sanamasdan."""
    id: int
    status: str
    total: int
    sent: int = 0
    failed: int = 0
    blocked: int = 0

    @property
    def done(self) -> int:
        return self.sent + self.failed + self.blocked

#: bir hodisada nеça manzil öqiladi
BATCH = 200
#: neça yuborişdan keyin holat xabari yangilanadi
PROGRESS_EVERY = 25


class Broadcaster:
    def __init__(self, bot: Bot, rate: float = 20.0) -> None:
        self.bot = bot
        self.delay = 1.0 / max(rate, 0.5)
        self._tasks: dict[int, asyncio.Task] = {}
        self._cancelled: set[int] = set()

    # ------------------------------------------------------------ boşqaruv
    def is_running(self, broadcast_id: int) -> bool:
        task = self._tasks.get(broadcast_id)
        return task is not None and not task.done()

    def start(self, broadcast_id: int, on_progress=None) -> asyncio.Task:
        if self.is_running(broadcast_id):
            return self._tasks[broadcast_id]
        self._cancelled.discard(broadcast_id)
        task = asyncio.create_task(self._run(broadcast_id, on_progress),
                                   name=f"broadcast-{broadcast_id}")
        self._tasks[broadcast_id] = task
        return task

    def cancel(self, broadcast_id: int) -> bool:
        if not self.is_running(broadcast_id):
            return False
        self._cancelled.add(broadcast_id)
        return True

    async def shutdown(self) -> None:
        for task in list(self._tasks.values()):
            if not task.done():
                task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks.values(), return_exceptions=True)
        self._tasks.clear()

    async def resume_all(self) -> int:
        """Bot qayta işga tuşganda tugallanmagan tarqatmalarni davom ettiradi."""
        rows = await db.running_broadcasts()
        for bc in rows:
            log.info("tarqatma #%s davom ettirilmoqda", bc.id)
            self.start(bc.id)
        return len(rows)

    # -------------------------------------------------------------- yuboriş
    async def _send_one(self, bc: Broadcast, chat_id: int) -> tuple[TargetStatus, str | None]:
        """Bitta manzilga yuboradi. Flood-wait da kutib qayta uradi."""
        for attempt in range(3):
            try:
                if bc.kind == "matn":
                    await self.bot.send_message(chat_id, bc.text or "")
                elif bc.kind == "yönaltiriş":
                    await self.bot.forward_message(chat_id, bc.from_chat_id, bc.message_id)
                else:
                    await self.bot.copy_message(chat_id, bc.from_chat_id, bc.message_id)
                return TargetStatus.SENT, None
            except TelegramRetryAfter as exc:
                wait = getattr(exc, "retry_after", 5) + 1
                log.warning("flood-wait %ss (chat %s)", wait, chat_id)
                await asyncio.sleep(wait)
            except TelegramForbiddenError as exc:
                # foydalanuvçi botni bloklagan yoki bot guruhdan çiqarilgan
                if chat_id > 0:
                    await db.mark_blocked(chat_id, True)
                else:
                    await db.deactivate_chat(chat_id)
                return TargetStatus.BLOCKED, str(exc)[:200]
            except TelegramBadRequest as exc:
                return TargetStatus.FAILED, str(exc)[:200]
            except asyncio.CancelledError:
                raise
            except Exception as exc:                      # kutilmagan xato
                if attempt == 2:
                    return TargetStatus.FAILED, f"{type(exc).__name__}: {exc}"[:200]
                await asyncio.sleep(2)
        return TargetStatus.FAILED, "flood-wait tugamadi"

    async def _run(self, broadcast_id: int, on_progress=None) -> None:
        bc = await db.get_broadcast(broadcast_id)
        if bc is None:
            return
        await db.set_broadcast_status(broadcast_id, BroadcastStatus.RUNNING)
        # davom ettirilgan bölsa — allaqaçon yuborilganlarni hisobga olamiz
        counts = await db.count_targets(broadcast_id)
        p = Progress(
            id=broadcast_id, status=BroadcastStatus.RUNNING.value, total=bc.total,
            sent=counts.get(TargetStatus.SENT.value, 0),
            failed=counts.get(TargetStatus.FAILED.value, 0),
            blocked=counts.get(TargetStatus.BLOCKED.value, 0),
        )
        done = 0
        try:
            while True:
                if broadcast_id in self._cancelled:
                    await db.set_broadcast_status(broadcast_id, BroadcastStatus.CANCELLED)
                    break
                targets = await db.pending_targets(broadcast_id, BATCH)
                if not targets:
                    await db.set_broadcast_status(broadcast_id, BroadcastStatus.DONE)
                    break
                for target in targets:
                    if broadcast_id in self._cancelled:
                        break
                    status, error = await self._send_one(bc, target.chat_id)
                    await db.mark_target(target.id, status, error)
                    if status is TargetStatus.SENT:
                        p.sent += 1
                    elif status is TargetStatus.BLOCKED:
                        p.blocked += 1
                    else:
                        p.failed += 1
                    done += 1
                    if done % PROGRESS_EVERY == 0:
                        await db.save_counters(broadcast_id, p.sent, p.failed, p.blocked)
                        if on_progress:
                            await _safe(on_progress, p)
                    await asyncio.sleep(self.delay)
        except asyncio.CancelledError:
            await db.set_broadcast_status(broadcast_id, BroadcastStatus.CANCELLED)
            raise
        except Exception:
            log.exception("tarqatma #%s yiqildi", broadcast_id)
            await db.set_broadcast_status(broadcast_id, BroadcastStatus.FAILED)
        finally:
            # yakunda bir marta — aniq raqam jadvaldan hisoblanadi
            fresh = await db.refresh_counters(broadcast_id)
            if on_progress and fresh is not None:
                await _safe(on_progress, fresh)
            self._cancelled.discard(broadcast_id)

    # --------------------------------------------------------- bitta xabar
    async def send_direct(self, admin_id: int, target: int | str,
                          text: str) -> tuple[bool, str | None]:
        """Bitta manzilga xabar — foydalanuvçi, guruh yoki kanal.

        `target` musbat son bölsa foydalanuvçi, manfiy bölsa guruh/kanal,
        `@nom` bölsa oçiq kanal.
        """
        log_id = target if isinstance(target, int) else 0
        try:
            await self.bot.send_message(target, text)
        except TelegramForbiddenError as exc:
            if isinstance(target, int) and target < 0:
                await db.deactivate_chat(target)
                why = "bot bu guruh/kanaldan çiqarilgan"
            else:
                if isinstance(target, int):
                    await db.mark_blocked(target, True)
                why = "foydalanuvçi botni bloklagan"
            await db.log_direct(admin_id, log_id, text, False, str(exc)[:200])
            return False, why
        except Exception as exc:
            await db.log_direct(admin_id, log_id, text, False, str(exc)[:200])
            return False, f"{type(exc).__name__}: {exc}"[:200]
        await db.log_direct(admin_id, log_id, text, True)
        return True, None


async def _safe(callback, *args) -> None:
    try:
        result = callback(*args)
        if asyncio.iscoroutine(result):
            await result
    except Exception:                                     # progress muhim emas
        log.debug("progress callback xatosi", exc_info=True)


#: yagona nusxa — `main.py` da töldiriladi
broadcaster: Broadcaster | None = None


def setup(bot: Bot, rate: float) -> Broadcaster:
    global broadcaster
    broadcaster = Broadcaster(bot, rate)
    return broadcaster


def get() -> Broadcaster:
    if broadcaster is None:
        raise RuntimeError("broadcast.setup() çaqirilmagan")
    return broadcaster
