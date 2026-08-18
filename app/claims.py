"""Append-only, hash-linked claim ledger.

    from app import claims
    rec = claims.append("claim-id", {...})
    claims.latest("claim-id")
    claims.verify()

Records are never modified or deleted; editing a claim appends a new version
with the same claim_id. Each record carries the SHA-256 of the record before
it, so verify() can recompute the chain and report the first line that no
longer matches.

This is tamper-evident, not immutable. It is one file on one machine with no
distribution and no consensus, and anyone with write access can edit it. The
chain only guarantees that doing so is detectable.

Stored as JSONL so a partial write damages one line rather than the file, and
so appending does not require rewriting the whole document.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from typing import Any

from app import config

GENESIS = "0" * 64


class ClaimsDisabled(RuntimeError):
    """Raised when the store is used while CLAIMS_STORE_ENABLED is False."""


def _require_enabled() -> None:
    if not config.CLAIMS_STORE_ENABLED:
        raise ClaimsDisabled(
            "The claims store is off. Set CLAIMS_STORE_ENABLED = True in "
            "app/config.py to turn it on, and read the comment above it "
            "first — it changes what Willa guarantees about your data."
        )


def _digest(seq: int, ts: str, prev: str, claim_id: str, body: Any) -> str:
    """Hash over everything that identifies the record.

    sort_keys and the compact separators matter more than they look: without
    them the same claim hashes differently depending on dict ordering or the
    whitespace json chose, and the chain would break on a re-serialisation
    that changed nothing. separators avoids the default ", " / ": ".
    """
    payload = json.dumps(
        {"seq": seq, "ts": ts, "prev": prev, "claim_id": claim_id, "claim": body},
        sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _read_lines() -> list[dict]:
    path = config.CLAIMS_PATH
    if not path.exists():
        return []
    out: list[dict] = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except ValueError:
            # A torn line is data loss, not a reason to hide the rest. Record
            # it as a broken record so verify() reports it instead of the
            # ledger silently appearing one entry shorter than it is.
            out.append({"_unreadable": True, "_line": n, "_raw": line[:200]})
    return out


def _tip() -> tuple[int, str]:
    """Sequence number and hash of the last good record."""
    records = [r for r in _read_lines() if not r.get("_unreadable")]
    if not records:
        return 0, GENESIS
    last = records[-1]
    return int(last.get("seq", len(records))), str(last.get("hash", GENESIS))


def append(claim_id: str, body: dict) -> dict:
    """Add a version of a claim. Returns the record written."""
    _require_enabled()
    seq, prev = _tip()
    seq += 1
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rec = {
        "seq": seq,
        "ts": ts,
        "prev_hash": prev,
        "claim_id": claim_id,
        "claim": body,
        "hash": _digest(seq, ts, prev, claim_id, body),
    }

    config.CLAIMS_PATH.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(rec, ensure_ascii=False) + "\n"
    # Append and fsync. Without the flush+fsync a crash can leave the record
    # in the OS buffer, and the next append would chain onto a hash that is
    # not actually on disk — producing a ledger that fails its own
    # verification through no tampering at all.
    with open(config.CLAIMS_PATH, "a", encoding="utf-8") as fh:
        fh.write(line)
        fh.flush()
        os.fsync(fh.fileno())
    return rec


def history(claim_id: str) -> list[dict]:
    """Every version of one claim, oldest first."""
    _require_enabled()
    return [r for r in _read_lines()
            if not r.get("_unreadable") and r.get("claim_id") == claim_id]


def latest(claim_id: str) -> dict | None:
    """The most recent version of one claim."""
    versions = history(claim_id)
    return versions[-1] if versions else None


def index() -> list[dict]:
    """One entry per claim: its id, its current version, and when it changed.

    Enough to render a list to choose from, without loading every version of
    every claim into the response.
    """
    _require_enabled()
    seen: dict[str, dict] = {}
    for r in _read_lines():
        if r.get("_unreadable"):
            continue
        cid = r.get("claim_id")
        if not cid:
            continue
        entry = seen.setdefault(cid, {"claim_id": cid, "versions": 0})
        entry["versions"] += 1
        entry["updated"] = r.get("ts")
        entry["seq"] = r.get("seq")
        claim = r.get("claim") or {}
        # A label to recognise it by. Falls back through the fields most
        # likely to be filled in early, then to the id itself.
        entry["label"] = (
            claim.get("other_name")
            or claim.get("claim_basis", "")[:60]
            or cid
        )
        entry["amount"] = claim.get("amount", "")
    return sorted(seen.values(), key=lambda e: e.get("seq") or 0, reverse=True)


def verify() -> dict:
    """Walk the chain. Report the first place it breaks, if anywhere."""
    _require_enabled()
    records = _read_lines()
    prev = GENESIS
    expected_seq = 0
    problems: list[dict] = []

    for i, r in enumerate(records, 1):
        if r.get("_unreadable"):
            problems.append({"record": i, "problem": "line could not be parsed"})
            # The chain cannot continue past a line whose hash is unknown.
            break

        expected_seq += 1
        if r.get("seq") != expected_seq:
            problems.append({"record": i, "problem":
                             f"sequence is {r.get('seq')}, expected {expected_seq}"})
        if r.get("prev_hash") != prev:
            problems.append({"record": i, "problem":
                             "prev_hash does not match the record before it"})
        recomputed = _digest(r.get("seq"), r.get("ts"), r.get("prev_hash"),
                             r.get("claim_id"), r.get("claim"))
        if recomputed != r.get("hash"):
            problems.append({"record": i, "problem":
                             "contents do not match the stored hash"})
        if problems:
            break
        prev = r["hash"]

    return {
        "records": len(records),
        "intact": not problems,
        "problems": problems,
        "tip": prev,
    }
