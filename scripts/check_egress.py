#!/usr/bin/env python3
"""Verify Willa makes no network calls except to loopback.

    python scripts/check_egress.py

This monkey-patches the socket layer, runs a full draft end to end, and fails
if anything tries to connect off-device. It is the executable version of the
claim in the project charter, so it should run in CI before any release.
"""

from __future__ import annotations

import asyncio
import socket
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

VIOLATIONS: list[str] = []
_real_connect = socket.socket.connect
_real_getaddrinfo = socket.getaddrinfo

LOOPBACK = {"127.0.0.1", "::1", "localhost"}


def _guarded_connect(self, address):  # type: ignore[no-untyped-def]
    host = address[0] if isinstance(address, tuple) else str(address)
    if host not in LOOPBACK:
        VIOLATIONS.append(f"connect({host})")
    return _real_connect(self, address)


def _guarded_getaddrinfo(host, *args, **kwargs):  # type: ignore[no-untyped-def]
    if host not in LOOPBACK:
        VIOLATIONS.append(f"dns({host})")
    return _real_getaddrinfo(host, *args, **kwargs)


socket.socket.connect = _guarded_connect  # type: ignore[method-assign]
socket.getaddrinfo = _guarded_getaddrinfo  # type: ignore[assignment]

SAMPLE = {
    "language": "en",
    "your_name": "Thandi",
    "your_surname": "Mokoena",
    "your_address": "14 Sisulu Street, Soweto, 1804",
    "your_email": "",
    "other_name": "Blue Sky Appliances",
    "other_surname": "",
    "other_address": "220 Main Reef Road, Roodepoort, 1724",
    "other_email": "",
    "amount": "4750",
    # Deliberately different: purchase on the 11th, failure days after
    # delivery on the 18th. The claim arose on failure, not on purchase, and
    # an earlier build silently used the purchase date.
    "agreement_date": "2026-03-11",
    "failure_date": "2026-03-22",
    "claim_basis": (
        "I paid R4750 cash for a fridge on 11 March 2026. It was delivered on "
        "18 March and stopped cooling after four days. I phoned the shop twice "
        "and went in once. They said the warranty does not cover it. I want my "
        "money back."
    ),
}


async def main() -> int:
    from app.main import draft, DraftRequest  # noqa: E402

    print("Running a full draft with the socket layer under guard…\n")
    try:
        result = await draft(DraftRequest(**SAMPLE))
    except Exception as exc:  # noqa: BLE001
        print(f"Draft failed: {type(exc).__name__}: {exc}")
        print("(If Ollama is not running, start it and retry.)")
        return 2

    import json
    body = json.loads(result.body)

    print("=" * 68)
    print(body["letter"])
    print("=" * 68)
    print("\nRetrieved:")
    for s in body["sources"]:
        print(f"  [{s['n']}] {s['source']} {s['citation']} (score {s['score']})")
    print("\nChecker flagged:")
    for i in body["issues"] or []:
        print(f"  {i.get('severity')}: {i.get('issue')}")
    if not body["issues"]:
        print("  nothing")

    print("\n" + "-" * 68)
    offsite = sorted(set(VIOLATIONS))
    if offsite:
        print(f"FAIL — {len(offsite)} off-device call(s):")
        for v in offsite:
            print(f"  {v}")
        return 1
    print("PASS — no connections left the device.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
