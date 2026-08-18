"""Form J141 preparation sheet, used once the 14 days have expired.

This is not a summons. Under s29(1)(a) the plaintiff delivers a summons to the
clerk, and under s29(2) the clerk checks it, sets a hearing date and issues it.
A document that looked issued would send a claimant to court holding something
that does not exist.

What it produces is the sheet a claimant writes onto the official Form 1,
including the Particulars of Claim, which the form requires to be brief, in
point form, and without a detailed history of the matter.

Structure is deterministic. Only the Particulars of Claim involve the model.
"""

from __future__ import annotations

import json
import re

from . import config, telemetry
from .checks import _money
from .prompts import PARTICULARS_SYSTEM, resolve_arose_date

TEMPLATE_PATH = config.FORMS_DIR / "J141_prep_template.md"
MISSING = "[NEEDS YOUR INPUT: {}]"


def _split_name(first: str, surname: str) -> tuple[str, str]:
    first, surname = (first or "").strip(), (surname or "").strip()
    return (first or MISSING.format("first names"),
            surname or MISSING.format("surname"))


def _bullets(items: list[str], indent: str = "   ") -> str:
    if not items:
        return f"{indent}{MISSING.format('this section')}"
    return "\n".join(f"{indent}- {str(i).strip()}" for i in items if str(i).strip())


def _abandonment_line(amount: str | None) -> str:
    """Paragraph 7 exists precisely for a claim over the ceiling.

    checks.py already warns when someone claims more than the limit; this is
    the mechanism that warning points at, so the two should agree.
    """
    value = _money(amount)
    ceiling = config.SCC_MONETARY_CEILING_ZAR
    if value is not None and value > ceiling:
        over = value - ceiling
        return (
            f"7. ABANDONMENT — this one applies to you.\n\n"
            f"   You are claiming R{value:,.2f}, which is above the Small Claims\n"
            f"   Court limit of R{ceiling:,}. Section 18 lets you abandon the\n"
            f"   excess so the claim fits within the court's jurisdiction.\n\n"
            f"   Amount to abandon: R{over:,.2f}\n"
            f"   You would then be claiming: R{ceiling:,}\n\n"
            f"   Abandoned money is gone for good — you cannot come back for it\n"
            f"   later, in this court or any other. If R{over:,.2f} matters more\n"
            f"   than the speed and low cost of this court, a Magistrate's Court\n"
            f"   is the alternative. That is your decision, not Willa's."
        )
    return (
        "7. ABANDONMENT — does not apply. Cross out paragraph 7 on the form.\n"
        "   (It is only for claims above the court's limit.)"
    )


def _setoff_line(admitted_debt: str) -> str:
    value = _money(admitted_debt)
    if value:
        return (
            f"8. SET-OFF — this one applies to you.\n\n"
            f"   You have said you owe the defendant R{value:,.2f}. Section 19\n"
            f"   lets you deduct that from your claim."
        )
    return (
        "8. SET-OFF — does not apply. Cross out paragraph 8 on the form.\n"
        "   (It is only for when you owe the defendant money too.)"
    )


async def build(facts: dict, provider) -> tuple[str, dict]:
    """Render the sheet. Returns the document and the model's raw sections."""
    reply = ""
    sections: dict = {"nature": [], "relief": "", "evidence": []}
    try:
        with telemetry.timed("particulars", model=config.CHAT_MODEL):
            reply = await provider.chat(
                PARTICULARS_SYSTEM,
                f"THE CLAIMANT'S ACCOUNT:\n{facts.get('claim_basis','')}\n\n"
                f"Amount claimed: R{facts.get('amount','')}\n"
                f"Date the claim arose: {resolve_arose_date(facts)}\n\n/no_think",
                temperature=0.1,
            )
        parsed = json.loads(reply[reply.index("{"): reply.rindex("}") + 1])
        sections = {
            "nature": [str(x) for x in parsed.get("nature", []) if str(x).strip()],
            "relief": str(parsed.get("relief", "") or "").strip(),
            "evidence": [str(x) for x in parsed.get("evidence", []) if str(x).strip()],
        }
    except (ValueError, json.JSONDecodeError, KeyError):
        # Better an empty section the user fills in than invented particulars.
        telemetry.event("particulars.unparseable", chars=len(reply))

    first, surname = _split_name(facts.get("your_name"), facts.get("your_surname"))
    amount = _money(facts.get("amount"))

    values = {
        "plaintiff_surname": surname,
        "plaintiff_first_names": first,
        "plaintiff_address": facts.get("your_address") or MISSING.format("your address"),
        "plaintiff_phone": facts.get("your_phone") or MISSING.format("your phone number"),
        "plaintiff_email": facts.get("your_email") or "(none given)",
        "defendant_name": facts.get("other_name") or MISSING.format("their name"),
        "defendant_first_names": facts.get("other_surname") or "(not applicable if a business)",
        "defendant_address": facts.get("other_address") or MISSING.format("their address"),
        "defendant_phone": facts.get("other_phone") or "(where known)",
        "defendant_email": facts.get("other_email") or "(where known)",
        "arose_date": f"   {resolve_arose_date(facts)}",
        "claim_amount": (f"   R{amount:,.2f}" if amount is not None
                         else f"   {MISSING.format('the amount you are claiming')}"),
        "particulars": _bullets(sections["nature"]),
        "relief": (f"   {sections['relief']}" if sections["relief"]
                   else f"   {MISSING.format('what you want the court to order')}"),
        "evidence": (_bullets(sections["evidence"]) if sections["evidence"]
                     else "   (none listed — attach photocopies of anything you have)"),
        "abandonment": _abandonment_line(facts.get("amount")),
        "setoff": _setoff_line(facts.get("admitted_debt", "")),
    }

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    document = re.sub(r"\{(\w+)\}", lambda m: values.get(m.group(1), m.group(0)), template)
    telemetry.event("summons_prep.built",
                    points=len(sections["nature"]),
                    evidence=len(sections["evidence"]))
    return document, sections
