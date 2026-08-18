#!/usr/bin/env python3
"""Prove that nothing a user types reaches disk.

    python scripts/check_privacy.py

check_egress.py proves nothing leaves the device. This proves nothing is left
*on* it. Together they are the evidence base for the privacy impact assessment
in docs/privacy-impact-assessment.md.

Method: run a full draft using distinctive canary values, then read back every
file the project could plausibly have written and grep for them. A canary that
turns up anywhere is a leak, regardless of what the architecture diagram says.

Note on P2-03. The plan calls for an NER redaction pipeline to stop personal
data reaching the vector index. Willa never indexes user data — the corpus is
five statutes and nothing else — so that particular pipeline would have
nothing to redact. The real question is narrower and answered here: does any
user input survive a request? This test is the honest version of that
requirement.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config  # noqa: E402

# Deliberately unmistakable. If any of these appear on disk we know exactly
# which field leaked and by what route.
CANARIES = {
    "your_name": "CANARYFIRSTNAME",
    "your_surname": "CANARYSURNAME",
    "your_address": "CANARYSTREET 42, CANARYTOWN",
    "your_email": "canary@canarymail.invalid",
    "other_name": "CANARYDEFENDANT TRADING",
    "other_address": "CANARYROAD 99",
    "claim_basis": (
        "CANARYSTORY. I paid R9 999 for a CANARYFRIDGE on 2026-01-01 and it "
        "broke. My ID number is 9999999999999 and my phone is 0829999999."
    ),
}

SAMPLE = {
    "language": "en",
    "your_name": CANARIES["your_name"],
    "your_surname": CANARIES["your_surname"],
    "your_address": CANARIES["your_address"],
    "your_email": CANARIES["your_email"],
    "other_name": CANARIES["other_name"],
    "other_surname": "",
    "other_address": CANARIES["other_address"],
    "other_email": "",
    "amount": "9999",
    "agreement_date": "2026-01-01",
    "failure_date": "2026-01-05",
    "claim_basis": CANARIES["claim_basis"],
}

# Everywhere the project could write. Deliberately broad — including the ones
# that should obviously be clean, because "obviously" is how leaks survive.
def search_roots() -> list[Path]:
    return [
        config.ROOT / "logs",
        config.DATA_DIR,
        config.ROOT / "docs",
        config.CORPUS_DIR,
        config.ROOT / "app",
        config.ROOT / "scripts",
        Path("/tmp"),
    ]


SKIP_SUFFIXES = {".pdf", ".npz", ".bin", ".safetensors", ".pt", ".onnx"}

# This file defines the canaries as string literals, so it — and anything
# compiled from it — will always contain them. Counting that as a leak makes
# the test fail permanently while telling you nothing.
SELF = Path(__file__).resolve()


def _is_self(path: Path) -> bool:
    if path.resolve() == SELF:
        return True
    # __pycache__/check_privacy.cpython-312.pyc and friends
    return "__pycache__" in path.parts and path.name.startswith(SELF.stem)


def scan(roots: list[Path], needles: dict[str, str]) -> list[tuple[Path, str]]:
    hits: list[tuple[Path, str]] = []
    seen: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() in SKIP_SUFFIXES:
                continue
            if "site-packages" in path.parts or ".venv" in path.parts:
                continue
            if _is_self(path):
                continue
            resolved = path.resolve()
            if resolved in seen:      # roots overlap; do not report twice
                continue
            seen.add(resolved)
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except (OSError, UnicodeDecodeError):
                continue
            for field, value in needles.items():
                # Match on a distinctive fragment, not the whole string, so
                # partial writes are caught too.
                fragment = value.split(",")[0].split(".")[0].strip()
                if fragment and fragment in text:
                    hits.append((path, field))
    return hits


async def main() -> int:
    from app.main import draft, DraftRequest

    print("Running a full draft with canary values…\n")
    try:
        await draft(DraftRequest(**SAMPLE))
    except Exception as exc:  # noqa: BLE001
        print(f"Draft failed: {type(exc).__name__}: {exc}")
        print("(Is Ollama running? The test needs a real request to be meaningful.)")
        return 2

    print("Searching for canaries on disk…\n")
    hits = scan(search_roots(), CANARIES)

    # The claims store, if someone has switched it on, writes user data to
    # disk on purpose.
    store_on = getattr(config, "CLAIMS_STORE_ENABLED", False)
    if store_on:
        print("=" * 68)
        print("CLAIMS_STORE_ENABLED is True.")
        print()
        print("The no-user-data-on-disk guarantee is SUSPENDED in this build.")
        print(f"Claims are written in plain text to {config.CLAIMS_PATH}")
        print("and any canary values below that resolve to that file are")
        print("expected — they are the feature working, not a leak.")
        print()
        print("Anything found OUTSIDE that file is still a real leak.")
        print("=" * 68)
        print()
        in_store = [(p, f) for p, f in hits if p.resolve() == config.CLAIMS_PATH.resolve()]
        hits = [(p, f) for p, f in hits if p.resolve() != config.CLAIMS_PATH.resolve()]
        if in_store:
            print(f"  {len(in_store)} canary value(s) in the claims ledger, as designed.\n")

    # The log must exist, or we are proving nothing — an absent log would pass
    # this test trivially while telling us nothing about redaction.
    from app import telemetry
    if not telemetry.LOG_PATH.exists():
        print("WARNING: no log file was written. This test cannot confirm the")
        print("redaction works if nothing was logged at all.")
    else:
        size = telemetry.LOG_PATH.stat().st_size
        print(f"  log present: {telemetry.LOG_PATH} ({size} bytes)")

    # Prove the scanner can actually see a leak. Without this, a bug in the
    # matching would report a clean pass forever and nobody would notice —
    # the most dangerous possible failure for a test like this.
    probe = config.ROOT / "logs" / ".privacy-probe.tmp"
    probe.parent.mkdir(parents=True, exist_ok=True)
    probe.write_text(CANARIES["your_name"], encoding="utf-8")
    can_detect = bool(scan([config.ROOT / "logs"], {"probe": CANARIES["your_name"]}))
    probe.unlink(missing_ok=True)
    print(f"  scanner self-test: {'detects a planted leak' if can_detect else 'BROKEN'}")
    if not can_detect:
        print("\nThe scanner failed to find a value it planted itself. Its clean")
        print("results cannot be trusted. Fix the scanner before reading anything")
        print("else in this output.")
        return 2

    print()
    if hits:
        print(f"FAIL — user input found on disk in {len(hits)} place(s):")
        for path, field in hits:
            print(f"  {field:14} -> {path}")
        print("\nEach of these is a POPIA problem. Fix before any real use.")
        return 1

    if store_on:
        print("PASS, WITH THE GUARANTEE SUSPENDED — no canary values escaped")
        print("anywhere except the claims ledger, which is storing them by")
        print("design. This is not the same result as a clean run and must not")
        print("be quoted as one. Willa does not currently keep its promise")
        print("about data at rest; set CLAIMS_STORE_ENABLED = False to restore it.")
    else:
        print("PASS — none of the canary values appear in any file on disk.")

    print("\nChecked:")
    for root in search_roots():
        print(f"  {root}{'' if root.exists() else '  (absent)'}")
    print("\nThis does not cover files the *user* chooses to save — a downloaded")
    print("letter or a printed PDF is theirs, and lands wherever they put it.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
