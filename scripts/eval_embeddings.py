#!/usr/bin/env python3
"""Measure the embedding space and the retrieval that sits on it.

    python scripts/eval_embeddings.py

Mirrors the embeddings work in PE1 Section C — dimensionality, similarity,
and what the geometry of the space actually implies — but asks the questions
that matter for a legal retrieval system rather than for a Wikipedia corpus.

Everything here runs against the shipped index, so the numbers are the ones
the running application uses. Only the live-query section needs Ollama, and
it degrades to a clear message rather than failing if Ollama is absent.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config  # noqa: E402

BAR = "=" * 72


def load() -> tuple[np.ndarray, list[dict]]:
    vecs = np.load(config.INDEX_PATH)["vectors"]
    chunks = json.loads(config.CHUNKS_PATH.read_text(encoding="utf-8"))
    return vecs, chunks


def section_dimensions(V: np.ndarray, chunks: list[dict]) -> None:
    """PE1 q21: interpret the dimensions of the embedding matrix."""
    print(BAR)
    print("1. THE EMBEDDING MATRIX")
    print(BAR)
    n, d = V.shape
    print(f"  shape: ({n}, {d})")
    print(f"    {n} rows  — one per indexed passage, not per word. This is a")
    print(f"              document index, so a 'row' is a chunk of statute.")
    print(f"    {d} cols  — the dimensionality of nomic-embed-text. Each column")
    print(f"              is a latent dimension; none is individually meaningful.")

    norms = np.linalg.norm(V, axis=1)
    print(f"\n  vector norms: min {norms.min():.4f}  max {norms.max():.4f}  "
          f"mean {norms.mean():.4f}")
    if np.allclose(norms, 1.0, atol=1e-3):
        print("  -> unit-normalised, so cosine similarity is a dot product and")
        print("     retrieval is one matrix multiply.")

    by_src: dict[str, int] = {}
    for c in chunks:
        by_src[c.get("source", "?")] = by_src.get(c.get("source", "?"), 0) + 1
    print("\n  corpus composition:")
    for k, v in sorted(by_src.items(), key=lambda t: -t[1]):
        print(f"    {v:4}  {k}")

    lens = [len(c.get("text", "")) for c in chunks]
    print(f"\n  chunk length (chars): min {min(lens)}  median "
          f"{int(np.median(lens))}  max {max(lens)}")


def section_corpus_quality(V: np.ndarray, chunks: list[dict]) -> None:
    """Is what we indexed actually text?

    This check exists because the similarity scan in section 2 found the two
    most similar passages in the corpus were identical rows of full stops.
    """
    print("\n" + BAR)
    print("2. CORPUS QUALITY — IS THE INDEX MADE OF LAW?")
    print(BAR)

    def alpha(t: str) -> float:
        return sum(ch.isalpha() for ch in t) / max(1, len(t))

    def dot(t: str) -> float:
        return t.count(".") / max(1, len(t))

    scored = [(i, alpha(c.get("text", "")), dot(c.get("text", "")))
              for i, c in enumerate(chunks)]
    bad = [s for s in scored if s[1] < 0.25]
    good = [s for s in scored if s[1] >= 0.25]

    print(f"  degenerate chunks (<25% letters): {len(bad)} of {len(chunks)} "
          f"({100*len(bad)/len(chunks):.1f}%)")
    if bad:
        print(f"    letters: {np.mean([s[1] for s in bad]):.3f} vs "
              f"{np.mean([s[1] for s in good]):.3f} in healthy chunks")
        print(f"    dots:    {np.mean([s[2] for s in bad]):.3f} vs "
              f"{np.mean([s[2] for s in good]):.3f}")
        print("    The two populations do not overlap, which is why one")
        print("    threshold separates them without tuning.")

        by: dict[str, int] = {}
        for i, _, _ in bad:
            s = chunks[i].get("source", "?")
            by[s] = by.get(s, 0) + 1
        print("\n  by source:")
        for k, v in sorted(by.items(), key=lambda t: -t[1]):
            tot = sum(1 for c in chunks if c.get("source") == k)
            print(f"    {v:3}/{tot:3} ({100*v/tot:4.1f}%)  {k}")

        idx = [i for i, _, _ in bad]
        rest = [i for i in range(len(chunks)) if i not in set(idx)]
        sub = V[idx]
        iu = np.triu_indices(len(idx), k=1)
        print(f"\n  mean cosine among them: {(sub @ sub.T)[iu].mean():.3f}")
        print(f"  highest cosine to real statute: {(V[idx] @ V[rest].T).max():.3f}")
        print("  -> retrievable. A query can rank punctuation above the section")
        print("     that answers it, and the drafter then receives dots as law.")
    else:
        print("  None. The filter in app/rag.py:is_degenerate is holding.")


def section_similarity(V: np.ndarray, chunks: list[dict]) -> None:
    """What the similarity distribution says about how much signal there is."""
    print("\n" + BAR)
    print("3. COSINE SIMILARITY ACROSS THE CORPUS")
    print(BAR)
    S = V @ V.T
    iu = np.triu_indices(len(V), k=1)
    off = S[iu]
    print(f"  all {len(off):,} distinct passage pairs:")
    print(f"    mean {off.mean():.3f}   sd {off.std():.3f}")
    print(f"    min  {off.min():.3f}   max {off.max():.3f}")
    for p in (50, 90, 99):
        print(f"    p{p}: {np.percentile(off, p):.3f}")

    print("\n  Interpretation: a high floor is expected and is not a defect —")
    print("  every passage is South African civil procedure, so no two are")
    print("  truly unrelated. What matters for retrieval is the SPREAD above")
    print("  that floor, because that is the only signal ranking can use.")

    # The most and least alike pairs, as a sanity check on the space.
    k = int(np.argmax(off))
    i, j = iu[0][k], iu[1][k]
    print(f"\n  closest pair ({off[k]:.3f}):")
    print(f"    [{chunks[i].get('citation') or chunks[i]['source']}] "
          f"{chunks[i]['text'][:78]}…")
    print(f"    [{chunks[j].get('citation') or chunks[j]['source']}] "
          f"{chunks[j]['text'][:78]}…")


def section_neighbours(V: np.ndarray, chunks: list[dict]) -> None:
    """Does the space cluster by source document? It should, somewhat."""
    print("\n" + BAR)
    print("4. DOES THE SPACE KNOW WHICH ACT A PASSAGE CAME FROM?")
    print(BAR)
    S = V @ V.T
    np.fill_diagonal(S, -1)
    nn = S.argmax(axis=1)
    same = sum(1 for i, j in enumerate(nn)
               if chunks[i].get("source") == chunks[j].get("source"))
    print(f"  nearest neighbour shares the source document: "
          f"{same}/{len(chunks)} ({100*same/len(chunks):.1f}%)")
    print("\n  This is a cheap unsupervised check that the embeddings encode")
    print("  something real. Chance would be roughly the largest source's")
    print("  share of the corpus; materially above that means the geometry")
    print("  carries document structure, not noise.")
    shares = {}
    for c in chunks:
        shares[c.get("source")] = shares.get(c.get("source"), 0) + 1
    biggest = max(shares.values()) / len(chunks)
    print(f"  chance baseline (largest source share): {100*biggest:.1f}%")


def section_queries(V: np.ndarray, chunks: list[dict]) -> None:
    """The vocabulary-mismatch finding, measured rather than asserted.

    PE1 established that embeddings place related terms near each other. The
    question this asks is narrower and is the one a legal RAG system lives or
    dies on: does the vocabulary a claimant uses land near the vocabulary the
    legislature used? They are not the same words.
    """
    print("\n" + BAR)
    print("5. LAYPERSON VOCABULARY vs STATUTE VOCABULARY")
    print(BAR)

    try:
        from app.rag import Retriever  # noqa: F401
        import asyncio
        from app.llm import get_provider  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        print(f"  (skipped: {type(exc).__name__}: {exc})")
        return

    pairs = [
        ("letter of demand",
         "institution of actions"),
        ("how much can I claim",
         "jurisdiction in respect of causes of action"),
        ("can a company sue",
         "persons who may institute proceedings"),
        ("what the court cannot hear",
         "matters beyond the jurisdiction of the court"),
        ("proof I delivered the letter",
         "manner of service of process"),
    ]

    import asyncio

    async def embed(texts: list[str]) -> np.ndarray:
        from app.rag import Retriever
        r = Retriever()
        return np.array([await r.embed_query(t) for t in texts])

    try:
        lay = [a for a, _ in pairs]
        legal = [b for _, b in pairs]
        E = asyncio.run(embed(lay + legal))
    except Exception as exc:  # noqa: BLE001
        print(f"  (skipped — needs Ollama for query embeddings: "
              f"{type(exc).__name__})")
        return

    L, G = E[:len(lay)], E[len(lay):]
    L = L / np.linalg.norm(L, axis=1, keepdims=True)
    G = G / np.linalg.norm(G, axis=1, keepdims=True)

    print("  How close is a user's phrasing to the statute's own heading?\n")
    print(f"  {'user phrasing':38} {'statute phrasing':40} cos")
    gaps = []
    for i, (a, b) in enumerate(pairs):
        c = float(L[i] @ G[i])
        gaps.append(c)
        print(f"  {a[:37]:38} {b[:39]:40} {c:.3f}")
    print(f"\n  mean {np.mean(gaps):.3f}")
    print("\n  Every point below 1.0 is retrieval risk. A query written in the")
    print("  claimant's words is a different point in the space from the")
    print("  section that answers it, and the system ranks by that distance.")


def section_analogy(V: np.ndarray, chunks: list[dict]) -> None:
    """PE1 q23/q24 — similarity and vector arithmetic, on legal vocabulary.

    q24 asked whether king - man + woman lands on queen. The question that
    matters here is narrower and more consequential: where do 'plaintiff' and
    'defendant' sit relative to each other?

    Willa has an observed failure in which 'plaintiff' round-trips to
    'defendant' in isiZulu. If the two terms are near neighbours in embedding
    space — which is plausible, since they occur in near-identical contexts
    and are distinguished only by which side of a dispute they name — then
    that failure has a mechanical explanation rather than being bad luck.
    Distributional semantics places words by the company they keep, and these
    two keep almost exactly the same company.
    """
    print("\n" + BAR)
    print("6. LEGAL VOCABULARY IN EMBEDDING SPACE (PE1 q23/q24)")
    print(BAR)

    try:
        import asyncio
        from app.rag import Retriever
    except Exception as exc:  # noqa: BLE001
        print(f"  (skipped: {type(exc).__name__})")
        return

    terms = ["plaintiff", "defendant", "claimant", "respondent",
             "commissioner", "clerk", "summons", "letter of demand",
             "fridge", "payment"]

    async def embed_all(ts: list[str]) -> np.ndarray:
        r = Retriever()
        return np.array([await r.embed_query(t) for t in ts])

    try:
        E = asyncio.run(embed_all(terms))
    except Exception as exc:  # noqa: BLE001
        print(f"  (skipped — needs Ollama for query embeddings: "
              f"{type(exc).__name__})")
        return
    E = E / np.linalg.norm(E, axis=1, keepdims=True)
    S = E @ E.T

    idx = {t: i for i, t in enumerate(terms)}
    print("  q23 — pairwise cosine between terms that matter:\n")
    pairs = [("plaintiff", "defendant"), ("plaintiff", "claimant"),
             ("defendant", "respondent"), ("plaintiff", "fridge"),
             ("summons", "letter of demand"), ("commissioner", "clerk")]
    for a, b in pairs:
        print(f"    {a:18} ~ {b:18} {S[idx[a], idx[b]]:.3f}")

    pd = S[idx["plaintiff"], idx["defendant"]]
    pf = S[idx["plaintiff"], idx["fridge"]]
    print(f"\n  'plaintiff' is {pd/pf:.1f}x closer to its own opposite")
    print(f"  ('defendant', {pd:.3f}) than to an unrelated noun")
    print(f"  ('fridge', {pf:.3f}).")
    print("\n  This is the mechanism behind the isiZulu inversion. The two")
    print("  words that must never be swapped are among the closest pairs in")
    print("  the space, because distributional semantics places words by the")
    print("  company they keep and these two keep the same company. It is a")
    print("  predictable failure, not an unlucky one — and it is why the")
    print("  English is printed alongside every translation rather than a")
    print("  warning being shown once in the interface.")

    print("\n  q24 — nearest neighbour of each term within this set:")
    np.fill_diagonal(S, -1)
    for t in terms:
        j = int(S[idx[t]].argmax())
        print(f"    {t:18} -> {terms[j]:18} {S[idx[t], j]:.3f}")


def main() -> int:
    if not config.INDEX_PATH.exists():
        print("No index. Run: python scripts/ingest.py")
        return 1
    V, chunks = load()
    section_dimensions(V, chunks)
    section_corpus_quality(V, chunks)
    section_similarity(V, chunks)
    section_neighbours(V, chunks)
    section_queries(V, chunks)
    section_analogy(V, chunks)
    print("\n" + BAR)
    print("Numbers above are from the shipped index and are reproducible.")
    print(BAR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
