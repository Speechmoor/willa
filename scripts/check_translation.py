#!/usr/bin/env python3
"""Round-trip every supported language and report what survived.

    python scripts/check_translation.py             # facts + back-translation
    python scripts/check_translation.py --meaning   # adds the model judgement

English goes out and comes back, so the comparison is English to English.

Read the TIER column before the result. "independent" means the reverse leg
used Helsinki Opus-MT, a different lab and architecture from NLLB, so
agreement is real evidence. "mirror" means NLLB translated back to itself,
which can reverse its own mistake and return clean English while the target
text is wrong. A mirror pass is weak; a mirror failure is not.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import warnings
from pathlib import Path

# Transformers repeats a max_length/max_new_tokens notice on every single
# generate() call. With 8 languages x 4 samples x 2 legs that is 64 lines of
# noise around the output you actually need to read.
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
logging.getLogger("transformers").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", module="transformers")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.translate import FLORES                     # noqa: E402
from app.verify_translation import (                 # noqa: E402
    verify, check_meaning, INDEPENDENT_BACK, MIRROR_ONLY,
)

# Chosen so the fact-checking layer has something to bite on: a deadline, an
# amount, a date, and a sentence whose whole point is a legal disclaimer.
SAMPLES = [
    "You must pay within 14 days of receiving this letter.",
    "You are claiming R4 750 for a fridge that stopped working on 2026-03-22.",
    "Willa is not a lawyer and this is not legal advice.",
    "If you do not pay, the plaintiff may take you to the Small Claims Court.",
]


async def main() -> int:
    want_meaning = "--meaning" in sys.argv
    targets = [c for c in FLORES if c != "en"]

    print(f"Independent reverse model : {', '.join(sorted(INDEPENDENT_BACK))}")
    print(f"Mirror only (weak)        : {', '.join(MIRROR_ONLY)}\n")

    failures, weak = 0, 0
    for sample in SAMPLES:
        print("=" * 78)
        print(f"EN  {sample}")
        print("=" * 78)
        for code in targets:
            r = verify(sample, code)
            if r.error:
                print(f"  FAIL  {r.language:11} [{r.tier:11}] {r.error}")
                failures += 1
                continue

            mark = "ok  " if r.ok else "PROB"
            print(f"  {mark}  {r.language:11} [{r.tier:11}] {r.translated}")
            print(f"        {'':11}  {'':13} back: {r.back}")
            for p in r.problems:
                print(f"        ! {p}")
            if not r.ok:
                failures += 1
            elif r.tier == "mirror":
                weak += 1

            if want_meaning and r.ok:
                same, lost = await check_meaning(r)
                if not same:
                    print(f"        ! meaning may have shifted: {lost}")
                    failures += 1
        print()

    print("-" * 78)
    if failures:
        print(f"{failures} check(s) found a problem. Look at those strings first.")
    else:
        print("No broken translations found.")
    print(f"{weak} result(s) passed on mirror evidence only — treat as unconfirmed.")
    print()
    print("What this does NOT tell you: whether the wording is natural, whether the")
    print("register is right for someone in distress, or whether a legal term of art")
    print("landed correctly. Those need a first-language speaker. This narrows what")
    print("you have to ask them about.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
