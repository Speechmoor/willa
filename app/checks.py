"""Deterministic jurisdiction checks.

Rules with a definite answer are enforced here rather than in the prompt.
Issues use the same shape as the model reviewer, so the UI treats them alike:

    {"severity": "high"|"medium", "issue": str, "where": str,
     "blocks": bool, "remedy": str}

An issue carrying `blocks` stops the draft. No letter is generated and no
model is called. Every blocking issue also carries a `remedy` naming the
correction the claimant can make on the form, so a refusal is never a dead
end and cannot be bypassed by resubmitting.
"""

from __future__ import annotations

import re

from . import config

# Juristic-person markers, matched on word boundaries so "Ltd" does not fire
# inside a surname.
_ENTITY_TOKENS = [
    r"\(?\s*pty\s*\)?\s*ltd", r"\bltd\b", r"\blimited\b", r"\bcc\b",
    r"\bclose corporation\b", r"\bnpc\b", r"\bincorporated\b", r"\binc\b",
    r"\bsoc\b", r"\btrust\b", r"\bpartnership\b", r"\bco-?operative\b",
    r"\bassociation\b", r"\bfoundation\b", r"\bcompany\b", r"\benterprises?\b",
    r"\bholdings\b", r"\bgroup\b", r"\bproprietary\b",
]
_ENTITY_RE = re.compile("|".join(_ENTITY_TOKENS), re.I)

# Matters s16 excludes, matched on both statutory and everyday wording.
_EXCLUDED = [
    (r"\bdefamation\b|\bdefamed\b|\bslander\b|\blibel\b",
     "damages for defamation", "s16(f)(i)"),
    (r"\bmalicious prosecution\b", "damages for malicious prosecution", "s16(f)(ii)"),
    (r"\bwrongful(ly)? (imprison|detain)", "damages for wrongful imprisonment", "s16(f)(iii)"),
    (r"\bwrongful(ly)? arrest", "damages for wrongful arrest", "s16(f)(iv)"),
    (r"\bseduction\b", "damages for seduction", "s16(f)(v)"),
    (r"\bbreach of promise to marry\b|\bjilted\b|\bcalled off (the|our) (wedding|engagement)\b",
     "damages for breach of promise to marry", "s16(f)(vi)"),
    (r"\bdivorce\b|\bdissolution of (the |our )?(marriage|customary union)\b",
     "dissolution of a marriage or customary union", "s16(a)"),
    (r"\bvalidity of (a |the )?will\b|\bcontest(ing)? (a |the )?will\b|\btestamentary\b",
     "the validity or interpretation of a will", "s16(b)"),
    (r"\binterdict\b|\brestraining order\b",
     "an interdict", "s16(g)"),
]


def _money(raw: str) -> float | None:
    """Parse a currency amount in South African or international notation.

    R45 000,00, R45,000.00 and 45000 all parse to the same value. Whichever
    of comma or dot appears last is the decimal separator; the rest is
    grouping. Returns None if no number can be read.
    """
    text = re.sub(r"[^\d.,]", "", str(raw or ""))
    if not text:
        return None

    last_comma, last_dot = text.rfind(","), text.rfind(".")
    if last_comma > last_dot:
        text = text.replace(".", "").replace(",", ".")
    else:
        text = text.replace(",", "")

    # Three digits after a separator means grouping, not a decimal.
    if re.fullmatch(r"\d+\.\d{3}", text):
        text = text.replace(".", "")

    try:
        return float(text)
    except ValueError:
        return None


def jurisdiction_issues(facts: dict) -> list[dict]:
    """Checks that do not depend on the model's judgement."""
    issues: list[dict] = []

    # --- s7(1): only a natural person may institute -------------------------
    plaintiff = f"{facts.get('your_name','')} {facts.get('your_surname','')}".strip()
    if plaintiff and _ENTITY_RE.search(plaintiff):
        issues.append({
            "severity": "high",
            "blocks": True,
            "issue": (
                "The name you gave looks like a company or trust. Only a natural "
                "person may bring a claim in the Small Claims Court — a business "
                "can be sued there but cannot sue. If this debt is owed to a "
                "business, it needs a different court."
            ),
            "remedy": (
                "If you are a person and this is your own name, correct the name "
                "fields to your personal name and Willa will continue."
            ),
            "where": "Small Claims Courts Act 61 of 1984, s7(1)",
        })

    # --- s15: monetary ceiling ---------------------------------------------
    amount = _money(facts.get("amount"))
    if amount is not None and amount > config.SCC_MONETARY_CEILING_ZAR:
        issues.append({
            "severity": "high",
            "blocks": True,
            "issue": (
                f"You are claiming R{amount:,.2f}, which is above the Small Claims "
                f"Court limit of R{config.SCC_MONETARY_CEILING_ZAR:,}. The court "
                f"cannot hear a claim for that amount, so Willa has not written "
                f"the letter."
            ),
            "remedy": (
                f"You may abandon the R{amount - config.SCC_MONETARY_CEILING_ZAR:,.2f} "
                f"above the limit and claim R{config.SCC_MONETARY_CEILING_ZAR:,} "
                f"here — change the amount and Willa will continue. Abandoned "
                f"amounts cannot be recovered later, in this court or any other, "
                f"so if the full amount matters, use a different court instead."
            ),
            "where": f"s15 read with s18; limit set by {config.SCC_CEILING_AUTHORITY}",
        })

    # --- s16: matters beyond jurisdiction -----------------------------------
    story = str(facts.get("claim_basis", "") or "")
    for pattern, label, cite in _EXCLUDED:
        if re.search(pattern, story, re.I):
            issues.append({
                "severity": "high",
                "blocks": True,
                "issue": (
                    f"Your description reads as a claim for {label}. The Small "
                    f"Claims Court has no jurisdiction over that, so Willa has "
                    f"not written the letter."
                ),
                "remedy": (
                    "If that is not what you are claiming for, describe what "
                    "happened without it and Willa will continue. This is matched "
                    "on the words you used, so a passing mention is enough to "
                    "trigger it."
                ),
                "where": f"Small Claims Courts Act 61 of 1984, {cite}",
            })
            break   # one forum issue is enough

    return issues


# Fields required by rule 7(1) and by service under s29(1)/rule 7(2).
# E-mail addresses, the other party's surname and the agreement date stay
# optional: the demand is served by post or by hand, a business has no
# surname, and rule 7(1) asks only for the date the claim arose.
_REQUIRED = [
    ("your_name",     "your first name"),
    ("your_surname",  "your surname"),
    ("your_address",  "your address"),
    ("other_name",    "the other party's name or business name"),
    ("other_address", "the other party's address"),
    ("amount",        "the amount you are claiming"),
    ("failure_date",  "the date it went wrong"),
    ("claim_basis",   "what happened"),
]


def missing_required(facts: dict) -> list[str]:
    """Human-readable names of the required fields that are still empty."""
    return [label for key, label in _REQUIRED
            if not str(facts.get(key, "") or "").strip()]


def completeness_issue(facts: dict) -> dict | None:
    missing = missing_required(facts)
    if not missing:
        return None
    listed = missing[0] if len(missing) == 1 else (
        ", ".join(missing[:-1]) + " and " + missing[-1])
    return {
        "severity": "high",
        "blocks": True,
        "issue": (
            f"The letter still needs {listed}. A letter of demand has to name "
            f"both parties, state the amount, give the date the claim arose "
            f"and say what happened — without those it is not a valid demand "
            f"and the clerk will refuse the summons that follows it."
        ),
        "remedy": (
            "Fill in the fields above and Willa will continue. E-mail "
            "addresses are optional: the demand is delivered by registered "
            "post or by hand, not by e-mail."
        ),
        "where": "Small Claims Courts Rules, rule 7(1); s29(1) for delivery",
    }


def blocking_issues(facts: dict) -> list[dict]:
    """Issues that must stop a draft.

    Separate from severity, because the model reviewer also emits high-severity
    issues that are worth reading but are not grounds to refuse. Completeness
    is reported first: an incomplete form produces spurious findings from the
    other checks.
    """
    incomplete = completeness_issue(facts)
    if incomplete:
        return [incomplete]
    return [i for i in jurisdiction_issues(facts) if i.get("blocks")]


def dedupe(issues: list[dict]) -> list[dict]:
    """Drop near-identical issues, keeping the highest severity of each."""
    rank = {"high": 0, "medium": 1, "low": 2}
    seen: dict[str, dict] = {}
    for issue in sorted(issues, key=lambda i: rank.get(i.get("severity", "low"), 3)):
        key = re.sub(r"[^a-z0-9]+", " ", str(issue.get("issue", "")).lower())[:60]
        seen.setdefault(key, issue)
    return sorted(seen.values(), key=lambda i: rank.get(i.get("severity", "low"), 3))
