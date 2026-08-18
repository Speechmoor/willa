#!/usr/bin/env python3
"""Evaluate Willa against the methods in the practical exercises.

    python scripts/evaluate.py                  # everything
    python scripts/evaluate.py --tokens         # PE1 tokeniser cost by language
    python scripts/evaluate.py --compare        # PE3 4(b), 4(d)
    python scripts/evaluate.py --latency        # PE3 4(e)
    python scripts/evaluate.py --reflection     # PE3 5(c), 5(d)
    python scripts/evaluate.py --structured     # PE3 4(c)
    python scripts/evaluate.py --explanation    # PE3 5(a), 5(b)

Requires Ollama. --compare needs more than one model pulled:

    ollama pull qwen3:8b
    ollama pull llama3.2
    ollama pull deepseek-r1:8b

Sections fail independently, so a missing model does not end the run.
See also eval_tokens.py, eval_embeddings.py and eval_attention.py for the
corpus-level PE1 and PE2 measurements.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config  # noqa: E402

BAR = "=" * 74

# One realistic claim, used everywhere so results are comparable.
CASE = {
    "language": "en",
    "your_name": "Thandi", "your_surname": "Mokoena",
    "your_address": "14 Sisulu Street, Soweto, 1804", "your_email": "",
    "other_name": "Blue Sky Appliances", "other_surname": "",
    "other_address": "220 Main Reef Road, Roodepoort, 1724", "other_email": "",
    "amount": "4750",
    "agreement_date": "2026-03-11", "failure_date": "2026-03-22",
    "claim_basis": ("I paid R4750 for a fridge on 11 March 2026. It was "
                    "delivered on 18 March and stopped cooling four days "
                    "later. The shop refuses to repair or refund it."),
}

# PE3 4(d) names three criteria and evaluates "using external feedback
# rather than reading the code".

# CORRECTNESS: values from the form that must survive into the letter.
FACTS = {"4750": "amount", "Blue Sky Appliances": "defendant",
         "Mokoena": "plaintiff", "14": "notice period"}

# SPECIFICITY: the prompt requires the J993 structure and forbids invention.
# Placeholder markers are compliant; template scaffolding and refusals are not.
SPEC_VIOLATIONS = ["notes for implementers", "as an AI", "I cannot",
                   "lorem ipsum", "as a language model"]

# HALLUCINATION: none of these appear anywhere in the input, so any of them in
# the output was manufactured by the model.
NOT_IN_INPUT = ["warranty", "guarantee period", "insurance", "attorney",
                "interest at", "court order", "summons"]


# --------------------------------------------------------------------------
# PE1 §B — tokenisation
# --------------------------------------------------------------------------

# The same sentence in each language, so token counts are comparable. Content
# is deliberately mundane and legal-adjacent rather than literary.
SENTENCES = {
    "English":   "The court will hear your claim for four thousand rand.",
    "Afrikaans": "Die hof sal jou eis vir vierduisend rand aanhoor.",
    "isiZulu":   "Inkantolo izozwa isimangalo sakho samarandi ayizinkulungwane ezine.",
    "isiXhosa":  "Inkundla iza kuva ibango lakho leerandi ezingamawaka amane.",
    "Sesotho":   "Lekgotla le tla utlwa qoso ya hao ya diranta tse dikete tse nne.",
    "Sepedi":    "Kgoro ya tsheko e tla kwa molato wa gago wa diranta tse dikete tse nne.",
    "Setswana":  "Kgotlatshekelo e tla utlwa ngongorego ya gago ya diranta tse dikete tse nne.",
    "siSwati":   "Inkantolo itawuva sikhalo sakho semarandi lasitfupha inkhulungwane.",
    "Xitsonga":  "Huvo yi ta twa xikombelo xa wena xa tirhandi ta magidi ya mune.",
    "Tshivenda": "Khoro i ḓo pfa khumbelo yau ya dzirandi dza zwigidi zwiṋa.",
    "isiNdebele": "Ikhotho izokuzwa isimangalo sakho samarandi azii zinkulungwane ezine.",
}


def run_tokens() -> None:
    """How many tokens does one sentence cost in each language?

    PE1 q15 established that cl100k_base is byte-level BPE trained on a corpus
    where some languages are far better represented than others. The practical
    consequence is measurable here: a language the tokeniser has not seen much
    of fragments into more tokens for the same meaning. More tokens is more
    context consumed, more latency, and less room for retrieved statute.
    """
    print(BAR)
    print("TOKENISER FERTILITY ACROSS SOUTH AFRICA'S OFFICIAL LANGUAGES")
    print(BAR)

    encode = None
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        encode = enc.encode
        print(f"  encoding: cl100k_base   vocabulary: {enc.n_vocab:,}")
    except ImportError:
        # UTF-8 byte length is a floor on what a byte-level BPE can produce and
        # correlates with it strongly, so the ordering survives even though the
        # absolute numbers do not.
        print("  tiktoken not installed — falling back to UTF-8 byte counts.")
        print("  Install it for the real BPE figures:  pip install tiktoken")
        encode = lambda t: t.encode("utf-8")  # noqa: E731

    real = "tiktoken" in sys.modules
    unit = "tokens" if real else "bytes"

    # Two ratios, and only one of them isolates the tokeniser. Tokens per WORD
    # conflates two things.
    print()
    print(f"  {'language':12} {'words':>6} {'chars':>6} {unit:>7} "
          f"{'per word':>9} {'per char':>9} {'vs Eng':>8}")
    print("  " + "-" * 62)

    rows = []
    for name, sent in SENTENCES.items():
        words = len(sent.split())
        chars = len(sent)
        toks = len(encode(sent))
        rows.append((name, words, chars, toks, toks / words, toks / chars))

    base_pc = next(r[5] for r in rows if r[0] == "English")
    for name, w, c, t, pw, pc in sorted(rows, key=lambda r: -r[5]):
        print(f"  {name:12} {w:6} {c:6} {t:7} {pw:9.2f} {pc:9.3f} "
              f"{pc/base_pc:7.2f}x")

    worst = max(rows, key=lambda r: r[5])
    print(f"\n  Per character, English costs {base_pc:.3f} {unit}/char and "
          f"{worst[0]} costs {worst[5]:.3f} ({worst[5]/base_pc:.2f}x).")

    if not real:
        print("\n  CAVEAT: these are UTF-8 bytes, not BPE tokens. Bytes measure")
        print("  how much a language leans on multi-byte characters, not how")
        print("  well the tokeniser knows it — the two are related but not the")
        print("  same, and PE1 q10 is precisely about not confusing them.")
        print("  Install tiktoken and re-run for the figures worth citing.")
    else:
        print("\n  This is the coverage gap expressed as arithmetic. A language")
        print("  the tokeniser saw little of fragments toward per-character")
        print("  encoding, so the same claim costs more context, leaves less")
        print("  room for retrieved statute, and runs slower — before any")
        print("  question of translation quality arises.")


# --------------------------------------------------------------------------
# PE3 4(e) — latency, cold start discarded
# --------------------------------------------------------------------------

async def _chat(model: str, system: str, prompt: str, temperature: float = 0.2) -> tuple[str, float]:
    from app.llm import OllamaProvider
    p = OllamaProvider(model=model)
    t0 = time.perf_counter()
    out = await p.chat(system, prompt, temperature=temperature)
    return out, time.perf_counter() - t0


async def run_latency(runs: int = 3) -> None:
    """Time each stage of a real draft.

    PE3 4(e) measured with time.time() around the call and ran it twice
    because the first call loads the model. The same applies here, and the
    warm-up is discarded rather than averaged in.
    """
    print("\n" + BAR)
    print("STAGE LATENCY  (cold start discarded)")
    print(BAR)

    try:
        from app.main import draft, DraftRequest
    except Exception as exc:  # noqa: BLE001
        print(f"  cannot load the app: {type(exc).__name__}: {exc}")
        return

    print(f"  model: {config.CHAT_MODEL}   thinking: {config.DRAFT_THINKING}")
    print(f"  warm-up run, then {runs} timed runs\n")

    print("  warming the model…", end=" ", flush=True)
    t0 = time.perf_counter()
    try:
        await draft(DraftRequest(**CASE))
    except Exception as exc:  # noqa: BLE001
        print(f"\n  FAILED: {type(exc).__name__}: {exc}")
        print("  (Is Ollama running? Is the index built?)")
        return
    print(f"{time.perf_counter()-t0:.1f}s (discarded)\n")

    times = []
    for i in range(runs):
        t0 = time.perf_counter()
        await draft(DraftRequest(**CASE))
        dt = time.perf_counter() - t0
        times.append(dt)
        print(f"  run {i+1}: {dt:6.1f}s")

    print(f"\n  mean {statistics.mean(times):.1f}s   "
          f"median {statistics.median(times):.1f}s   "
          f"min {min(times):.1f}s   max {max(times):.1f}s")
    if len(times) > 1:
        print(f"  spread {max(times)-min(times):.1f}s "
              f"({100*(max(times)-min(times))/statistics.mean(times):.0f}% of mean)")
    print("\n  Per-stage timings are in the telemetry log; the pipeline runs")
    print("  retrieval, draft, review and explain, and the two model passes")
    print("  dominate. See config.DRAFT_THINKING for the largest single lever.")


# --------------------------------------------------------------------------
# PE3 4(b)/4(d) — model comparison against stated criteria
# --------------------------------------------------------------------------

def score_letter(text: str) -> dict:
    """Score one letter on PE3 4(d)'s three criteria, by external check."""
    low = text.lower()
    missing = [f"{v} ({FACTS[v]})" for v in FACTS if v.lower() not in low]
    spec = [v for v in SPEC_VIOLATIONS if v in low]
    halluc = [v for v in NOT_IN_INPUT if v in low]
    return {
        "correctness": f"{len(FACTS)-len(missing)}/{len(FACTS)}",
        "missing": missing,
        "specificity": "pass" if not spec else "fail",
        "spec_detail": spec,
        "hallucination": len(halluc),
        "halluc_detail": halluc,
        "chars": len(text),
    }


async def run_compare(models: list[str]) -> None:
    print("\n" + BAR)
    print("MODEL COMPARISON  (identical prompt, stated criteria)")
    print(BAR)

    try:
        from app.prompts import DRAFTER_SYSTEM, draft_user_prompt
        from app.rag import Retriever, format_context
        import datetime as dt
    except Exception as exc:  # noqa: BLE001
        print(f"  cannot load the app: {type(exc).__name__}: {exc}")
        return

    facts = dict(CASE)
    facts["today"] = dt.date.today().isoformat()

    try:
        results = await Retriever().search_grouped(CASE["claim_basis"])
        context = format_context(results)
    except Exception as exc:  # noqa: BLE001
        print(f"  retrieval failed: {exc}")
        return

    template = (config.FORMS_DIR / "J993_template.md").read_text(encoding="utf-8")
    prompt = draft_user_prompt(facts=facts, form_template=template,
                               context=context, language_code="en")

    print("  Criteria, taken from PE3 4(d) and fixed before running:")
    print("    correctness    — do the deciding values survive into the letter")
    print("    specificity    — did it obey the prompt's explicit constraints")
    print("    hallucination  — does it assert anything the inputs do not")
    print("    speed          — PE3 4(e), warm, identical prompt\n")

    rows = []
    for m in models:
        print(f"  {m} …", end=" ", flush=True)
        try:
            await _chat(m, DRAFTER_SYSTEM, prompt)          # warm
            text, secs = await _chat(m, DRAFTER_SYSTEM, prompt)
        except Exception as exc:  # noqa: BLE001
            print(f"unavailable ({type(exc).__name__})")
            continue
        s = score_letter(text)
        rows.append((m, secs, s, text))
        print(f"{secs:.1f}s")

    if not rows:
        print("\n  No models responded. Pull at least one and retry.")
        return

    print(f"\n  {'model':18} {'correct':>8} {'specific':>9} {'halluc':>7} "
          f"{'chars':>6} {'secs':>7}")
    print("  " + "-" * 60)
    for m, secs, sc, _ in rows:
        print(f"  {m:18} {sc['correctness']:>8} {sc['specificity']:>9} "
              f"{sc['hallucination']:>7} {sc['chars']:>6} {secs:>7.1f}")

    for m, _, sc, _ in rows:
        detail = []
        if sc["missing"]:
            detail.append(f"correctness — lost {', '.join(sc['missing'])}")
        if sc["spec_detail"]:
            detail.append(f"specificity — {', '.join(sc['spec_detail'])}")
        if sc["halluc_detail"]:
            detail.append(f"hallucination — {', '.join(sc['halluc_detail'])}")
        if detail:
            print(f"\n  {m}:")
            for d in detail:
                print(f"    {d}")

    print("\n  Checked mechanically, as PE3 4(d) does — 'using external")
    print("  feedback rather than reading the code'. A letter that reads well")
    print("  but has lost the amount fails correctness, which is the right")
    print("  ordering for a document that starts a legal process.")


# --------------------------------------------------------------------------
# PE3 5(c)/5(d) — does reflection actually improve anything?
# --------------------------------------------------------------------------

async def run_reflection() -> None:
    """Willa drafts, then critiques its own draft. Does that help?

    PE3 5(d)'s finding is the model for this: "the reflection pattern barely
    improved the summary. The critique was excellent but the revision was
    not." The two halves were judged separately, and that separation is the
    whole value of the answer — a pattern can have a working critique step and
    still deliver nothing, and reporting a single verdict would hide it.

    So this measures the same two things independently:

      CRITIQUE   does the review pass raise anything real, over and above the
                 deterministic rules that fire anyway?
      REVISION   does anything change as a result? Willa's arrangement is
                 weaker than PE3's here by construction: PE3 revised the
                 summary, whereas Willa surfaces the critique to the user as
                 warnings and never rewrites the letter. If the critique is
                 empty, the pattern has cost a model pass and returned nothing.

    One further difference PE3 makes relevant: it critiqued llama3.2 with
    qwen3.5 — a different model. Willa critiques qwen3 with qwen3.
    """
    print("\n" + BAR)
    print("REFLECTION PATTERN  (PE3 5(c)/5(d))")
    print(BAR)

    try:
        from app.main import draft, DraftRequest
        from app.checks import jurisdiction_issues
    except Exception as exc:  # noqa: BLE001
        print(f"  cannot load the app: {type(exc).__name__}: {exc}")
        print("  Run this from the project venv, with dependencies installed.")
        return

    print(f"  drafter: {config.CHAT_MODEL}   critic: {config.CHAT_MODEL}"
          f"   (PE3 used two different models)\n")

    # Three cases: one clean, two with planted statutory problems that the
    # code rules will also catch. Separating the two sources is what shows
    # whether the model pass contributes anything of its own.
    cases = {
        "clean claim": CASE,
        "over the ceiling (R35 000)": {**CASE, "amount": "35000"},
        "company as plaintiff": {**CASE, "your_name": "Mokoena Trading (Pty) Ltd",
                                 "your_surname": ""},
    }

    total_model = 0
    for label, case in cases.items():
        print(f"  {label}")
        try:
            body = json.loads((await draft(DraftRequest(**case))).body)
        except Exception as exc:  # noqa: BLE001
            print(f"    FAILED: {type(exc).__name__}: {exc}\n")
            continue

        issues = body.get("issues", [])
        statutory = jurisdiction_issues({**case, "today": ""})
        stat_keys = {i.get("where") for i in statutory}
        from_model = [i for i in issues if i.get("where") not in stat_keys]
        total_model += len(from_model)

        print(f"    raised in total:           {len(issues)}")
        print(f"    from code (deterministic): {len(statutory)}")
        print(f"    CRITIQUE, model-only:      {len(from_model)}")
        for i in from_model[:4]:
            print(f"      [{i.get('severity','?')}] {str(i.get('issue'))[:82]}")
        print(f"    REVISION: none — the letter is never rewritten, the")
        print(f"              critique is surfaced to the user as warnings.\n")

    print(f"  Model-only findings across {len(cases)} cases: {total_model}")
    print("\n  Reading this the way 5(d) does: the deterministic rules are the")
    print("  floor and always fire, so they are not evidence for the pattern.")
    print("  The question is what the critique column adds. If it is empty or")
    print("  wrong, the review stage is buying latency and nothing else, and")
    print("  the remedy is the one PE3 used — an independent critic rather")
    print("  than the drafting model grading its own work.")



# --------------------------------------------------------------------------
# PE3 4(c) — structured output compliance
# --------------------------------------------------------------------------

async def run_structured(runs: int = 5) -> None:
    """Does the review pass return parseable JSON, every time?

    PE3 4(c) required the generated code to be wrapped in <python> tags and
    4(d) scored the models on whether they complied — deepseek "used markdown
    fences instead of the tags". Willa has the identical requirement one layer
    down: the review pass must return a JSON array, and app/main.py parses it
    by locating the first '[' and the last ']'. When that fails it logs
    review.unparseable and the letter is returned with the model's findings
    silently dropped.

    That is a specificity failure in exactly PE3's sense, and unlike PE3's it
    is invisible to the user: the letter still appears, just without the
    warnings the review pass produced. This measures how often it happens.
    """
    print("\n" + BAR)
    print("STRUCTURED OUTPUT COMPLIANCE  (PE3 4(c))")
    print(BAR)

    try:
        from app.main import draft, DraftRequest
        from app.prompts import REVIEW_SYSTEM
    except Exception as exc:  # noqa: BLE001
        print(f"  cannot load the app: {type(exc).__name__}: {exc}")
        return

    print(f"  The review prompt requires a JSON array. Parsing is by first '['")
    print(f"  to last ']', so partial compliance can still succeed.\n")

    ok = 0
    for i in range(runs):
        try:
            body = json.loads((await draft(DraftRequest(**CASE))).body)
        except Exception as exc:  # noqa: BLE001
            print(f"  run {i+1}: request failed — {type(exc).__name__}")
            continue
        issues = body.get("issues", [])
        # Deterministic rules always return something, so an empty list after a
        # clean case is consistent with either compliance or a parse failure.
        print(f"  run {i+1}: {len(issues)} issue(s) returned")
        ok += 1

    print(f"\n  {ok}/{runs} runs completed.")
    print("  Check logs/ for review.unparseable events — each one is a review")
    print("  pass whose findings never reached the claimant. PE3's deepseek")
    print("  failure was visible because the tags were missing from output the")
    print("  user could see; this one is not, which makes it worse.")


# --------------------------------------------------------------------------
# PE3 5(a)/5(b) — what is lacking from the generated summary?
# --------------------------------------------------------------------------

async def run_explanation(runs: int = 1) -> None:
    """Evaluate Willa's plain-language explanation the way PE3 5(b) does.

    PE3 5(a) generated a summary of a dataset and 5(b) asked what was lacking
    from it. The answer separated two kinds of defect: errors of
    interpretation (the Addiction mean labelled "mostly non-addicted" when
    0.92 on a binary variable means the opposite) and omissions (things that
    should have been said and were not).

    Willa produces a structurally identical artefact: a plain-language
    explanation of the letter, shown to a claimant who may not be able to read
    the letter itself. It has never been evaluated. The same two axes apply,
    and the stakes are higher — a claimant acts on this summary.
    """
    print("\n" + BAR)
    print("EXPLANATION QUALITY  (PE3 5(a)/5(b))")
    print(BAR)

    try:
        from app.main import draft, DraftRequest
    except Exception as exc:  # noqa: BLE001
        print(f"  cannot load the app: {type(exc).__name__}: {exc}")
        return

    # Facts the explanation must convey for a claimant to act correctly. These
    # are the omission checks: each is something 5(b) would list as "lacking".
    MUST_CONVEY = {
        "the amount": ["4750", "4,750"],
        "the deadline": ["14", "fourteen"],
        "who must pay": ["blue sky"],
        "what happens next": ["court", "claim", "summons"],
    }

    for i in range(runs):
        try:
            body = json.loads((await draft(DraftRequest(**CASE))).body)
        except Exception as exc:  # noqa: BLE001
            print(f"  FAILED: {type(exc).__name__}: {exc}")
            return

        exp = (body.get("explanation") or body.get("explanation_en") or "")
        if not exp:
            print("  No explanation was produced.")
            if body.get("explanation_failed"):
                print(f"  reason: {body['explanation_failed']}")
            return

        low = exp.lower()
        print(f"  run {i+1}: {len(exp)} characters, "
              f"{len(exp.split())} words\n")
        print("  OMISSIONS — is each thing a claimant must know present?")
        missing = []
        for label, variants in MUST_CONVEY.items():
            hit = any(v in low for v in variants)
            print(f"    {'yes' if hit else 'NO ':>4}  {label}")
            if not hit:
                missing.append(label)

        print("\n  ERRORS OF INTERPRETATION — checks that can be automated:")
        # The clearest analogue of PE3's inverted-mean error: a number in the
        # explanation that appears nowhere in the source facts.
        import re as _re
        nums = set(_re.findall(r"\b\d[\d,\.]{1,}\b", exp))
        source = " ".join(str(v) for v in CASE.values())
        invented = [n for n in nums
                    if n.replace(",", "") not in source.replace(",", "")]
        print(f"    numbers in the explanation: {sorted(nums) or 'none'}")
        print(f"    not traceable to the input: {sorted(invented) or 'none'}")

        if missing or invented:
            print("\n  This is what 5(b) asks for: not whether the summary reads")
            print("  well, but what it gets wrong and what it leaves out.")
        else:
            print("\n  No omissions or untraceable figures in this run. One run")
            print("  is not evidence; raise --runs before drawing a conclusion.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tokens", action="store_true")
    ap.add_argument("--latency", action="store_true")
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--reflection", action="store_true")
    ap.add_argument("--structured", action="store_true")
    ap.add_argument("--explanation", action="store_true")
    ap.add_argument("--models", default="qwen3:8b,llama3.2,deepseek-r1:8b")
    ap.add_argument("--runs", type=int, default=3)
    args = ap.parse_args()

    everything = not any([args.tokens, args.latency, args.compare,
                          args.reflection, args.structured, args.explanation])

    def guard(label, fn):
        """One failing section must not take the rest of the run with it —
        a laptop without a second model pulled should still get the others."""
        try:
            fn()
        except KeyboardInterrupt:
            raise
        except Exception as exc:  # noqa: BLE001
            print(f"\n  [{label}] stopped: {type(exc).__name__}: {exc}")

    if args.tokens or everything:
        guard("tokens", run_tokens)
    if args.compare or everything:
        guard("compare", lambda: asyncio.run(
            run_compare([m.strip() for m in args.models.split(",") if m.strip()])))
    if args.latency or everything:
        guard("latency", lambda: asyncio.run(run_latency(args.runs)))
    if args.reflection or everything:
        guard("reflection", lambda: asyncio.run(run_reflection()))
    if args.structured or everything:
        guard("structured", lambda: asyncio.run(run_structured()))
    if args.explanation or everything:
        guard("explanation", lambda: asyncio.run(run_explanation()))

    print("\n" + BAR)
    print("Paste these tables into section 4 of the paper.")
    print(BAR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
