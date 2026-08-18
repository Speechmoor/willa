#!/usr/bin/env python3
"""One-time corpus download.

Run this once, on a connected machine, before going offline. Everything after
this point — embedding, retrieval, drafting — is local.

    python scripts/fetch_corpus.py

Every URL below was verified reachable on 2026-08-12. All are statutory public
law published by the South African government or by SAFLII, so there is no
licensing obstacle to indexing them (P2-01 licensing check).

If a URL has rotted, the script tells you which one and keeps going. Drop a
replacement PDF into corpus/ by hand and re-run scripts/ingest.py — the
ingester reads whatever is in the folder, it does not depend on this script.
"""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus"

# (filename, [urls tried in order], why it matters) gov.za is slow and
# intermittently times out, so anything hosted there has a SAFLII mirror
# listed after it.
SOURCES: list[tuple[str, list[str], str]] = [
    (
        "Small_Claims_Courts_Act_61_of_1984.pdf",
        [
            "https://www.justice.gov.za/legislation/acts/1984-061.pdf",
            "https://media.lawlibrary.org.za/media/legislation/325285/source_file/1984-061.pdf",
        ],
        "The Act itself. s29(1) is the letter of demand; s7/s14-16 govern "
        "jurisdiction, who may sue, and what is excluded.",
    ),
    (
        "Small_Claims_Courts_Rules.pdf",
        [
            # LawLibrary / Laws.Africa consolidation of GN R2573 of 2022, amendments
            # applied, CC BY 4.0, no copyright on the legislative text.
            "https://media.lawlibrary.org.za/media/legislation/325286/source_file/0bed150a2ed6ac58/2022-r2573.pdf",
            "https://sheriffs.org.za/wp-content/uploads/2025/03/Small-Claims-Court-Rules-amended-7-Oct-2022.pdf",
            # Original gazette. Authoritative but gov.za times out often.
            "https://www.gov.za/sites/default/files/gcis_document/202210/47254reg11497gon2573.pdf",
        ],
        "Rules Regulating Matters in Respect of Small Claims Courts. "
        "Rule 7 covers the demand and proof of delivery, and Annexure 1 "
        "carries the official forms.",
    ),
    (
        "Consumer_Protection_Act_68_of_2008.pdf",
        ["https://www.thedtic.gov.za/wp-content/uploads/Consumer_Protection_Act.pdf"],
        "CPA 68 of 2008, published by the dtic. Relevant where the claim is "
        "a consumer transaction — defective goods, services not rendered.",
    ),
    (
        "Form_J993_Letter_of_Demand.pdf",
        ["https://www.justice.gov.za/forms/scc/scc_J993-Form04.pdf"],
        "Form 4. The document Willa is drafting. A plain-text transcription "
        "already lives in data/forms/ and is what the prompt uses, so this "
        "PDF failing is not fatal.",
    ),
    (
        "Form_J994_Affidavit_rule_7_2.pdf",
        ["https://www.justice.gov.za/forms/scc/scc_J994-Form05.pdf"],
        "Form 5. Affidavit proving personal delivery of the demand.",
    ),
]

UA = "Willa-POC/0.1 (legal aid research tool; contact: local)"


TIMEOUT = 45  # gov.za is slow; fail over to the mirror rather than hang


def fetch(name: str, urls: list[str]) -> bool:
    dest = CORPUS / name
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  = {name} (already present, {dest.stat().st_size // 1024} KB)")
        return True

    for n, url in enumerate(urls, 1):
        label = "" if len(urls) == 1 else f" [source {n}/{len(urls)}]"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                data = resp.read()
        except Exception as exc:  # noqa: BLE001 - try the next mirror
            print(f"  ~ {type(exc).__name__}{label}: {url}")
            continue
        if len(data) < 2000:
            print(f"  ~ suspiciously small, {len(data)} bytes{label}: {url}")
            continue
        if not data.startswith(b"%PDF"):
            print(f"  ~ not a PDF, probably an error page{label}: {url}")
            continue
        dest.write_bytes(data)
        print(f"  + {name} ({len(data) // 1024} KB)")
        return True

    print(f"  ! {name} FAILED — all {len(urls)} source(s) unreachable.")
    print("    Download by hand into corpus/ from any of:")
    for url in urls:
        print(f"      {url}")
    return False


def write_manifest() -> None:
    """Record what is in corpus/, where it came from, and WHEN IT LAST CHANGED.

    A timestamp alone answers "how old is this?". The more useful question for
    a legal corpus is "did the law move?", and that needs history: the hash of
    every document, every time it has been fetched, kept across runs.

    The precedent is the monetary ceiling. R20,000 was correct when it was
    written down and stopped being correct on 1 August 2026, and nothing in
    the codebase could tell — not because the information was unavailable but
    because nothing was watching. This watches. Re-run the fetch and any
    amended document announces itself, with the date it changed.

    Two files:
      corpus/manifest.json  the record, including full history. Machine-read.
      corpus/MANIFEST.md    the same thing rendered for a human reading the
                            repository on GitHub.
    """
    import hashlib
    import json
    from datetime import date

    today = date.today().isoformat()
    store = CORPUS / "manifest.json"

    try:
        record = json.loads(store.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        record = {"files": {}}

    changed: list[tuple[str, str, str]] = []   # name, old hash, new hash
    added: list[str] = []

    for name, urls, why in SOURCES:
        f = CORPUS / name
        if not f.exists():
            continue
        digest = hashlib.sha256(f.read_bytes()).hexdigest()
        entry = record["files"].get(name)

        if entry is None:
            record["files"][name] = {
                "url": urls[0], "why": why, "sha256": digest,
                "first_seen": today, "last_checked": today,
                "history": [{"date": today, "sha256": digest, "note": "first fetch"}],
            }
            added.append(name)
        elif entry["sha256"] != digest:
            changed.append((name, entry["sha256"], digest))
            entry["history"].append(
                {"date": today, "sha256": digest,
                 "note": f"changed from {entry['sha256'][:16]}"})
            entry["sha256"] = digest
            entry["last_checked"] = today
            entry["url"] = urls[0]
        else:
            entry["last_checked"] = today

    record["last_run"] = today
    store.write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n",
                     encoding="utf-8")

    # ---- the loud part -----------------------------------------------------
    if changed:
        print()
        print("=" * 68)
        print("THE CORPUS CHANGED SINCE THE LAST FETCH")
        print("=" * 68)
        for name, old, new_ in changed:
            hist = record["files"][name]["history"]
            print(f"  {name}")
            print(f"    was {old[:16]}  ->  now {new_[:16]}")
            print(f"    previously fetched {hist[-2]['date']}")
        print()
        print("  Read the new document before trusting anything built from it.")
        print("  Statutory values live in app/config.py — SCC_MONETARY_CEILING_ZAR")
        print("  and DEMAND_NOTICE_DAYS — and they do not update themselves.")
        print("  Then re-run: python scripts/ingest.py")
        print("=" * 68)
    elif added:
        print(f"\n  {len(added)} document(s) recorded for the first time.")
    else:
        print("\n  No document changed since the last fetch.")

    # ---- the readable version ---------------------------------------------
    lines = [
        "# Corpus manifest",
        "",
        "Generated by `scripts/fetch_corpus.py`. These files are committed so the",
        "repository can be cloned and run without network access — they are a",
        "**snapshot**, and South African law changes.",
        "",
        f"Last checked: **{today}**",
        "",
        "| File | First seen | Last changed | Last checked | SHA-256 | Source |",
        "|---|---|---|---|---|---|",
    ]
    for name, urls, _why in SOURCES:
        e = record["files"].get(name)
        if not e:
            lines.append(f"| `{name}` | — | — | — | *missing* | {urls[0]} |")
            continue
        last_change = e["history"][-1]["date"] if len(e["history"]) > 1 else "—"
        lines.append(
            f"| `{name}` | {e['first_seen']} | {last_change} | "
            f"{e['last_checked']} | `{e['sha256'][:16]}` | {e['url']} |")

    moved = [(n, e) for n, e in record["files"].items() if len(e["history"]) > 1]
    if moved:
        lines += ["", "## Changes observed", ""]
        for name, e in moved:
            lines.append(f"**{name}**")
            lines.append("")
            for h in e["history"]:
                lines.append(f"- `{h['date']}` — {h['note']} (`{h['sha256'][:16]}`)")
            lines.append("")
    else:
        lines += ["", "No document has changed since it was first recorded.", ""]

    lines += [
        "## If something here changes",
        "",
        "A changed hash means the published document was amended. Read the new",
        "text before trusting an index built from it, and check the statutory",
        "constants in `app/config.py` — they are set by hand and do not follow",
        "the corpus. The Small Claims Court ceiling moved from R20,000 to",
        "R30,000 on 1 August 2026 and went unnoticed here for eleven days.",
        "",
    ]
    (CORPUS / "MANIFEST.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  Manifest: {CORPUS / 'MANIFEST.md'}\n")


def main() -> int:
    CORPUS.mkdir(parents=True, exist_ok=True)
    print(f"Downloading SA legal corpus into {CORPUS}\n")
    failed: list[str] = []
    for name, urls, why in SOURCES:
        print(f"{name}\n    {why}")
        if not fetch(name, urls):
            failed.append(name)
        print()

    write_manifest()

    ok = len(SOURCES) - len(failed)
    print(f"{ok}/{len(SOURCES)} retrieved.")
    if failed:
        print("\nMissing:")
        for name in failed:
            print(f"  - {name}")
        print("\ningest.py reads whatever is in corpus/ and skips the rest, so")
        print("you can proceed — retrieval just will not cover those documents.")
    if ok == 0:
        print("\nNothing downloaded at all. Check your connection.")
        return 1
    print("\nNext: python scripts/ingest.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
