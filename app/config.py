"""Application configuration. All inference is local; see scripts/check_egress.py."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = ROOT / "corpus"
DATA_DIR = ROOT / "data"
FORMS_DIR = DATA_DIR / "forms"
INDEX_PATH = DATA_DIR / "index.npz"
CHUNKS_PATH = DATA_DIR / "chunks.json"

# --- Local inference ----------------------------------------------------------
# Must remain a loopback address. app/llm.py rejects anything else.
OLLAMA_HOST = "http://127.0.0.1:11434"
CHAT_MODEL = "qwen3:8b"
EMBED_MODEL = "nomic-embed-text"

# Qwen3 emits <think> blocks; strip them before they reach the user.
STRIP_THINKING = True

# Roughly doubles drafting time. On by default: the drafter decides what goes
# in the letter and what becomes a placeholder, which is where fabrication
# creeps in. Disable for fast iteration on layout, re-enable to judge output.
DRAFT_THINKING = True

# --- Translation --------------------------------------------------------------
# Set False to remove the machine-translated languages from the selector with
# an explanation rather than an error.
TRANSLATION_AVAILABLE = True
NLLB_MODEL = "facebook/nllb-200-distilled-600M"
# Downloaded once by scripts/fetch_translator.py, then used offline. Kept in
# the project rather than the HuggingFace cache so it is inspectable.
NLLB_LOCAL_DIR = ROOT / "models" / "nllb-200-distilled-600M"

# --- Retrieval ----------------------------------------------------------------
CHUNK_CHARS = 1200
CHUNK_OVERLAP = 200
TOP_K = 6

# --- Statutory values ---------------------------------------------------------
# s15 sets jurisdiction by reference to the amount determined by the Minister
# by notice in the Gazette, so the ceiling is not in the Act and must be
# tracked separately. Re-verify before any release: an out-of-date ceiling
# sends claimants to the wrong court, and checks.py advises abandoning the
# excess under s18, which cannot be reversed.
SCC_MONETARY_CEILING_ZAR = 30000
SCC_CEILING_AUTHORITY = "GoN 7717 in GG 55038 of 20 July 2026, wef 1 August 2026"
SCC_CEILING_VERIFIED_ON = "2026-08-14, against justice.gov.za/scc"

DEMAND_NOTICE_DAYS = 14  # s29(1)(a)

# --- Claims store -------------------------------------------------------------
# Off by default. Willa's guarantee is that nothing a user types reaches disk,
# and scripts/check_privacy.py verifies it. Enabling this stores full claim
# text in plain text, append-only, with no encryption at rest and no deletion
# path. Both the guarantee and the POPIA position change if it is turned on.
CLAIMS_STORE_ENABLED = False
CLAIMS_PATH = DATA_DIR / "claims.jsonl"
