#!/usr/bin/env python3
"""Produce a review sheet per language for first-language speakers.

    python scripts/make_review_pack.py

Writes docs/review/<lang>.md — one file per machine-translated language, each
self-contained so it can be sent to one person without them needing the repo,
the app, or any context about how it was built.

Why this exists: nine languages of machine output that nobody on the project
can read is not a caveat you can leave in a README. It is a task. This turns it
into one that takes a reviewer roughly twenty minutes instead of a day.

The sheet asks for three things, in descending order of how much damage a
mistake does:

  1. The five legal terms. Round-trip testing showed "plaintiff" coming back as
     "defendant" in isiZulu and "prosecutor" in three others — a party reversal
     and a civil/criminal category error. Getting these right matters more than
     every other string combined.
  2. The disclaimer, checked word by word. Xitsonga's round-trips as "Willa
     WAS a lawyer".
  3. Everything else, skimmed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config                       # noqa: E402
from app.i18n import STRINGS, BY_CODE        # noqa: E402
from app.verify_translation import tier_for  # noqa: E402

OUT_DIR = config.ROOT / "docs" / "review"

# The terms where a wrong answer changes what the document means, not just how
# it reads. Each carries the English definition so a reviewer who is not a
# lawyer can still answer.
TERMS = [
    ("plaintiff",
     "The person bringing the claim — the one who is owed money and who writes "
     "the letter."),
    ("defendant",
     "The person or business being claimed against — the one who owes the money."),
    ("letter of demand",
     "The formal written request for payment that must be delivered before a "
     "summons can be issued."),
    ("commissioner",
     "The official who presides over a Small Claims Court hearing. Not a "
     "magistrate and not a judge."),
    ("Small Claims Court",
     "The court itself. Willa currently leaves this in English on the theory "
     "that it matches the sign on the building — tell us if that is wrong."),
]

# Strings where an error is dangerous rather than merely awkward.
CRITICAL_KEYS = [
    "disclaimer", "print_footer", "notice_days", "mt_banner",
    "explain_note", "review_hint", "local_badge",
]

KNOWN_ISSUES = {
    "ts": [
        "The disclaimer round-trips into English as **\"Willa WAS a lawyer\"** "
        "instead of \"Willa is not a lawyer\". Please check the negation "
        "carefully — this is the sentence that says Willa is not giving legal "
        "advice, so losing the \"not\" reverses something important.",
    ],
    "zu": [
        "\"Plaintiff\" round-trips as **\"defendant\"** — the two parties may "
        "have been swapped. Please check the term question below first.",
    ],
    "xh": [
        "\"Plaintiff\" round-trips as **\"prosecutor\"**, which is criminal-law "
        "language. This is a civil matter — nobody is being prosecuted.",
        "`your_email` renders \"optional\" as *engacwangciswanga*, which may "
        "read closer to \"unconfigured\".",
        "`notice_days` appears to say \"to pay or to pay\" — the English is "
        "\"pay or settle\".",
        "`pending_title` may be first person (\"I will come soon\") where it "
        "should be \"coming shortly\".",
    ],
    "st": [
        "\"Plaintiff\" round-trips as **\"prosecutor\"** — criminal-law "
        "language for a civil matter.",
    ],
}


def sheet(code: str, mt: dict[str, str]) -> str:
    lang = BY_CODE[code]
    english = STRINGS["en"]
    tier = tier_for(code)

    lines: list[str] = []
    a = lines.append

    a(f"# Willa — {lang['endonym']} review")
    a("")
    a(f"**Language:** {lang['name']} ({lang['endonym']}) · `{code}`  ")
    a(f"**Strings to review:** {len(mt)}  ")
    a(f"**Automated confidence:** "
      + ("checked against a second, independent translation model"
         if tier == "independent" else
         "**low** — no independent model covers this language, so automated "
         "checking could not confirm much. Your reading is the only real check."))
    a("")
    a("## What Willa is")
    a("")
    a("Willa helps someone write a **letter of demand** for the South African "
      "Small Claims Court — the formal letter you must send before you can "
      "issue a summons. It runs entirely on the user's own device.")
    a("")
    a("The letter itself is always in English, because that is the language "
      "South African courts keep their record in. Everything you are reviewing "
      "here is the *interface* and a plain-language *explanation* of the "
      "letter, so that someone can understand what they are signing.")
    a("")
    a("All of this text was produced by a translation model. **No first-language "
      "speaker has read it.** That is what we are asking you to do.")
    a("")
    a("---")
    a("")

    if code in KNOWN_ISSUES:
        a("## Please look at these first")
        a("")
        a("Automated checking already flagged these. They may be false alarms.")
        a("")
        for issue in KNOWN_ISSUES[code]:
            a(f"- {issue}")
        a("")
        a("---")
        a("")

    a("## 1. Legal terms  ← most important")
    a("")
    a(f"These five words carry the meaning of the document. If one is wrong, "
      f"the letter can say something its writer did not intend. Please give "
      f"the word you would actually use in {lang['endonym']}.")
    a("")
    a("| English term | What it means | Correct term in "
      f"{lang['endonym']} |")
    a("|---|---|---|")
    for term, meaning in TERMS:
        a(f"| **{term}** | {meaning} | |")
    a("")
    a("---")
    a("")

    a("## 2. Sentences where a mistake is serious")
    a("")
    a("Read these against the English and correct anything that changes the "
      "meaning — especially a missing **not**.")
    a("")
    for key in CRITICAL_KEYS:
        if key not in mt:
            continue
        a(f"### `{key}`")
        a("")
        a(f"**English:** {english[key]}")
        a("")
        a(f"**{lang['endonym']}:** {mt[key]}")
        a("")
        a("**Correction (leave blank if fine):**")
        a("")
        a("> ")
        a("")
    a("---")
    a("")

    a("## 3. Everything else")
    a("")
    a("Skim these. Mark anything that is wrong, confusing, or would sound "
      "strange to someone worried about money. Natural beats literal.")
    a("")
    a(f"| Key | English | {lang['endonym']} | Correction |")
    a("|---|---|---|---|")
    for key, en_text in english.items():
        if key in CRITICAL_KEYS or key not in mt:
            continue
        en_cell = en_text.replace("|", "\\|")
        mt_cell = mt[key].replace("|", "\\|")
        a(f"| `{key}` | {en_cell} | {mt_cell} | |")
    a("")
    a("---")
    a("")
    a("## Tone")
    a("")
    a("The person reading this is usually owed money they need back, and may "
      "be under real pressure. The writing should be plain, calm and "
      "respectful — not officious, not falsely reassuring, and not so formal "
      "that it becomes hard to follow.")
    a("")
    a("If a sentence is technically accurate but sounds wrong coming from a "
      "service meant to help, please say so. That is as useful as a "
      "mistranslation.")
    a("")
    a("## Sending it back")
    a("")
    a("Fill in the blanks and return the file. Corrections go straight into "
      "`data/ui_strings_mt.json`, and rebuilding will not overwrite them.")
    return "\n".join(lines) + "\n"


def main() -> int:
    path = config.DATA_DIR / "ui_strings_mt.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        print(f"No translations at {path}.\nRun: python scripts/build_ui_translations.py")
        return 1
    if not data:
        print(f"{path} is empty. Run scripts/build_ui_translations.py first.")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for code, strings in data.items():
        if code not in BY_CODE:
            continue
        target = OUT_DIR / f"{code}-{BY_CODE[code]['name'].lower()}.md"
        target.write_text(sheet(code, strings), encoding="utf-8")
        written.append((BY_CODE[code]["endonym"], target, len(strings), tier_for(code)))

    print(f"Wrote {len(written)} review sheet(s) to {OUT_DIR}\n")
    for endonym, target, n, tier in written:
        flag = "" if tier == "independent" else "   <- weakest automated checking"
        print(f"  {endonym:12} {n:3} strings  {target.name}{flag}")

    print("\nSend one file per reviewer. Each is self-contained.")
    print("The five legal terms at the top matter more than everything else")
    print("combined — if a reviewer only does that section, it was worth it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
