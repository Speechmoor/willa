#!/usr/bin/env python3
"""Pull dated Small Claims Court notices into a local file.

    python scripts/fetch_notices.py

Writes data/notices.json, read by the landing page ticker. Run it while
online; everything after that works offline.

Cached rather than fetched on page load, for the same reason as the reference
pages: a live request would disclose to a third party that a particular person
is preparing a claim. The file records when it was fetched so staleness is
visible.

It collects dated statutory notices rather than news, because those are what
change what a claimant may do.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config  # noqa: E402

SOURCE = "https://www.justice.gov.za/scc/scc.htm"
OUT = config.DATA_DIR / "notices.json"
UA = "Willa-POC/0.1 (legal aid research tool; contact: local)"

# Lines worth showing a claimant. Each pattern pulls a dated item out of the
# page; anything undated is skipped, because a notice you cannot date is a
# notice you cannot judge the currency of.
PATTERNS = [
    (re.compile(r"amount not exceeding\s*\**R\s?([\d\s]+)\**", re.I),
     lambda m: f"The Small Claims Court limit is now R{m.group(1).strip()}."),
    (re.compile(r"Determine R\s?([\d\s]+) to be the amount[^,]*,\s*(GG [\d]+)[^,]*,\s*(\d+ \w+ \d{4})", re.I),
     lambda m: f"Limit set to R{m.group(1).strip()} — {m.group(2)}, {m.group(3)}."),
    (re.compile(r"(Fees and travelling expenses of sheriffs)[^,]*,\s*(GG [\d]+)[^,]*?(\d{1,2} \w+ \d{4})", re.I),
     lambda m: f"Sheriff fees amended — {m.group(2)}, {m.group(3)}."),
]

# Facts from the page that do not change often but are worth repeating,
# because they are the things people most often do not know.
STANDING = [
    "You do not need a lawyer in the Small Claims Court.",
    "All official languages may be used in a Small Claims Court.",
    "The clerk of the court assists members of the public free of charge.",
    "A letter of demand gives the other side 14 days to pay or settle.",
]


def main() -> int:
    print(f"Fetching {SOURCE}\n")
    try:
        req = urllib.request.Request(SOURCE, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=45) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001
        print(f"Failed: {type(exc).__name__}: {exc}")
        print("The ticker will fall back to the standing notices below.")
        html = ""

    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)

    found: list[str] = []
    for pattern, render in PATTERNS:
        m = pattern.search(text)
        if m:
            line = render(m)
            if line not in found:
                found.append(line)
                print(f"  + {line}")

    if not found:
        print("  (nothing matched — page structure may have changed)")

    payload = {
        "fetched": date.today().isoformat(),
        "source": SOURCE,
        "notices": found + STANDING,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n{len(payload['notices'])} line(s) written to {OUT}")
    print("\nThis file is a snapshot, not a feed. Re-run it before a release —")
    print("the monetary limit changed on 1 August 2026 and nothing noticed for")
    print("two weeks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
