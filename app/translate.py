"""Local translation via NLLB-200.

One public function, translate(text, to_lang), so the backend can be swapped
without changing callers.

Scope is deliberate: this translates interface text and the plain-language
explanation of the letter, not the letter itself. English is the language of
record in South African courts, and no reviewer on this project can verify a
translated operative document.

The model is downloaded once at setup and then runs offline.
"""

from __future__ import annotations

import functools
import re
import threading
from typing import Protocol

from . import config, telemetry
from .i18n import BY_CODE

# The nine written official languages NLLB-200 covers, by FLORES-200 code.
# Verified against Meta's published list, 2026-08-12. Tshivenḓa and isiNdebele
# are absent and must not fall through to English; see i18n.py.
FLORES = {
    "en": "eng_Latn", "af": "afr_Latn", "zu": "zul_Latn", "xh": "xho_Latn",
    "st": "sot_Latn", "nso": "nso_Latn", "tn": "tsn_Latn", "ss": "ssw_Latn",
    "ts": "tso_Latn",
}


class TranslationError(RuntimeError):
    pass


class Backend(Protocol):
    def translate(self, text: str, src: str, tgt: str) -> str: ...


class TransformersBackend:
    """NLLB-200-distilled-600M via transformers.

    Loaded lazily and once: the model is ~2.4GB and takes tens of seconds to
    come off disk, so it must not be pulled in at import time or every uvicorn
    reload would stall.
    """

    _lock = threading.Lock()

    def __init__(self) -> None:
        self._tok = None
        self._model = None

    def _load(self):
        if self._model is not None:
            return
        with self._lock:
            if self._model is not None:
                return
            try:
                from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
            except ImportError as exc:
                raise TranslationError(
                    "Translation needs transformers and torch:\n"
                    "  pip install 'transformers>=4.44' torch sentencepiece\n"
                    "then: python scripts/fetch_translator.py"
                ) from exc

            path = config.NLLB_LOCAL_DIR
            if not path.exists():
                raise TranslationError(
                    f"Translation model not found at {path}.\n"
                    "Run: python scripts/fetch_translator.py"
                )
            with telemetry.timed("translator.load", model=config.NLLB_MODEL):
                self._tok = AutoTokenizer.from_pretrained(str(path))
                self._model = AutoModelForSeq2SeqLM.from_pretrained(str(path))
                self._model.eval()

    def translate(self, text: str, src: str, tgt: str) -> str:
        self._load()
        import torch

        self._tok.src_lang = src
        batch = self._tok(text, return_tensors="pt", truncation=True, max_length=512)
        # NLLB selects the target language by forcing its token first.
        try:
            forced = self._tok.convert_tokens_to_ids(tgt)
        except Exception as exc:  # noqa: BLE001
            raise TranslationError(f"Unknown target language token: {tgt}") from exc
        if forced is None or forced == self._tok.unk_token_id:
            raise TranslationError(
                f"{tgt} is not a token this model knows. Refusing to translate "
                "rather than silently returning English."
            )
        with torch.inference_mode():
            out = self._model.generate(
                **batch, forced_bos_token_id=forced,
                max_new_tokens=512, num_beams=4,
            )
        return self._tok.batch_decode(out, skip_special_tokens=True)[0]


@functools.lru_cache(maxsize=1)
def _backend() -> Backend:
    return TransformersBackend()


def supported(code: str) -> bool:
    return code in FLORES


def translate(text: str, to_lang: str, from_lang: str = "en") -> str:
    """Translate text into a language code from i18n.LANGUAGES.

    Raises rather than degrading. A translation function that quietly returns
    English on failure is worse than one that errors: the user selected
    isiZulu, would be handed English, and would have no way to tell whether
    that was a bug or the whole product.
    """
    if to_lang == from_lang:
        return text
    if not text.strip():
        return text
    if not supported(to_lang):
        lang = BY_CODE.get(to_lang)
        name = lang["name"] if lang else to_lang
        raise TranslationError(
            f"No translation model covers {name}. It is not in NLLB-200."
        )
    with telemetry.timed("translate", to=to_lang, chars=len(text)):
        return _backend().translate(text, FLORES[from_lang], FLORES[to_lang])


def translate_many(texts: list[str], to_lang: str, from_lang: str = "en") -> list[str]:
    return [translate(t, to_lang, from_lang) for t in texts]


# --- checking that values survived ----------------------------------------
# Numbers are translated normally and then checked for presence in the
# output.
_VALUES = re.compile(
    r"""(
        \d{4}-\d{2}-\d{2}      |   # ISO dates
        \d[\d\s.,]*\d          |   # grouped digits: 4 750, 4,750, 19 999.99
        \d                         # single digit
    )""",
    re.VERBOSE,
)

# Institution names are left untranslated. Round-trip testing rendered "Small
# Claims Court" three different wrong ways, none of which a claimant could use
# to find the building or ask the right clerk.
PROTECTED_TERMS = [
    "Small Claims Court",
    "Willa",
]


def digits_in(text: str) -> set[str]:
    """Numeric values, normalised so R4 750, R4,750 and 4750 compare equal."""
    out = set()
    for raw in _VALUES.findall(text):
        cleaned = re.sub(r"[^\d]", "", raw)
        if cleaned:
            out.add(cleaned)
    return out


def missing_values(source: str, translated: str) -> list[str]:
    """Numbers in the source that are absent from the translation.

    Digits are language-independent: 14 is 14 in isiZulu. If a value the user
    supplied is not present verbatim in the output, the sentence has lost
    something it cannot afford to lose, whatever the surrounding words say.
    """
    src, out = digits_in(source), digits_in(translated)
    return sorted(src - out)


def translate_checked(
    text: str, to_lang: str, from_lang: str = "en"
) -> tuple[str, list[str]]:
    """Translate, then confirm every numeric value survived.

    Returns the translation and a list of values that went missing. A non-empty
    list means the caller should withhold the text — a summary that has lost
    the amount or the deadline is worse than no summary.
    """
    out = translate(text, to_lang, from_lang)
    return out, missing_values(text, out)
