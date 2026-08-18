#!/usr/bin/env python3
"""Tokenisation and vocabulary of Willa's statutory corpus — PE1 Section B.

    python scripts/eval_tokens.py

PE1 asked these questions of a Wikipedia dump. They are asked here of the five
documents Willa actually retrieves from, because the answers turn out to
decide whether retrieval works at all.

Covers:
  q7b  what do you notice about the tokens
  q7c  vocabulary size
  q8   ten most common tokens, non-character tokens omitted
  q14  tiktoken vocabulary, for comparison with the word-level count
  q15  what encoding scheme cl100k_base uses, and why the counts differ
  q16  most frequent token IDs and their values

nltk and tiktoken are optional; the script degrades to a regex tokeniser and
says so rather than refusing to run.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config  # noqa: E402

BAR = "=" * 72


def corpus_text() -> tuple[str, list[dict]]:
    chunks = json.loads(config.CHUNKS_PATH.read_text(encoding="utf-8"))
    return "\n\n".join(c.get("text", "") for c in chunks), chunks


def tokenise(text: str) -> tuple[list[str], str]:
    """word_tokenize if nltk is present, regex otherwise."""
    try:
        from nltk.tokenize import word_tokenize
        return word_tokenize(text), "nltk.word_tokenize"
    except Exception:  # noqa: BLE001
        return re.findall(r"\w+|[^\w\s]", text), "regex fallback"


def main() -> int:
    if not config.CHUNKS_PATH.exists():
        print("No corpus index. Run: python scripts/ingest.py")
        return 1

    text, chunks = corpus_text()
    tokens, how = tokenise(text)

    print(BAR)
    print("PE1 q7 — TOKENISING THE CORPUS")
    print(BAR)
    print(f"  documents: {len({c.get('source') for c in chunks})}")
    print(f"  passages:  {len(chunks)}")
    print(f"  characters:{len(text):,}")
    print(f"  tokeniser: {how}")
    print(f"\n  first 15 tokens: {tokens[:15]}")

    # q7c — vocabulary size
    vocab = set(tokens)
    print(f"\n  q7c  total tokens:      {len(tokens):,}")
    print(f"       vocabulary size:  {len(vocab):,}")
    print(f"       type/token ratio: {len(vocab)/len(tokens):.4f}")

    # q7b — what do you notice
    punct = sum(1 for t in tokens if not any(ch.isalnum() for ch in t))
    numeric = sum(1 for t in tokens if t.isdigit())
    caps = sum(1 for t in tokens if t.isupper() and len(t) > 1)
    print(f"\n  q7b  what is in here:")
    print(f"       punctuation-only tokens: {punct:,} ({100*punct/len(tokens):.1f}%)")
    print(f"       pure digits:             {numeric:,} ({100*numeric/len(tokens):.1f}%)")
    print(f"       ALL-CAPS words:          {caps:,} ({100*caps/len(tokens):.1f}%)")
    print("       Statute is unusually punctuation-heavy: section numbers,")
    print("       cross-references and sub-paragraph markers are content here,")
    print("       not noise, which is why the raw counts look odd next to prose.")

    # q8 — ten most common, non-character tokens omitted
    print("\n" + BAR)
    print("PE1 q8 — TEN MOST COMMON TOKENS (non-character tokens omitted)")
    print(BAR)
    words = [t.lower() for t in tokens if t.isalpha()]
    for tok, n in Counter(words).most_common(10):
        print(f"  {n:6}  {tok}")

    # The same list WITHOUT the omission, which is the instructive contrast.
    print("\n  For contrast, the same count with nothing omitted:")
    for tok, n in Counter(tokens).most_common(10):
        shown = repr(tok) if not tok.isalnum() else tok
        print(f"  {n:6}  {shown}")
    print("\n  q8 tells you to omit non-character tokens before drawing any")
    print("  conclusion, and the two lists show why. Willa's ingester was not")
    print("  doing the equivalent: 58 passages of table-of-contents dot leaders")
    print("  were embedded as though they were law. See scripts/eval_embeddings.py.")

    # The same corpus with the ingestion filter applied, which is the number
    # that shows what q8's instruction is actually worth.
    try:
        ns: dict = {}
        src = (Path(__file__).resolve().parent.parent / "app" / "rag.py").read_text()
        exec(src[src.index("def is_degenerate"):src.index("def chunk_text")], ns)
        is_degenerate = ns["is_degenerate"]
    except Exception as exc:  # noqa: BLE001
        print(f"\n  (filter comparison skipped: {type(exc).__name__})")
    else:
        clean_text = "\n\n".join(c.get("text", "") for c in chunks
                                 if not is_degenerate(c.get("text", "")))
        clean_tokens, _ = tokenise(clean_text)
        dots_before = sum(1 for t in tokens if t == ".")
        dots_after = sum(1 for t in clean_tokens if t == ".")
        print("\n" + BAR)
        print("PE1 q8 APPLIED — THE CORPUS BEFORE AND AFTER FILTERING")
        print(BAR)
        print(f"  {'':22} {'before':>12} {'after':>12}")
        print(f"  {'passages':22} {len(chunks):>12,} "
              f"{sum(1 for c in chunks if not is_degenerate(c.get('text',''))):>12,}")
        print(f"  {'characters':22} {len(text):>12,} {len(clean_text):>12,}")
        print(f"  {'tokens':22} {len(tokens):>12,} {len(clean_tokens):>12,}")
        print(f"  {'full stops':22} {dots_before:>12,} {dots_after:>12,}")
        print(f"  {'full stops as % of all':22} "
              f"{100*dots_before/len(tokens):>11.1f}% "
              f"{100*dots_after/max(1,len(clean_tokens)):>11.1f}%")
        print(f"\n  Two thirds of the corpus was punctuation. Removing 28.7% of")
        print(f"  the passages removed {100*(dots_before-dots_after)/dots_before:.0f}% "
              f"of the full stops and only "
              f"{100*(len(clean_text))/len(text):.0f}% of the characters were kept —")
        print("  the discarded passages carried almost no text at all.")

    # q14/q15/q16 — subword tokenisation
    print("\n" + BAR)
    print("PE1 q14/q15/q16 — SUBWORD TOKENISATION")
    print(BAR)
    try:
        import tiktoken
    except ImportError:
        print("  tiktoken not installed:  pip install tiktoken")
        print("  (word-level results above are unaffected)")
        return 0

    enc = tiktoken.get_encoding("cl100k_base")
    ids = enc.encode(text)
    print(f"  encoding:          cl100k_base")
    print(f"  q14 vocabulary:    {enc.n_vocab:,}")
    print(f"      word-level vocabulary from q7c: {len(vocab):,}")
    print(f"  total token IDs:   {len(ids):,}")
    print(f"  distinct IDs used: {len(set(ids)):,} "
          f"({100*len(set(ids))/enc.n_vocab:.1f}% of the vocabulary)")

    print("\n  q15  cl100k_base is byte-level BPE. It starts from the 256 byte")
    print("       values and merges the most frequent adjacent pair repeatedly")
    print("       until it reaches its target size. That is why its vocabulary")
    print("       is fixed and large while the corpus word vocabulary above is")
    print("       whatever this corpus happens to contain — and why no word is")
    print("       ever out-of-vocabulary, since any unseen word decomposes into")
    print("       pieces that ultimately bottom out at single bytes.")

    print(f"\n  tokens per word across the corpus: {len(ids)/len(tokens):.2f}")

    print("\n  q16  twenty most frequent token IDs:")
    print(f"       {'id':>7}  {'count':>7}  value")
    for tid, n in Counter(ids).most_common(20):
        val = enc.decode([tid])
        print(f"       {tid:>7}  {n:>7}  {val!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
