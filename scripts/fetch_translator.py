#!/usr/bin/env python3
"""Download the translation model. Run once, while online.

    pip install 'transformers>=4.44' torch sentencepiece
    python scripts/fetch_translator.py

About 2.4GB. After this the model lives in models/ and is used offline, the
same arrangement as the legal corpus.

The script verifies every language code Willa claims to support actually
exists in the downloaded tokeniser. If Meta ever ships a build without, say,
siSwati, this fails here rather than silently handing a siSwati speaker
English at the point they most need to understand something.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config          # noqa: E402
from app.translate import FLORES  # noqa: E402
from app.i18n import BY_CODE     # noqa: E402


def main() -> int:
    try:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    except ImportError:
        print("Missing dependencies. Run:\n"
              "  pip install 'transformers>=4.44' torch sentencepiece")
        return 1

    dest = config.NLLB_LOCAL_DIR
    print(f"Model : {config.NLLB_MODEL}")
    print(f"Into  : {dest}")
    print("Size  : ~2.4GB. This will take a while.\n")

    dest.mkdir(parents=True, exist_ok=True)
    try:
        tok = AutoTokenizer.from_pretrained(config.NLLB_MODEL)
        model = AutoModelForSeq2SeqLM.from_pretrained(config.NLLB_MODEL)
    except Exception as exc:  # noqa: BLE001
        print(f"Download failed: {type(exc).__name__}: {exc}")
        return 1

    tok.save_pretrained(str(dest))
    model.save_pretrained(str(dest))
    print(f"Saved to {dest}\n")

    print("Verifying every language code Willa advertises:")
    missing = []
    for code, flores in sorted(FLORES.items()):
        name = BY_CODE[code]["name"] if code in BY_CODE else code
        tid = tok.convert_tokens_to_ids(flores)
        ok = tid is not None and tid != tok.unk_token_id
        print(f"  {'ok  ' if ok else 'MISSING'} {name:12} {flores:10} id={tid}")
        if not ok:
            missing.append(f"{name} ({flores})")

    if missing:
        print("\nFAILED — the model does not know: " + ", ".join(missing))
        print("Do not enable those languages. Silently returning English to")
        print("someone who chose otherwise is the failure this check exists for.")
        return 1

    print(f"\nAll {len(FLORES)} codes present.")
    print("Next: set TRANSLATION_AVAILABLE = True in app/config.py,")
    print("then: python scripts/check_translation.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
