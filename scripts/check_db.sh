#!/usr/bin/env bash
# Baza ulanişini va jadvallarni tekşiradi.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-./.venv/bin/python}
"$PY" -m bot.db --show
"$PY" - <<'PYEOF'
import asyncio
from sqlalchemy import text
from bot import db

async def main():
    await db.init()
    async with db.engine().connect() as conn:
        one = (await conn.execute(text("SELECT 1"))).scalar_one()
        print("ulaniş:", "OK" if one == 1 else "XATO")
    print("statistika:", await db.stats())
    await db.close()

asyncio.run(main())
PYEOF
