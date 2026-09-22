from aiogram import Router

from . import (admin, alphabet, convert, documents, group, inline, photo,
               settings, start)


def build_router() -> Router:
    root = Router(name="root")
    root.include_routers(
        start.router,
        alphabet.router,
        settings.router,
        admin.router,
        group.router,
        documents.router,
        photo.router,
        inline.router,
        convert.router,   # eng oxirida: qolgan barça matnlar
    )
    return root
