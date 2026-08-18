#!/usr/bin/env python3
"""Pre-translate the interface strings into the supported languages.

    python scripts/build_ui_translations.py

Writes data/ui_strings_mt.json, which i18n.py loads as a layer between the
hand-written strings and the English fallback. Doing this once at build time
rather than per request keeps the app responsive and, more importantly, makes
the output a file a human can open, read and correct.

Every string is checked for numbers surviving. Anything that fails is left in
English rather than shipped broken, and reported at the end.

Nothing here has been read by a first-language speaker. The file it writes is
explicitly the artefact to hand to reviewers.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import warnings
from pathlib import Path

os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
logging.getLogger("transformers").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", module="transformers")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config                                    # noqa: E402
from app.i18n import STRINGS, LANGUAGES, BY_CODE          # noqa: E402
from app.translate import FLORES, translate, missing_values, TranslationError  # noqa: E402

OUT = config.DATA_DIR / "ui_strings_mt.json"

# Already written by hand; do not machine-translate over them.
HAND_WRITTEN = set(STRINGS.keys())


def main() -> int:
    targets = [
        l["code"] for l in LANGUAGES
        if l["code"] in FLORES and l["code"] not in HAND_WRITTEN
    ]
    if not targets:
        print("Nothing to do — every supported language already has hand-written strings.")
        return 0

    source = STRINGS["en"]
    print(f"Translating {len(source)} interface strings into "
          f"{len(targets)} language(s): {', '.join(targets)}\n")

    # Anything already in the file is kept unless --overwrite is passed. Once a
    # first-language speaker corrects a string, re-running this script must not
    # silently throw their work away and replace it with machine output again.
    overwrite = "--overwrite" in sys.argv
    existing: dict[str, dict[str, str]] = {}
    if OUT.exists():
        try:
            existing = json.loads(OUT.read_text(encoding="utf-8"))
        except ValueError:
            print(f"{OUT} is not valid JSON — starting fresh.\n")
    if existing and not overwrite:
        kept = sum(len(v) for v in existing.values())
        print(f"Keeping {kept} existing string(s); only filling gaps.")
        print("Pass --overwrite to regenerate everything.\n")

    out: dict[str, dict[str, str]] = {}
    failures: list[tuple[str, str, str]] = []
    reused = 0

    for code in targets:
        name = BY_CODE[code]["name"]
        print(f"{name} ({code})")
        bucket: dict[str, str] = {}
        prior = existing.get(code, {})
        for key, english in source.items():
            if not overwrite and key in prior:
                bucket[key] = prior[key]
                reused += 1
                continue
            try:
                text = translate(english, code)
            except TranslationError as exc:
                failures.append((code, key, str(exc)))
                continue
            lost = missing_values(english, text)
            if lost:
                # Leave it in English rather than ship a string that lost a
                # number. A UI that says "14 days" in one place and "8 days"
                # in another is worse than one that is partly English.
                failures.append((code, key, f"lost number(s) {lost}"))
                continue
            bucket[key] = text
        out[code] = bucket
        fresh = len(bucket) - sum(1 for k in bucket if not overwrite and k in prior)
        print(f"  {len(bucket)}/{len(source)} present ({fresh} newly translated)\n")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Written to {OUT}")
    if reused:
        print(f"{reused} existing string(s) preserved untouched.")

    if failures:
        print(f"\n{len(failures)} string(s) left in English:")
        for code, key, why in failures:
            print(f"  {code:4} {key:22} {why}")

    print("\nNone of this has been reviewed by a first-language speaker.")
    print("Set TRANSLATION_AVAILABLE = True in app/config.py to enable these")
    print("languages, and treat the file above as a draft for review.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
