from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats, ErrorEvent

from . import broadcast, db
from .config import config
from .handlers import build_router
from .middlewares import ThrottleMiddleware, UserMiddleware

log = logging.getLogger("yozuvbot")

COMMANDS = [
    ("start", "Botni işga tuşiriş"),
    ("yangi", "Yangi alifboga ötkaziş"),
    ("eski", "Eski alifboga ötkaziş"),
    ("kirill", "Kirillga ötkaziş"),
    ("avto", "Avtomatik tanlaş"),
    ("alifbo", "Rasmiy alifbo jadvali"),
    ("misol", "Misollar: söz yozilişi"),
    ("sozlama", "Sozlamalar"),
    ("mening", "Statistikam"),
    ("obuna", "Yangiliklarga obuna"),
    ("yordam", "Yöriqnoma"),
]

def _safe_dsn(url) -> str:
    """Parolsiz körinişdagi ulaniş satri (jurnalga yozmaslik uçun)."""
    try:
        return url.render_as_string(hide_password=True)
    except Exception:            # pragma: no cover
        return str(url)


ALLOWED_UPDATES = [
    "message", "edited_message", "callback_query",
    "inline_query", "channel_post", "my_chat_member",
]

errors = Router(name="errors")


@errors.error(F.update.message.as_("message"))
async def on_error(event: ErrorEvent, message=None) -> bool:
    log.exception("handler xatosi: %s", event.exception)
    if message is not None:
        try:
            await message.answer("⚠️ Kutilmagan xato yuz berdi. Qaytadan urinib köring.")
        except Exception:
            pass
    return True


@errors.error()
async def on_any_error(event: ErrorEvent) -> bool:
    log.exception("xato: %s", event.exception)
    return True


async def set_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        [BotCommand(command=c, description=d) for c, d in COMMANDS],
        scope=BotCommandScopeAllPrivateChats(),
    )


async def main() -> None:
    logging.basicConfig(
        level=getattr(logging, config.log_level, logging.INFO),
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
    if not config.token:
        raise SystemExit("BOT_TOKEN topilmadi. .env faylini tekşiring (.env.example dan nusxa oling).")

    await db.init()
    log.info("baza: %s", _safe_dsn(db.engine().url))

    bot = Bot(
        token=config.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML, link_preview_is_disabled=True),
    )
    caster = broadcast.setup(bot, config.broadcast_rate)
    dp = Dispatcher()
    dp.message.outer_middleware(ThrottleMiddleware(config.throttle))
    dp.update.outer_middleware(UserMiddleware())
    dp.include_router(build_router())
    dp.include_router(errors)

    await set_commands(bot)
    me = await bot.me()
    resumed = await caster.resume_all()
    if resumed:
        log.info("%s ta tugallanmagan tarqatma davom ettirildi", resumed)
    log.info("@%s işga tuşdi", me.username)
    try:
        await dp.start_polling(
            bot,
            allowed_updates=ALLOWED_UPDATES,
        )
    finally:
        await caster.shutdown()
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit) as exc:
        if isinstance(exc, SystemExit) and exc.code:
            raise
