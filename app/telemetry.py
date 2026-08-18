"""Local, redacting logger.

Logs the shape of what happened and never the substance: lengths, counts,
timings, scores, chunk ids, error types and tracebacks. Any value that could
have come from the claim form is reduced to a length or a hash before it is
written, because Willa must not write user input to disk.

The log is local, gitignored, and safe to attach to a bug report.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from contextlib import contextmanager
from logging.handlers import RotatingFileHandler
from pathlib import Path

from . import config

LOG_DIR = config.ROOT / "logs"
LOG_PATH = LOG_DIR / "willa.log"

# Fields that carry user content. Never logged as text.
_SENSITIVE = {
    "claim_basis", "your_name", "your_surname", "your_address", "your_email",
    "your_phone", "other_name", "other_surname", "other_address",
    "other_email", "other_phone", "amount", "admitted_debt",
    "agreement_date", "failure_date", "letter", "explanation",
    "id_number", "plaintiff_full_name", "plaintiff_address",
    "delivery_date", "delivery_time", "recipient_name", "delivery_place",
    "other_method",
}

# The only things safe to log verbatim: values Willa itself chose, never a
# value a user typed. Everything else is reduced to its shape.
_NON_IDENTIFYING = {
    "language", "today", "lang", "model", "thinking", "method", "tier",
    "ok", "n", "chars", "ms", "reason", "to", "problems", "missing",
    "letter_len", "issues", "high", "statutory", "points", "evidence",
    "index", "ollama", "detail",
}

# Patterns scrubbed from any free text that does slip through, e.g. a traceback
# that happens to quote an input.
_SCRUB = [
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"), "<email>"),
    (re.compile(r"\bR\s?\d[\d ,.]*\b"), "<amount>"),
    (re.compile(r"\b\d{4}-\d{2}-\d{2}\b"), "<date>"),
    (re.compile(r"\b\d{6}\s?\d{4}\s?\d{2}\s?\d\b"), "<id-number>"),
    (re.compile(r"\b(?:\+27|0)\d{9}\b"), "<phone>"),
]

_log = logging.getLogger("willa")


def _setup() -> None:
    if _log.handlers:
        return
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(LOG_PATH, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s %(message)s"))
    _log.addHandler(handler)
    _log.setLevel(logging.INFO)
    _log.propagate = False


_setup()


def scrub(text: str) -> str:
    """Strip anything that looks like personal detail from free text."""
    out = str(text)
    for pattern, replacement in _SCRUB:
        out = pattern.sub(replacement, out)
    return out


def fingerprint(value: str) -> str:
    """Stable short hash, so the same input can be recognised across runs
    without the value itself ever being recoverable from the log."""
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:10]


def safe(payload: dict) -> dict:
    """Reduce a payload to its shape, denying by default.

    Anything not on the small non-identifying allowlist is treated as user
    content, whether or not this module has heard of it. A new form field can
    therefore never leak by being forgotten — the failure mode becomes an
    over-redacted log, which is recoverable, rather than someone's ID number
    in a file, which is not.
    """
    out: dict = {}
    for key, value in payload.items():
        if key in _NON_IDENTIFYING and not isinstance(value, (dict, list)):
            out[key] = value
            continue
        if isinstance(value, bool) or value is None:
            out[key] = value
            continue
        text = str(value or "")
        out[key] = {"len": len(text), "set": bool(text.strip())}
        if key == "claim_basis" and text.strip():
            out[key]["fp"] = fingerprint(text)
    return out


def event(name: str, **fields) -> None:
    _log.info("%s %s", name, json.dumps(fields, default=str, ensure_ascii=False))


def failure(name: str, exc: BaseException, **fields) -> None:
    import traceback
    _log.error(
        "%s %s\n%s",
        name,
        json.dumps({**fields, "error": type(exc).__name__, "message": scrub(str(exc))},
                   default=str, ensure_ascii=False),
        scrub("".join(traceback.format_exception(exc))),
    )


@contextmanager
def timed(name: str, **fields):
    """Log how long a stage took, and log it even when the stage explodes.

    A draft that takes 90 seconds and one that fails after 90 seconds look
    identical to a user watching a spinner; they should not look identical in
    the log.
    """
    start = time.perf_counter()
    try:
        yield
    except BaseException as exc:
        failure(f"{name}.failed", exc, ms=round((time.perf_counter()-start)*1000), **fields)
        raise
    else:
        event(f"{name}.ok", ms=round((time.perf_counter()-start)*1000), **fields)


def log_retrieval(results: list[dict]) -> None:
    """Which passages grounded the letter, and how confidently.

    This is the one that would have caught s29 being absent from every draft
    for three rounds — no exception was ever raised, the letters simply were
    not grounded in the governing section.
    """
    event("retrieval", n=len(results), hits=[
        {"id": r.get("id"), "src": r.get("source"), "cite": r.get("citation"),
         "score": round(float(r.get("score", 0)), 3)}
        for r in results
    ])
