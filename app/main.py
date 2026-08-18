"""FastAPI application.

No authentication and no session store. Facts posted to /api/draft live in the
request handler and are gone when it returns.

One exception, opt-in: config.CLAIMS_STORE_ENABLED enables the append-only
ledger in app/claims.py, which writes claims to disk in plain text. It is off
by default and the /api/claims endpoints refuse while it is.
"""

from __future__ import annotations

import datetime as dt
import json
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import claims, config, telemetry
from .affidavit import (
    AffidavitInput, render as render_affidavit, delivery_guidance,
    REGISTERED_POST_GUIDANCE,
)
from .checks import jurisdiction_issues, blocking_issues, dedupe
from .i18n import (
    LANGUAGES, BY_CODE, strings_for, is_draftable, availability_note,
    is_machine_translated,
)
from .llm import get_provider, InferenceError
from .prompts import (
    DRAFTER_SYSTEM, REVIEW_SYSTEM, EXPLAIN_SYSTEM,
    draft_user_prompt, review_facts_block,
)
from .translate import translate_checked, supported as translate_supported, TranslationError
from .rag import Retriever, format_context
from .summons import build as build_summons_prep

app = FastAPI(title="Willa", docs_url=None, redoc_url=None)


@app.exception_handler(RequestValidationError)
async def _validation_error(request, exc: RequestValidationError) -> JSONResponse:
    """Strip user input out of validation errors.

    The default handler echoes the rejected value back in the response body.
    The field name and reason are enough to correct a form.
    """
    fields = []
    for err in exc.errors():
        loc = ".".join(str(p) for p in err.get("loc", []) if p != "body")
        fields.append(f"{loc}: {err.get('msg', 'invalid')}")
    telemetry.event("validation_error", fields=len(fields))
    return JSONResponse(
        status_code=422,
        content={"detail": "Some fields were not accepted: " + "; ".join(fields)},
    )

STATIC_DIR = Path(__file__).parent / "static"
# The letter skeleton the model fills. The other file in forms/ is human
# documentation and must never reach the prompt.
FORM_TEMPLATE = (config.FORMS_DIR / "J993_template.md").read_text(encoding="utf-8")

_retriever: Retriever | None = None


def retriever() -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever


class DraftRequest(BaseModel):
    language: str = "en"
    your_name: str = ""
    your_surname: str = ""
    your_address: str = ""
    your_email: str = ""
    other_name: str = ""
    other_surname: str = ""
    other_address: str = ""
    other_email: str = ""
    amount: str = ""
    # Two dates, because the date a claim "arose" differs by claim type:
    # failure date for defective goods, due date for an unpaid invoice.
    agreement_date: str = ""
    failure_date: str = ""
    claim_basis: str = Field(default="", max_length=8000)

    # Input and output languages are independent: any official language may be
    # used in court. `language` remains the interface language and the default
    # for both, so clients that do not send these keep working.
    input_language: str = ""
    output_language: str = ""

    def resolved_input(self) -> str:
        return self.input_language or self.language

    def resolved_output(self) -> str:
        return self.output_language or "en"


@app.get("/api/languages")
def languages() -> JSONResponse:
    return JSONResponse(
        {
            "languages": [
                {
                    "code": l["code"],
                    "name": l["name"],
                    "endonym": l["endonym"],
                    "status": l["status"],
                    "draftable": is_draftable(l["code"]),
                    "note": availability_note(l["code"]),
                }
                for l in LANGUAGES
            ]
        }
    )


@app.get("/api/strings/{code}")
def ui_strings(code: str) -> JSONResponse:
    if code not in BY_CODE:
        raise HTTPException(404, "Unknown language")
    lang = BY_CODE[code]
    return JSONResponse(
        {
            "code": code,
            "status": lang["status"],
            "draftable": is_draftable(code),
            "machine_translated": is_machine_translated(code),
            "strings": strings_for(code),
        }
    )


class AffidavitRequest(BaseModel):
    plaintiff_full_name: str = ""
    id_number: str = ""
    plaintiff_address: str = ""
    delivery_date: str = ""
    delivery_time: str = ""
    recipient_name: str = ""
    delivery_place: str = ""
    # "post" needs no affidavit at all; "personal" and "other" do.
    delivery_method: str = "personal"
    other_method: str = ""


@app.post("/api/affidavit")
def affidavit(req: AffidavitRequest) -> JSONResponse:
    """Form J994. Substitution only; no model is involved."""
    if req.delivery_method == "post":
        telemetry.event("affidavit.not_needed", method="post")
        return JSONResponse({
            "document": "", "missing": [], "guidance": REGISTERED_POST_GUIDANCE,
        })

    data = AffidavitInput(
        plaintiff_full_name=req.plaintiff_full_name,
        id_number=req.id_number,
        plaintiff_address=req.plaintiff_address,
        delivery_date=req.delivery_date,
        delivery_time=req.delivery_time,
        recipient_name=req.recipient_name,
        delivery_place=req.delivery_place,
        delivered_personally=(req.delivery_method == "personal"),
        other_method=req.other_method,
    )
    document, missing = render_affidavit(data)
    telemetry.event("affidavit.rendered",
                    method=req.delivery_method, missing=len(missing))
    return JSONResponse({
        "document": document,
        "missing": missing,
        "guidance": delivery_guidance(req.delivery_method == "personal"),
    })


class SummonsRequest(DraftRequest):
    """Everything the letter needed, plus the extras Form 1 asks for."""
    your_phone: str = ""
    other_phone: str = ""
    admitted_debt: str = ""


@app.post("/api/summons-prep")
async def summons_prep(req: SummonsRequest) -> JSONResponse:
    """Preparation sheet for Form 1. Not a summons: only the clerk issues one."""
    if not req.claim_basis.strip():
        raise HTTPException(400, "Tell Willa what happened first.")
    facts = req.model_dump()
    facts["today"] = dt.date.today().isoformat()
    telemetry.event("summons_prep.start", **{"facts": telemetry.safe(facts)})
    try:
        document, sections = await build_summons_prep(facts, get_provider())
    except InferenceError as exc:
        raise HTTPException(503, str(exc)) from exc
    return JSONResponse({
        "document": document,
        "sections": sections,
        "issues": dedupe(jurisdiction_issues(facts)),
    })


@app.get("/api/notices")
def notices() -> JSONResponse:
    """Cached Small Claims Court notices for the landing ticker.

    Served from disk, never fetched at request time. A live scrape would put
    an outbound request on every page load — failing check_egress.py and
    telling justice.gov.za that this user is preparing a claim.
    """
    path = config.DATA_DIR / "notices.json"
    try:
        return JSONResponse(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return JSONResponse({"fetched": None, "notices": []})


"""--- claims store ------------------------------------------------------

Off unless config.CLAIMS_STORE_ENABLED is True. Every endpoint below returns
503 with an explanation while it is off, rather than 404 — a missing route
reads as "this was never built", and someone would waste an afternoon on it.
"""


class ClaimIn(BaseModel):
    claim_id: str = ""
    claim: dict


@app.get("/api/claims")
def claims_list() -> JSONResponse:
    if not config.CLAIMS_STORE_ENABLED:
        return JSONResponse({"enabled": False, "claims": []})
    return JSONResponse({"enabled": True, "claims": claims.index()})


@app.post("/api/claims")
def claims_save(req: ClaimIn) -> JSONResponse:
    if not config.CLAIMS_STORE_ENABLED:
        return JSONResponse(
            {"detail": "The claims store is off. Set CLAIMS_STORE_ENABLED = "
                       "True in app/config.py to enable it."},
            status_code=503)
    # A claim without an id is a new one. Time-based rather than random so the
    # ledger sorts chronologically when read by eye.
    cid = req.claim_id.strip() or f"claim-{uuid.uuid4().hex[:12]}"
    rec = claims.append(cid, req.claim)
    return JSONResponse({"claim_id": cid, "seq": rec["seq"], "hash": rec["hash"]})


@app.get("/api/claims/verify")
def claims_verify() -> JSONResponse:
    """Walk the hash chain and report the first break, if any.

    Declared before /api/claims/{claim_id} on purpose: FastAPI matches routes
    in definition order, so the other way round "verify" is swallowed as a
    claim id and this endpoint becomes unreachable.
    """
    if not config.CLAIMS_STORE_ENABLED:
        return JSONResponse({"enabled": False}, status_code=503)
    return JSONResponse(claims.verify())


@app.get("/api/claims/{claim_id}")
def claims_get(claim_id: str) -> JSONResponse:
    if not config.CLAIMS_STORE_ENABLED:
        return JSONResponse({"detail": "The claims store is off."},
                            status_code=503)
    rec = claims.latest(claim_id)
    if not rec:
        return JSONResponse({"detail": "No such claim."}, status_code=404)
    return JSONResponse({
        "claim_id": claim_id,
        "claim": rec["claim"],
        "seq": rec["seq"],
        "saved": rec["ts"],
        "versions": len(claims.history(claim_id)),
    })


@app.get("/api/reference")
def reference() -> JSONResponse:
    """Cached reference pages — the Guide, the FAQ, and the court list.

    Same rule as the notices above, and for a sharper reason. These sections
    could trivially have been outbound links to justice.gov.za. That would
    hand a third party this user's IP, their timing, and — because of which
    page they landed on — the fact that they are preparing a claim. For
    someone in a dispute with a landlord or an employer, on a shared or
    monitored connection, that is the disclosure they may be trying to avoid.

    Note that check_egress.py would NOT have caught it: the browser makes the
    request, not us, so the harness would keep passing while the guarantee it
    tests had stopped being true. Written by scripts/fetch_reference.py.
    """
    path = config.DATA_DIR / "reference.json"
    try:
        return JSONResponse(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        # Absent cache is a normal state on a fresh clone, not an error. The
        # UI says how to populate it rather than showing an empty page.
        return JSONResponse({"fetched": None, "sections": {}})


@app.get("/api/health")
async def health() -> JSONResponse:
    """Is the local stack actually up? Surfaced in the UI so a failed draft is
    diagnosable without reading a traceback."""
    status: dict = {"ollama": False, "index": config.INDEX_PATH.exists(), "detail": ""}
    try:
        provider = get_provider()
        await provider.embed(["ping"])
        status["ollama"] = True
    except InferenceError as exc:
        status["detail"] = str(exc)
    except Exception as exc:  # noqa: BLE001 - surface anything to the UI
        status["detail"] = f"{type(exc).__name__}: {exc}"
    return JSONResponse(status)


@app.post("/api/draft")
async def draft(req: DraftRequest) -> JSONResponse:
    if req.language not in BY_CODE:
        raise HTTPException(400, "Unknown language")
    if not is_draftable(req.language):
        raise HTTPException(
            422,
            "Willa cannot responsibly draft in this language yet. "
            "See the language notes in the interface.",
        )
    # Validate up front rather than failing after the model has already run.
    for label, code in (("input", req.resolved_input()),
                        ("output", req.resolved_output())):
        if code not in BY_CODE:
            raise HTTPException(400, f"Unknown {label} language: {code}")
        if code != "en" and not translate_supported(code):
            raise HTTPException(
                422,
                f"Willa cannot translate {BY_CODE[code]['name']} yet, so it "
                f"cannot be used as the {label} language.",
            )
    if not req.claim_basis.strip():
        raise HTTPException(400, "Tell Willa what happened before drafting.")

    facts = req.model_dump()
    facts["today"] = dt.date.today().isoformat()
    telemetry.event("draft.start", lang=req.language,
                    lang_in=req.resolved_input(), lang_out=req.resolved_output(),
                    **{"facts": telemetry.safe(facts)})

    # --- input side ---------------------------------------------------------
    # The account is translated to English first: the corpus, the retriever
    # and the review prompt are all English.
    lang_in = req.resolved_input()
    input_translation_note = ""
    if lang_in != "en" and req.claim_basis.strip():
        try:
            englished, lost = translate_checked(req.claim_basis, "en", from_lang=lang_in)
            if lost:
                # An amount or date vanished on the way in. Drafting from that produces a
                # letter that is wrong about the very number the claim turns on, so the
                # original is used instead and the model is told which language it is
                # reading.
                telemetry.event("draft.input_values_lost", lang=lang_in, n=len(lost))
                input_translation_note = (
                    f"Your account was left in its original language: translating it "
                    f"lost {', '.join(lost)}, and drafting from that would have put "
                    f"the wrong figure in your letter."
                )
            else:
                facts["claim_basis"] = englished
                telemetry.event("draft.input_translated", lang=lang_in)
        except TranslationError as exc:
            input_translation_note = str(exc)
            telemetry.event("draft.input_translation_failed", lang=lang_in)

    # --- jurisdiction gate ---------------------------------------------------
    # After input translation, so a non-English claim is screened on the same
    # English text the drafter would see.
    refusals = blocking_issues(facts)
    if refusals:
        telemetry.event("draft.refused",
                        sections=[i.get("where", "") for i in refusals])
        return JSONResponse({
            "blocked": True,
            "letter": "",
            "issues": refusals,
            "input_language": lang_in,
            "output_language": req.resolved_output(),
            "input_translation_note": input_translation_note,
            "sources": [],
        })

    try:
        with telemetry.timed("retrieval"):
            # Searched with the Englished narrative: the corpus is five
            # English statutes, so querying it in Afrikaans retrieves noise.
            results = await retriever().search_grouped(facts["claim_basis"])
    except FileNotFoundError as exc:
        raise HTTPException(503, str(exc)) from exc
    telemetry.log_retrieval(results)

    context = format_context(results)
    provider = get_provider()

    try:
        with telemetry.timed("draft", model=config.CHAT_MODEL,
                             thinking=config.DRAFT_THINKING):
            prompt = draft_user_prompt(
                facts=facts,
                form_template=FORM_TEMPLATE,
                context=context,
                language_code=req.language,
            )
            if not config.DRAFT_THINKING:
                prompt += "\n\n/no_think"
            letter = await provider.chat(DRAFTER_SYSTEM, prompt, temperature=0.2)
        with telemetry.timed("review", model=config.CHAT_MODEL):
            checks = await provider.chat(
                REVIEW_SYSTEM,
                # The checker needs the structured fields as well as the
                # narrative, or it reports form values as fabricated.
                f"{review_facts_block(facts)}\n\n"
                f"THE USER'S ACCOUNT IN THEIR OWN WORDS:\n{facts['claim_basis']}\n\n"
                f"PASSAGES PROVIDED TO THE DRAFTER:\n{context}\n\n"
                f"OFFICIAL FORM SKELETON (prescribed wording — never flag this):\n"
                f"{FORM_TEMPLATE}\n\n"
                f"DRAFT:\n{letter}\n\n/no_think",
                temperature=0.0,
            )
    except InferenceError as exc:
        raise HTTPException(503, str(exc)) from exc

    try:
        issues = json.loads(checks[checks.index("[") : checks.rindex("]") + 1])
        if not isinstance(issues, list):
            issues = []
    except (ValueError, json.JSONDecodeError):
        telemetry.event("review.unparseable", chars=len(checks))
        issues = []

    # Plain-language explanation, then translated into the user's language.
    # The letter itself stays English — that is the language of record — but
    # nobody should sign something they cannot read.
    explanation_en = ""
    explanation = ""
    explanation_failed = ""
    try:
        with telemetry.timed("explain", model=config.CHAT_MODEL):
            explanation_en = await provider.chat(
                EXPLAIN_SYSTEM,
                f"THE LETTER:\n{letter}\n\n/no_think",
                temperature=0.1,
            )
    except InferenceError as exc:
        telemetry.event("explain.skipped", reason=type(exc).__name__)

    if explanation_en and req.language != "en":
        try:
            # Translate, then confirm the numbers survived. Masking them
            # beforehand was tried and made things worse — the model treats
            # placeholder characters as words and translates them.
            explanation, lost = translate_checked(explanation_en, req.language)
            if lost:
                # The model dropped a masked value entirely. The sentence no
                # longer contains the user's amount or date, so the summary is
                # not safe to show.
                telemetry.event("explain.values_lost", lang=req.language, n=len(lost))
                explanation = ""
                explanation_failed = (
                    "The translation lost number(s) that must not change "
                    f"({', '.join(lost)}), so it has been withheld."
                )
        except TranslationError as exc:
            # Never silently hand back English to someone who chose otherwise.
            explanation_failed = str(exc)
            telemetry.event("explain.translation_failed", lang=req.language)
    else:
        explanation = explanation_en

    # --- output side ---------------------------------------------------------
    # The letter is drafted in English and translated, and both are returned.
    lang_out = req.resolved_output()
    letter_translated = ""
    letter_translation_failed = ""
    if lang_out != "en" and letter.strip():
        try:
            letter_translated, lost = translate_checked(letter, lang_out)
            if lost:
                telemetry.event("draft.letter_values_lost",
                                lang=lang_out, n=len(lost))
                letter_translated = ""
                letter_translation_failed = (
                    "The translation lost figures that must not change "
                    f"({', '.join(lost)}), so it has been withheld. The English "
                    "letter below is complete and may be used as it stands."
                )
            else:
                telemetry.event("draft.letter_translated", lang=lang_out)
        except TranslationError as exc:
            letter_translation_failed = str(exc)
            telemetry.event("draft.letter_translation_failed", lang=lang_out)

    # Statutory checks run in code and are merged in. They are not opinions of
    # the model and do not depend on it having noticed anything.
    statutory = jurisdiction_issues(facts)
    issues = dedupe(statutory + [i for i in issues if isinstance(i, dict)])
    telemetry.event(
        "draft.done",
        letter_len=len(letter),
        issues=len(issues),
        high=sum(1 for i in issues if i.get("severity") == "high"),
        statutory=len(statutory),
    )

    return JSONResponse(
        {
            "letter": letter,
            "letter_translated": letter_translated,
            "letter_translation_failed": letter_translation_failed,
            "input_language": lang_in,
            "output_language": lang_out,
            "input_translation_note": input_translation_note,
            "explanation": explanation,
            "explanation_en": explanation_en,
            "explanation_language": req.language if explanation and req.language != "en" else "en",
            "explanation_failed": explanation_failed,
            "issues": issues,
            "sources": [
                {
                    "n": n,
                    "source": r["source"],
                    "citation": r.get("citation", ""),
                    "score": round(r["score"], 3),
                }
                for n, r in enumerate(results, 1)
            ],
        }
    )


@app.get("/")
def index() -> FileResponse:
    # no-store during development: a cached shell against a changed API is a
    # blank page with no error, which is the worst possible failure mode.
    return FileResponse(
        STATIC_DIR / "index.html",
        headers={"Cache-Control": "no-store, must-revalidate"},
    )


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
