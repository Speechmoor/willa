# Willa

Local-first drafting help for the South African Small Claims Court. One web
page, a language selector, and a grounded letter of demand. No authentication,
no database, no cloud.

Everything runs on the machine it is installed on. After the initial fetch
steps the application needs no network access.

## Quick start

macOS or Linux. On Windows use WSL, or follow *Setup by hand* below, which
works in PowerShell. You need [Ollama](https://ollama.com/download), Python
3.11–3.13, and about 8 GB of free memory. 16 GB of RAM makes it comfortable.

```bash
ollama serve                 # separate terminal, leave it running
./setup.sh --translate       # drop --translate for English only
./run.sh                     # http://127.0.0.1:8000
```

`setup.sh` creates the virtualenv, installs dependencies, pulls the models and
builds the index. It is safe to re-run and skips anything already done.
`./setup.sh --check` reports what is missing without changing anything, and
`run.sh` calls it first so a missing dependency arrives as a checklist rather
than as a traceback.

Budget about 8.5 GB of model downloads, or 6 GB without `--translate`. After
that the application needs no network access at all.

**Drafting takes 40 to 60 seconds** on Qwen3-8B. That is the cost of running
the model locally rather than calling an API, and it is discussed under
*Known limitations*. The page shows progress; it has not hung.

## If you are evaluating this

Start here, because it needs no models and finishes instantly:

```bash
./setup.sh --check                # what is installed, what is not
python scripts/check_rules.py     # 26 statutory fixtures, 0.04 seconds
```

`check_rules.py` is the clearest thing in the repository. It exercises the
jurisdiction gate in both directions: every rule fires when it should and
stays silent when it should not, no letter is generated for a claim the court
cannot hear, and every refusal carries a correction the claimant can act on.
No model is involved, so the result is the same on every run.

Then `python scripts/check_egress.py` and `check_privacy.py` for the privacy
claims, which also need no models. Run the application itself last, since that
is the part that needs the 8 GB download.

## Setup by hand

Python 3.11–3.13. **Not 3.14** — `pydantic-core` has no 3.14 wheels, so pip
compiles it from Rust and PyO3 rejects the interpreter.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

ollama serve                          # separate terminal
ollama pull qwen3:8b
ollama pull nomic-embed-text

python scripts/ingest.py              # builds the local index
uvicorn app.main:app --reload         # http://127.0.0.1:8000
```

The Acts, the Rules and the official forms are committed under `corpus/`, so a
clone does not need the network for them. `python scripts/fetch_corpus.py`
refreshes them from source and `corpus/MANIFEST.md` records where each came
from, with a SHA-256 for each file.

Optional, for the seven machine-translated languages (~2.4 GB):

```bash
pip install -r requirements-translate.txt
python scripts/fetch_translator.py
python scripts/build_ui_translations.py
python scripts/fetch_reference.py     # caches court guidance for offline use
```

## Verifying it

```bash
python scripts/check_egress.py       # nothing leaves the device
python scripts/check_privacy.py      # nothing is left on it
python scripts/check_rules.py        # statutory fixtures, instant
python scripts/check_translation.py  # round-trip every language
```

`check_egress.py` patches the socket layer and fails on any off device
connection. `check_privacy.py` runs a draft with canary values, greps every
writable path, and self-tests by planting a leak it must find. Each exits non
zero on failure and is suitable for CI.

## What it does

Language, then a guided form, then a grounded draft, then review, then proof
of delivery, then summons preparation.

| Step | Output | Model involved |
|---|---|---|
| Review | Letter of demand (J993), plus a plain-language explanation in the user's language | Yes, grounded then checked |
| Proof of delivery | Affidavit (J994) if delivered by hand; nothing if by registered post | No, pure substitution |
| If they do not pay | Preparation sheet for Form 1 (J141) | Only the Particulars of Claim |

**Willa does not produce a summons.** Under s29(2) the clerk assigns the case
number, sets the hearing date and issues it. The last step produces the sheet
a person writes onto the official form, and says so in its first line.

**The affidavit is not valid until sworn.** The interface says so and names
where to find a Commissioner of Oaths free of charge.

**Jurisdiction is enforced, not suggested.** `app/checks.py` applies s7(1)
(only a natural person may claim), s15 (the monetary ceiling) and s16
(excluded matters) before any model runs. If the court cannot hear the claim,
no letter is generated. Every refusal names the section and the correction
that clears it.

## Language coverage

| | Willa does | Verification |
|---|---|---|
| English, Afrikaans | hand-written UI, native drafting | — |
| isiZulu, isiXhosa, Xitsonga | machine-translated UI and explanation | independent (Opus-MT) |
| Sesotho, Sepedi, Setswana, siSwati | machine-translated UI and explanation | mirror only, weak |
| Tshivenḓa, isiNdebele | refuses, and says why | no model exists |
| SA Sign Language | refuses, and says why | not a written language |

**The letter is always produced in English as well.** English is the language
of record in South African courts, and no one on this project can verify a
legal document in isiZulu. When a translation is requested, both versions are
returned in the same file and the same print job.

`data/ui_strings_mt.json` is machine output that becomes a reviewed asset. It
is committed deliberately, and `build_ui_translations.py` preserves existing
strings unless you pass `--overwrite`, so reviewer corrections survive a
rebuild.

## For reviewers

```bash
python scripts/make_review_pack.py   # docs/review/<lang>.md, one per reviewer
```

Self-contained sheets for first-language speakers, roughly twenty minutes
each. Each leads with five legal terms: plaintiff, defendant, letter of
demand, commissioner, Small Claims Court. Those carry the document's meaning,
and "plaintiff" currently mistranslates as "defendant" in isiZulu and
"prosecutor" in three other languages.

## Known limitations

- **No translation has been reviewed by a first-language speaker.** Fine for a
  demo, not for a claimant. `docs/review/` is the artefact to send.
- **Legal terminology is unreliable.** "Plaintiff" returns as "defendant" in
  isiZulu and "prosecutor" in isiXhosa, Sesotho and Xitsonga, which is
  criminal vocabulary for a civil matter. Needs a per-language glossary.
- **Negation can drop.** "Willa is not a lawyer" round-trips from Xitsonga as
  "Willa was a lawyer".
- **The s16 screen matches on keywords** and produces false positives, so a
  contract dispute that mentions defamation in passing is refused. The
  refusal wording says this and tells the claimant how to correct it.
- **The review checker runs on the same model that wrote the draft.** The
  clearest remaining weakness in the pipeline.
- **It needs a laptop.** Python, Ollama and about 8 GB of free memory is a
  reasonable ask of a developer and a poor one for the person this is built
  for, most of whom reach the internet on a phone.
- No responsible party or information officer designated (POPIA condition 1).

## Layout

```
setup.sh          one command from clone to runnable; --check to preflight
run.sh            preflight, then serve on 127.0.0.1:8000
app/
  config.py       paths, models, statutory constants, feature flags
  i18n.py         12 languages; hand-written, then machine, then English
  llm.py          provider interface; refuses non-loopback hosts
  rag.py          chunking, citation detection, numpy cosine index
  prompts.py      drafting persona, grounding rules, review checker
  checks.py       s7/s15/s16 enforced in code
  affidavit.py    Form J994, deterministic
  summons.py      Form J141 prep sheet; only the particulars use the model
  translate.py    NLLB behind a swappable interface
  verify_translation.py   round-trip checking, tiered by evidence strength
  claims.py       append-only hash-linked ledger; tamper-evident, one machine
  telemetry.py    redacting logger; deny-by-default, shape not content
  main.py         FastAPI; no auth, no session store
  static/         single page, no build step, no external requests
scripts/
  fetch_corpus, ingest, fetch_translator, build_ui_translations,
  fetch_reference, fetch_notices
  check_egress, check_privacy, check_rules, check_translation
  eval_tokens, eval_embeddings, eval_attention, evaluate
  make_review_pack
corpus/           the Acts, the Rules and the official forms, with a manifest
data/forms/       form skeletons the drafter fills; the index is built, not committed
docs/review/      per-language sheets for reviewers
```

## Design notes

**Rules with a correct answer live in code, not in the prompt.** Which date
the claim arose, the s7 bar, and not reproducing the form template were all
tried as prompt instructions and all eventually ignored. The same rules moved
into Python have held. Prompts are for tone and shape.

**The failures that lasted longest all looked fine in the output.** The form
template leaking into a letter, the Act being unretrievable, the wrong arising
date, and the checker calling correct letters fabricated. None would have been
caught by reading the result. That is what `logs/willa.log` and the check
scripts are for.

## Not legal advice

Willa drafts from what a user types and what the statute says. It does not
assess merits. A Small Claims Court commissioner decides each case on its own
facts, and the clerk of any Small Claims Court assists the public free of
charge.
