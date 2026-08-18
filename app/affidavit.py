"""Form J994, the affidavit proving delivery of the letter of demand.

Rule 7(2) requires proof that the demand reached the defendant, by registered
post receipt or by affidavit, and rule 7(3) offers Form 5 for the affidavit.

No model is involved. Every field is either user input or fixed statutory
wording, so the output is identical for identical inputs.

Two constraints the interface must not gloss over. An affidavit is only valid
once sworn before a Commissioner of Oaths, who completes the bottom section.
And it is only needed for personal delivery, because registered post produces
its own receipt.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from . import config

TEMPLATE_PATH = config.FORMS_DIR / "J994_template.md"

# Where a Commissioner of Oaths can usually be found, free of charge. Included
# because "find a Commissioner of Oaths" is not actionable advice on its own.
COMMISSIONER_HINT = (
    "A Commissioner of Oaths can witness this for free. Police stations, "
    "post offices, and the clerk at any Magistrate's Court all have one. "
    "Take your ID and do not sign the affidavit until you are in front of them."
)


@dataclass
class AffidavitInput:
    plaintiff_full_name: str = ""
    id_number: str = ""
    plaintiff_address: str = ""
    delivery_date: str = ""
    delivery_time: str = ""
    recipient_name: str = ""
    delivery_place: str = ""
    delivered_personally: bool = True
    other_method: str = ""


MISSING = "[NEEDS YOUR INPUT: {}]"

_LABELS = {
    "plaintiff_full_name": "your full name and surname",
    "id_number": "your ID or passport number",
    "plaintiff_address": "your address",
    "delivery_date": "the date you delivered the letter",
    "delivery_time": "the time you delivered the letter",
    "recipient_name": "the name of the person who took the letter",
    "delivery_place": "where you delivered it",
}


def render(data: AffidavitInput) -> tuple[str, list[str]]:
    """Fill Form 5. Returns the document and the fields still outstanding."""
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    values: dict[str, str] = {}
    missing: list[str] = []
    for field, label in _LABELS.items():
        value = str(getattr(data, field, "") or "").strip()
        if value:
            values[field] = value
        else:
            values[field] = MISSING.format(label)
            missing.append(label)

    if data.delivered_personally:
        values["tick_or_blank_personal"] = "        [X]  <- this applies to you"
        values["other_method_explanation"] = "       (not applicable)"
    else:
        other = str(data.other_method or "").strip()
        values["tick_or_blank_personal"] = "        [ ]"
        if other:
            values["other_method_explanation"] = "\n".join(
                "       " + line for line in other.splitlines()
            )
        else:
            values["other_method_explanation"] = "       " + MISSING.format(
                "how you delivered the letter"
            )
            missing.append("how you delivered the letter")

    def sub(match: re.Match) -> str:
        key = match.group(1)
        return values.get(key, match.group(0))

    return re.sub(r"\{(\w+)\}", sub, template), missing


def delivery_guidance(delivered_personally: bool) -> dict:
    """What the user must actually do, which differs by delivery method."""
    if not delivered_personally:
        return {
            "needs_affidavit": True,
            "headline": "You will need this affidavit sworn",
            "body": (
                "Because you did not send the letter by registered post, rule "
                "7(2) requires an affidavit proving it reached the other side. "
                + COMMISSIONER_HINT
            ),
        }
    return {
        "needs_affidavit": True,
        "headline": "This must be signed in front of a Commissioner of Oaths",
        "body": (
            "You handed the letter over yourself, so rule 7(2) requires this "
            "affidavit as proof. It is not valid until it is sworn. "
            + COMMISSIONER_HINT
        ),
    }


REGISTERED_POST_GUIDANCE = {
    "needs_affidavit": False,
    "headline": "Keep your registered post receipt — that is your proof",
    "body": (
        "Rule 7(2) accepts a registered post receipt instead of an affidavit, "
        "so you do not need Form 5 and you do not need a Commissioner of "
        "Oaths. Keep the receipt somewhere safe. You will hand it to the clerk "
        "with your summons."
    ),
}
