"""Round-trip verification for translations.

English goes out, comes back, and the two are compared. Three layers, in
increasing cost and decreasing certainty.

1. Facts. Every number, amount, date and deadline in the source must survive
   the round trip. Deterministic and cheap.

2. Back-translation. The reverse leg runs through Helsinki Opus-MT where an
   independent model exists, and through NLLB itself where none does. The tier
   is reported with every result, because a model can reverse its own mistake
   and return clean English while the target text is wrong.

3. Meaning. Optionally, the local model judges whether source and round trip
   say the same thing. Off by default, since it costs a model call per string.

None of this proves a translation is good. It finds translations that are
clearly broken and shows which languages carry the least evidence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from . import telemetry
from .i18n import BY_CODE
from .translate import FLORES, TranslationError, translate, missing_values

Tier = Literal["independent", "mirror", "none"]

# Reverse-direction models that are NOT NLLB. Helsinki-NLP/opus-mt-bnt-en
# covers Kinyarwanda, Lingala, Luganda, Nyanja, Rundi, Shona, Swahili, Tonga,
# Tsonga, Umbundu, Xhosa and Zulu — of our set, only these three.
INDEPENDENT_BACK = {
    "zu": "Helsinki-NLP/opus-mt-bnt-en",
    "xh": "Helsinki-NLP/opus-mt-bnt-en",
    "ts": "Helsinki-NLP/opus-mt-bnt-en",
    "af": "Helsinki-NLP/opus-mt-af-en",
}

# No independent reverse model found. Verified by mirror only.
MIRROR_ONLY = ["st", "nso", "tn", "ss"]


def tier_for(code: str) -> Tier:
    if code in INDEPENDENT_BACK:
        return "independent"
    if code in FLORES:
        return "mirror"
    return "none"


# --- layer 1: facts that must survive -------------------------------------
_NUM = re.compile(r"\d[\d\s,.]*\d|\d")
_ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")


def _numbers(text: str) -> set[str]:
    """Bare numeric values, normalised so R4 750 and R4,750 compare equal."""
    out = set()
    for raw in _NUM.findall(text):
        cleaned = re.sub(r"[\s,]", "", raw).rstrip(".")
        if cleaned:
            out.add(cleaned)
    return out


@dataclass
class Result:
    code: str
    language: str
    tier: Tier
    source: str
    translated: str = ""
    back: str = ""
    problems: list[str] = field(default_factory=list)
    error: str = ""

    @property
    def ok(self) -> bool:
        return not self.problems and not self.error

    @property
    def evidence(self) -> str:
        if self.error:
            return "failed"
        if not self.ok:
            return "problems found"
        return "passed (strong)" if self.tier == "independent" else "passed (weak — mirror)"


def _check_facts(source: str, back: str) -> list[str]:
    """Checks that are meaningful on a round trip.

    Numbers are deliberately NOT checked here. They are verified against the
    forward translation instead, because Opus-MT mangles digits on the way
    back — R4 750 returning as $750, 2026-03-22 as month 33 — while the
    isiZulu and Afrikaans the user would actually see had them perfectly
    correct. Checking numbers here measured the verifier, not the product, and
    reported four failures that did not exist.

    What survives a round trip meaningfully: negation, and whether the
    sentence still exists at all.
    """
    problems: list[str] = []

    # Negation. "Willa is not a lawyer" came back from Xitsonga as "Willa was
    # a lawyer" and the number check said nothing, because there are no
    # numbers in it.
    neg = re.compile(r"\b(not|no|never|cannot|can't|don't|doesn't|won't|isn't|is not)\b", re.I)
    src_neg, back_neg = len(neg.findall(source)), len(neg.findall(back))
    if src_neg and back_neg < src_neg:
        problems.append(
            f"the English has {src_neg} negation(s) but the round trip has "
            f"{back_neg} — a dropped 'not' reverses the meaning, and this is a "
            f"disclaimer if it reads like one"
        )

    if source.strip() and not back.strip():
        problems.append("round trip produced nothing")
    elif back.strip() and len(back) < len(source) * 0.4:
        problems.append(
            f"round trip is far shorter than the source "
            f"({len(back)} vs {len(source)} chars) — content likely dropped"
        )
    return problems


# --- layer 2: the reverse leg ----------------------------------------------
_back_cache: dict[str, object] = {}


def _back_translate_independent(text: str, code: str) -> str:
    """Reverse leg through Opus-MT. Separate model, separate training data.

    This leg mangles numbers freely, which is why the number check runs against
    the forward translation instead. What the round trip is good for is meaning:
    dropped negations, collapsed sentences, reversed parties.
    """
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    import torch

    name = INDEPENDENT_BACK[code]
    if name not in _back_cache:
        with telemetry.timed("verify.load_back_model", model=name):
            _back_cache[name] = (
                AutoTokenizer.from_pretrained(name),
                AutoModelForSeq2SeqLM.from_pretrained(name).eval(),
            )
    tok, model = _back_cache[name]  # type: ignore[misc]
    batch = tok(text, return_tensors="pt", truncation=True, max_length=512)
    with torch.inference_mode():
        out = model.generate(**batch, max_new_tokens=512, num_beams=4)
    return tok.batch_decode(out, skip_special_tokens=True)[0]


def verify(source_en: str, code: str) -> Result:
    """Translate into `code`, bring it back, and report what survived."""
    lang = BY_CODE.get(code, {})
    result = Result(
        code=code,
        language=lang.get("name", code),
        tier=tier_for(code),
        source=source_en,
    )
    if result.tier == "none":
        result.error = f"No translation model covers {result.language}."
        return result

    try:
        result.translated = translate(source_en, code)
        # Numbers are checked against the FORWARD translation, not the round trip.
        lost = missing_values(source_en, result.translated)
        if lost:
            result.problems.append(
                f"number(s) {lost} are in the English but not in the "
                f"translation the user would see"
            )
    except TranslationError as exc:
        result.error = f"forward: {exc}"
        return result

    try:
        if result.tier == "independent":
            result.back = _back_translate_independent(result.translated, code)
        else:
            result.back = translate(result.translated, "en", from_lang=code)
    except Exception as exc:  # noqa: BLE001
        # An independent model that will not load must not silently become a
        # mirror check — the caller is relying on the tier being accurate.
        result.error = f"back-translation ({result.tier}): {type(exc).__name__}: {exc}"
        return result

    result.problems = _check_facts(source_en, result.back)
    telemetry.event(
        "verify",
        lang=code, tier=result.tier, ok=result.ok, problems=len(result.problems),
    )
    return result


# --- layer 3: does it still mean the same thing? ---------------------------
MEANING_SYSTEM = """\
You are comparing an English sentence with the same sentence after it was
translated into another language and back again.

Judge only whether the meaning survived. Differences in word order, article
choice or phrasing are fine. What matters is whether a reader of the round-trip
version would understand the same obligation, the same deadline, the same
amount and the same consequence.

Reply with a JSON object and nothing else:
{"same_meaning": true|false, "lost": "one short sentence, or empty string"}

Be strict about legal substance and relaxed about style.
"""


async def check_meaning(result: Result) -> tuple[bool, str]:
    """Optional third layer. Requires Ollama."""
    from .llm import get_provider

    if not result.back or result.error:
        return False, result.error or "nothing to compare"
    import json

    reply = await get_provider().chat(
        MEANING_SYSTEM,
        f"ORIGINAL:\n{result.source}\n\nAFTER ROUND TRIP:\n{result.back}\n\n/no_think",
        temperature=0.0,
    )
    try:
        parsed = json.loads(reply[reply.index("{"): reply.rindex("}") + 1])
        return bool(parsed.get("same_meaning")), str(parsed.get("lost", ""))
    except (ValueError, json.JSONDecodeError):
        return False, "could not parse the model's judgement"
