"""Buyruq qatori: python -m yozuv [-t yangi|eski|kirill] "matn"  (yoki stdin)."""
from __future__ import annotations

import argparse
import sys

from . import Target, convert, detect, options_from
from .tables import alphabet_table, examples_text, letter_note


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="yozuv", description="Özbek alifbolari ötkazgiçi")
    p.add_argument("text", nargs="*", help="matn (bö'ş bö'lsa stdin öqiladi)")
    p.add_argument("-t", "--target", default="yangi",
                   choices=[t.value for t in Target], help="maqsadli yozuv")
    p.add_argument("--no-smart", action="store_true", help="havola/@username ni ham ötkaziş")
    p.add_argument("--no-foreign", action="store_true", help="xorijiy sözlarni ham ötkaziş")
    p.add_argument("-d", "--detect", action="store_true", help="faqat yozuvni aniqlaş")
    p.add_argument("--alifbo", action="store_true", help="rasmiy alifbo jadvali")
    p.add_argument("--misol", action="store_true", help="misol sözlar")
    a = p.parse_args(argv)

    if a.alifbo:
        print(alphabet_table()); print(); print(letter_note())
        return 0
    if a.misol:
        print(examples_text())
        return 0

    text = " ".join(a.text) if a.text else sys.stdin.read()
    if a.detect:
        print(detect(text).value)
        return 0
    opts = options_from(smart_links=not a.no_smart, keep_foreign=not a.no_foreign)
    sys.stdout.write(convert(text, a.target, opts).text)
    if a.text:
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
