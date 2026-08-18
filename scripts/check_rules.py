#!/usr/bin/env python3
"""Exercise the statutory jurisdiction checks.

    python scripts/check_rules.py           # instant, no model
    python scripts/check_rules.py --full    # through the whole pipeline, slow

The checks in app/checks.py are pure functions over the form fields. Testing
them does not need Ollama, and the first version of this script called the
model ten times to verify logic that runs in microseconds. Default is now the
fast path; --full exists only for when you want to see the rendered letter
alongside the warnings.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

BASE = {
    "language": "en",
    "your_name": "Thandi", "your_surname": "Mokoena",
    "your_address": "14 Sisulu Street, Soweto, 1804", "your_email": "",
    "other_name": "Blue Sky Appliances", "other_surname": "",
    "other_address": "220 Main Reef Road, Roodepoort, 1724", "other_email": "",
    "amount": "4750",
    "agreement_date": "2026-03-11", "failure_date": "2026-03-22",
    "claim_basis": "I paid R4750 for a fridge. It stopped cooling four days after delivery.",
}

# (label, overrides, citations that must appear, citations that must NOT)
CASES: list[tuple[str, dict, list[str], list[str]]] = [
    ("clean baseline", {}, [], ["s7(1)", "s15", "s16"]),

    ("company as plaintiff",
     {"your_name": "Mokoena Trading (Pty) Ltd", "your_surname": ""}, ["s7(1)"], []),
    ("close corporation as plaintiff",
     {"your_name": "Sisulu Motors", "your_surname": "CC"}, ["s7(1)"], []),
    ("person whose surname starts with a company word",
     {"your_name": "Ltdiwe", "your_surname": "Nkosi"}, [], ["s7(1)"]),

    ("R35 000, over the ceiling", {"amount": "35000"}, ["s15"], []),
    ("R28 000, under the new R30k limit", {"amount": "28000"}, [], ["s15"]),
    ("R30 000 exactly, at the ceiling", {"amount": "30000"}, [], ["s15"]),
    ("R29 999.99, under", {"amount": "29999.99"}, [], ["s15"]),
    # SA convention: space groups thousands, comma marks the decimal. These
    # exist because stripping to digits-and-dots read "R 45 000,00" as four
    # and a half million — harmless as a warning, a wrongly refused claimant
    # now that the check blocks.
    ("R45 000,00 — SA spacing and comma decimal", {"amount": "R 45 000,00"},
     ["s15"], []),
    ("R29 999,50 — comma decimal, just under", {"amount": "R 29 999,50"},
     [], ["s15"]),
    ("R30 000,00 — comma decimal, exactly at", {"amount": "R30 000,00"},
     [], ["s15"]),
    ("R30,000.00 — US grouping, exactly at", {"amount": "R30,000.00"},
     [], ["s15"]),
    ("R4 500 000,00 — genuinely millions", {"amount": "R4 500 000,00"},
     ["s15"], []),

    ("defamation", {"claim_basis": "My neighbour defamed me on Facebook."}, ["s16(f)"], []),
    ("wrongful arrest", {"claim_basis": "The police wrongfully arrested me."}, ["s16(f)"], []),
    ("interdict", {"claim_basis": "I want an interdict to stop him."}, ["s16(g)"], []),
    ("divorce", {"claim_basis": "I want a divorce from my husband."}, ["s16(a)"], []),

    # Completeness (rule 7(1)). Runs before the jurisdiction checks, so an
    # empty form is told what it is missing rather than that its blank amount
    # is over the ceiling.
    ("no amount given", {"amount": ""}, ["rule 7(1)"], ["s15"]),
    ("no date it went wrong", {"failure_date": ""}, ["rule 7(1)"], []),
    ("no surname", {"your_surname": ""}, ["rule 7(1)"], []),
    ("no address for the other party", {"other_address": ""}, ["rule 7(1)"], []),
    ("e-mails blank — optional, delivery is by post",
     {"your_email": "", "other_email": ""}, [], ["rule 7(1)"]),
    ("other party has no surname — a shop does not",
     {"other_surname": ""}, [], ["rule 7(1)"]),
    ("no purchase date — rule 7(1) asks only when the claim arose",
     {"agreement_date": ""}, [], ["rule 7(1)"]),
    ("incomplete AND over the ceiling — completeness speaks first",
     {"amount": "", "claim_basis": ""}, ["rule 7(1)"], ["s15", "s16"]),

    # A surname is supplied so this exercises the three jurisdiction rules
    # rather than being caught by the completeness check first.
    ("all three at once",
     {"your_name": "Mokoena Trading (Pty) Ltd", "your_surname": "Holdings",
      "amount": "35000",
      "claim_basis": "They failed to deliver stock we paid for and then defamed us "
                     "to other suppliers."},
     ["s7(1)", "s15", "s16"], []),
]


def fast() -> int:
    from app.checks import jurisdiction_issues, blocking_issues, dedupe

    failures = 0
    for label, override, expect, forbid in CASES:
        facts = {**BASE, **override}
        blocked = blocking_issues(facts)
        # The completeness check lives in blocking_issues rather than in
        # jurisdiction_issues — it is about rule 7(1), not about the court's power
        # — so searching only the latter would never see rule 7(1) and every
        # completeness case would read as a silent pass.
        issues = dedupe(blocked + jurisdiction_issues(facts))
        blob = json.dumps(issues)
        missing = [c for c in expect if c not in blob]
        spurious = [c for c in forbid if c in blob]

        # A citation that fires must also refuse the draft, and a case with no
        # citation must not.
        should_block = bool(expect)
        gate_wrong = bool(blocked) != should_block
        no_remedy = [i["where"] for i in blocked if not i.get("remedy")]

        ok = not missing and not spurious and not gate_wrong and not no_remedy
        failures += not ok
        state = "REFUSED " if blocked else "drafts  "
        print(f"{'ok  ' if ok else 'FAIL'} {label:44} {state} {len(issues)} issue(s)")
        for i in issues:
            print(f"       [{i['severity']}{'/blocks' if i.get('blocks') else ''}]"
                  f" {i['where']}")
        if missing:
            print(f"       EXPECTED, ABSENT: {missing}")
        if spurious:
            print(f"       SHOULD NOT FIRE: {spurious}")
        if gate_wrong:
            print(f"       GATE WRONG: expected {'a refusal' if should_block else 'a draft'}")
        if no_remedy:
            print(f"       BLOCKS WITH NO WAY FORWARD: {no_remedy}")

    print("-" * 72)
    print("All statutory checks behave as expected." if not failures
          else f"{failures} case(s) wrong.")
    print("\nEvery refusal carries a remedy. Read those wordings as a claimant")
    print("would: the s16 screen matches on words and can fire on a passing")
    print("mention, so the correction it offers has to be usable.")
    return 1 if failures else 0


async def full() -> int:
    from app.main import draft, DraftRequest

    for label, override, expect, _ in CASES:
        if not expect and label != "clean baseline":
            continue                      # only the interesting ones; each is slow
        facts = {**BASE, **override}
        print("=" * 72, f"\n{label}\n", "=" * 72, sep="")
        try:
            body = json.loads((await draft(DraftRequest(**facts))).body)
        except Exception as exc:  # noqa: BLE001
            print(f"  FAILED: {type(exc).__name__}: {exc}\n  (Is Ollama running?)")
            return 2
        print(body["letter"])
        print("-" * 40)
        for i in body["issues"] or [{"severity": "-", "issue": "no issues"}]:
            print(f"  [{i.get('severity')}] {i.get('issue')}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(full()) if "--full" in sys.argv else fast())
