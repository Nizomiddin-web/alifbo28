#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-./.venv/bin/python}
fail=0
for f in tests/test_converter.py tests/test_alphabet.py tests/test_regress.py tests/test_db.py tests/test_broadcast.py tests/test_bot.py tests/test_handlers.py; do
  echo "=============== $f"
  "$PY" "$f" || fail=1
done
echo
if [ $fail -eq 0 ]; then echo "BARCA TESTLAR OTDI"; else echo "Ayrim testlar yiqildi"; fi
exit $fail
