#!/usr/bin/env bash
# Barça test töplamini yurgizadi.
#   PY=python ./tests/run_all.sh
# CI da ($GITHUB_ACTIONS) yiqilgan tekşiruvlar annotatsiya sifatida çiqadi —
# şunda jurnalni oçmasdan ham sabab körinadi.
set -uo pipefail
cd "$(dirname "$0")/.."

# Özbek harflari (ö, ğ, ş, ç) ASCII lokalda ham buzilmasdan çiqsin —
# aks holda minimal konteynerlarda UnicodeEncodeError böladi.
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8
PY=${PY:-./.venv/bin/python}
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

fail=0
failed_files=()

for f in tests/test_converter.py tests/test_alphabet.py tests/test_regress.py \
         tests/test_db.py tests/test_broadcast.py tests/test_bot.py \
         tests/test_handlers.py; do
  echo "=============== $f"
  out="$TMP/$(basename "$f").log"
  "$PY" "$f" 2>&1 | tee "$out"
  code=${PIPESTATUS[0]}
  if [ "$code" -ne 0 ]; then
    fail=1
    failed_files+=("$f")
    if [ -n "${GITHUB_ACTIONS:-}" ]; then
      # yiqilgan tekşiruvlar
      grep -E "^\[XATO\]" "$out" | head -10 | while IFS= read -r line; do
        printf '::error file=%s,title=%s::%s\n' "$f" "$(basename "$f")" "${line//$'\n'/ }"
      done
      # traceback bölsa — oxirgi maʼnoli qatori
      if grep -q "Traceback" "$out"; then
        last=$(grep -vE "^\s*(File|\s)" "$out" | tail -3 | tr '\n' ' ')
        printf '::error file=%s,title=%s crash::%s\n' "$f" "$(basename "$f")" "$last"
      fi
      printf '::error file=%s::%s chiqiş kodi %s bilan yiqildi\n' "$f" "$f" "$code"
    fi
  fi
done

echo
if [ $fail -eq 0 ]; then
  echo "BARCA TESTLAR OTDI"
else
  echo "Yiqilgan toplamlar: ${failed_files[*]}"
fi
exit $fail
