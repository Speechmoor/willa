"""Retrieval over the local statutory corpus.

A NumPy cosine index rather than a vector database: the corpus is a handful of
statutes, so an exhaustive matrix multiply is faster than an approximate index
and has no dependencies. Nothing here touches the network except through
llm.embed, which is loopback only.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np

from . import config
from .llm import get_provider


@dataclass
class Chunk:
    id: int
    text: str
    source: str          # human-readable document title
    citation: str        # e.g. "s29(1)" or "rule 7(2)" where detectable
    path: str


# Section headings, used to attach a citation to each chunk. Formatting is
# inconsistent across publishers, so the trailing period is optional.
_SECTION_RE = re.compile(
    r"^[ \t]*(?:"
    r"(?P<rule>[Rr]ule)[ \t]+(?P<rnum>\d{1,3}[A-Za-z]?(?:\([^)]{1,6}\))*)"
    # Title is either Title Case ("Institution of actions") or ALL CAPS, which
    # the Consumer Protection Act uses for its section headings.
    r"|(?P<snum>\d{1,3}[A-Za-z]?)\.?[ \t]+(?P<title>[A-Z][a-z]{2,}|[A-Z]{3,})"
    r")",
    re.MULTILINE,
)


def _is_rules_document(title: str) -> bool:
    """Rules are numbered as rules, Acts as sections."""
    t = title.lower()
    return "rule" in t or "regulation" in t


def _detect_citation(text: str, doc_kind: str) -> str:
    m = _SECTION_RE.search(text)
    if not m:
        return ""
    numbered_as_rules = _is_rules_document(doc_kind)
    if m.group("rule"):
        return f"rule {m.group('rnum')}"
    if m.group("snum"):
        num = m.group("snum")
        return f"rule {num}" if numbered_as_rules else f"s{num}"
    return ""


# Optional English lexicon, used by _clean() to decide whether a line break
# fell inside a word. Absent is fine; the cleaner falls back to inserting a
# space. Install with: python -c "import nltk; nltk.download('words')"
try:
    from nltk.corpus import words as _nltk_words
    _WORDS = frozenset(w.lower() for w in _nltk_words.words())
except Exception:  # noqa: BLE001
    _WORDS = frozenset()


def _clean(text: str) -> str:
    """Undo the source PDF's line layout.

    Extractors report lines as they are placed on the page, so breaks fall
    mid-sentence and sometimes mid-word. Both damage retrieval, because the
    embedding model sees fragments rather than words. Split words are rejoined
    first, then soft wraps are unwrapped.
    """
    text = text.replace("\r\n", "\n").replace("\xa0", " ")

    # 1. Hyphenated break: unambiguous, always a split word.
    #    "pro-\nmotions" -> "promotions"
    text = re.sub(r"([A-Za-z])-\n([a-z])", r"\1\2", text)

    # 2. Un-hyphenated break between two letters is ambiguous: "of\nfers" is a
    # split word, "for\ndamages" is a soft wrap.
    text = re.sub(r"(?<![.;:?!])\n(?=[a-z])",
                  lambda m: " ", text) if not _WORDS else re.sub(
        r"([A-Za-z]+)\n([a-z]+)",
        lambda m: (m.group(1) + m.group(2)
                   if (m.group(2).lower() not in _WORDS
                       and (m.group(1) + m.group(2)).lower() in _WORDS)
                   else m.group(1) + " " + m.group(2)),
        text)

    # 3. Any remaining break not after terminal punctuation and followed by
    #    a lowercase letter is a soft wrap.
    text = re.sub(r"(?<![.;:?!])\n(?=[a-z])", " ", text)

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def is_degenerate(piece: str, min_alpha: float = 0.25) -> bool:
    """True if a chunk is typography rather than text.

    Table-of-contents dot leaders survive PDF extraction as passages of almost
    pure punctuation. They embed close enough to real statute to be retrieved,
    so they are rejected at ingestion. Real passages average about 75% letters
    and leader lines about 5%, so the threshold needs no tuning.
    """
    if not piece:
        return True
    letters = sum(1 for ch in piece if ch.isalpha())
    return (letters / len(piece)) < min_alpha


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    """Paragraph-aware sliding window."""
    text = _clean(text)
    paras = [p for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    buf = ""
    for para in paras:
        if len(buf) + len(para) + 2 <= size:
            buf = f"{buf}\n\n{para}" if buf else para
            continue
        if buf:
            chunks.append(buf)
        if len(para) <= size:
            buf = para
        else:
            # Hard-wrap an oversized paragraph.
            for i in range(0, len(para), size - overlap):
                piece = para[i : i + size]
                if len(piece) > overlap or not chunks:
                    chunks.append(piece)
            buf = ""
    if buf:
        chunks.append(buf)
    return chunks


def _is_blank_form(filename: str) -> bool:
    """Blank forms stay out of the index.

    A blank form matches any query about that form and displaces the Act and
    the Rules, and its text is already in the prompt as the skeleton.
    """
    return filename.lower().startswith("form_")


# Files in corpus/ that are not law. fetch_corpus.py writes its provenance
# record alongside the documents it describes, and build_chunks globs *.md,
# so the manifest would otherwise be indexed and retrieved as statute.
_NOT_CORPUS = {"manifest.md", "manifest.json", "readme.md"}


def _is_not_law(filename: str) -> bool:
    return filename.lower() in _NOT_CORPUS or _is_blank_form(filename)


# A trailing or leading page number, removed before comparing two lines.
_PAGE_NUM = re.compile(r"^\s*(?:page\s*)?\d{1,4}\s*|\s*(?:page\s*)?\d{1,4}\s*$",
                       re.IGNORECASE)


def _furniture_key(line: str) -> str:
    return _PAGE_NUM.sub("", _PAGE_NUM.sub("", line.strip())).strip()


def _strip_running_furniture(
    pages: list[str], min_pages: int = 3, min_share: float = 0.40,
    edge: int = 3,
) -> list[str]:
    """Remove running headers and footers.

    Detected by repetition rather than by matching known strings: a line that
    recurs across a large share of a document's pages and sits in the top or
    bottom `edge` lines of its page is page furniture.

    Both guards are needed. Repetition alone removed a commencement note that
    recurred because several provisions commenced on the same day. `min_share`
    is below a majority because some running headers survive extraction on
    only part of a document.

    Must run before _clean(), which dissolves the page boundaries this relies on.
    """
    if len(pages) < min_pages:
        return pages

    seen: Counter[str] = Counter()
    for page in pages:
        lines = [ln for ln in page.split("\n") if ln.strip()]
        # Set, not list: a line repeated twice on the same page is a
        # formatting quirk, not evidence of a running header.
        seen.update({_furniture_key(ln) for ln in lines[:edge] + lines[-edge:]
                     if len(_furniture_key(ln)) > 20})

    threshold = max(min_pages, int(len(pages) * min_share))
    boiler = {ln for ln, n in seen.items() if n >= threshold}
    if not boiler:
        return pages

    return ["\n".join(ln for ln in page.split("\n")
                      if _furniture_key(ln) not in boiler) for page in pages]


def _read_document(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("pip install pypdf to ingest PDFs") from exc
        reader = PdfReader(str(path))
        # Government forms are often encrypted with an empty password purely to
        # restrict editing. That is not a real lock and pypdf opens it, given a
        # crypt provider.
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception as exc:  # noqa: BLE001
                raise RuntimeError(
                    f"encrypted and would not open with an empty password: {exc}"
                ) from exc
        pages = [(page.extract_text() or "") for page in reader.pages]
        return "\n\n".join(_strip_running_furniture(pages))
    return path.read_text(encoding="utf-8", errors="replace")


def build_chunks(corpus_dir: Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    cid = 0
    files = sorted(
        p for p in corpus_dir.rglob("*")
        if p.suffix.lower() in {".pdf", ".txt", ".md"}
        and p.is_file()
        and not _is_not_law(p.name)
    )
    if not files:
        raise FileNotFoundError(
            f"No documents in {corpus_dir}. Run: python scripts/fetch_corpus.py"
        )
    skipped: list[tuple[str, str]] = []
    for path in files:
        # One unreadable document must not take down the whole corpus. Report
        # it loudly at the end and carry on with the rest.
        try:
            raw = _read_document(path)
        except Exception as exc:  # noqa: BLE001
            reason = str(exc) or type(exc).__name__
            print(f"  ! {path.name}: SKIPPED — {reason}")
            skipped.append((path.name, reason))
            continue
        if not raw.strip():
            reason = "no extractable text (scanned image? needs OCR)"
            print(f"  ! {path.name}: SKIPPED — {reason}")
            skipped.append((path.name, reason))
            continue

        title = path.stem.replace("_", " ").replace("-", " ")
        before = cid
        # A section runs across several chunks but only one of them contains
        # the heading. Carry the last heading forward so every chunk is
        # citable, and mark inherited ones so a reader knows the difference.
        current = ""
        labelled = 0
        dropped = 0
        for piece in chunk_text(raw, config.CHUNK_CHARS, config.CHUNK_OVERLAP):
            # Table-of-contents leader lines are typography, not law. See
            # is_degenerate() for the measurement that motivated this.
            if is_degenerate(piece):
                dropped += 1
                continue
            found = _detect_citation(piece, title)
            if found:
                current = found
                labelled += 1
                citation = found
            else:
                citation = f"{current} cont." if current else ""
            chunks.append(
                Chunk(
                    id=cid,
                    text=piece,
                    source=title,
                    citation=citation,
                    path=str(path.relative_to(corpus_dir)),
                )
            )
            cid += 1
        n = cid - before
        note = f", {dropped} dropped as table-of-contents" if dropped else ""
        print(f"  + {path.name}: {n} chunks ({labelled} with a heading{note})")

    if skipped:
        print(f"\n  {len(skipped)} of {len(files)} document(s) skipped:")
        for name, reason in skipped:
            print(f"    - {name}: {reason}")
        print("  Retrieval will not cover these. Fix or replace them and re-run.")
    if not chunks:
        raise RuntimeError(
            "Every document failed to parse. Nothing to index."
        )
    return chunks


# nomic-embed-text is trained with task prefixes and its retrieval quality
# degrades noticeably without them: documents and queries land in the same
# undifferentiated region and cosine scores bunch up around 0.7.
DOC_PREFIX = "search_document: "
QUERY_PREFIX = "search_query: "


async def build_index() -> int:
    chunks = build_chunks(config.CORPUS_DIR)
    provider = get_provider()
    print(f"Embedding {len(chunks)} chunks with {config.EMBED_MODEL}…")
    vectors = await provider.embed([DOC_PREFIX + c.text for c in chunks])
    matrix = np.array(vectors, dtype=np.float32)
    matrix /= np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-9

    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(config.INDEX_PATH, vectors=matrix)
    config.CHUNKS_PATH.write_text(
        json.dumps([asdict(c) for c in chunks], ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    return len(chunks)


class Retriever:
    def __init__(self) -> None:
        if not config.INDEX_PATH.exists():
            raise FileNotFoundError(
                "No index. Run: python scripts/ingest.py"
            )
        self.vectors: np.ndarray = np.load(config.INDEX_PATH)["vectors"]
        self.chunks: list[dict] = json.loads(
            config.CHUNKS_PATH.read_text(encoding="utf-8")
        )
        self.provider = get_provider()

    async def search(self, query: str, k: int = config.TOP_K) -> list[dict]:
        qvec = (await self.provider.embed([QUERY_PREFIX + query]))[0]
        q = np.array(qvec, dtype=np.float32)
        q /= np.linalg.norm(q) + 1e-9
        scores = self.vectors @ q
        top = np.argsort(-scores)[:k]
        results = []
        for i in top:
            chunk = dict(self.chunks[int(i)])
            chunk["score"] = float(scores[int(i)])
            results.append(chunk)
        return results

    async def search_grouped(
        self, claim_text: str, k_total: int = config.TOP_K
    ) -> list[dict]:
        """Retrieve for a draft, spread across source documents.

    A single query drawn from the user's story tends to return one document.
    Querying per document and interleaving the results keeps the Act, the
    Rules and the Consumer Protection Act all represented.
    """
        # Worded to match the statute's own vocabulary, not the user's. The
        # governing provision is headed "Institution of actions", not "letter
        # of demand", so a query phrased the obvious way never reaches it.
        procedural = (
            "institution of actions; the plaintiff shall deliver a summons to "
            "the clerk of the court together with a copy of a written demand "
            "delivered to the defendant by hand or by registered post allowing "
            "at least 14 days to satisfy the claim; contents of the letter of "
            "demand; affidavit proving delivery"
        )
        jurisdiction = (
            "jurisdiction of the small claims court; monetary limit of claims; "
            "matters excluded from the court's jurisdiction"
        )
        substance = claim_text[:600]

        # Procedural grounding is non-negotiable, so it gets the largest share.
        plan = [(procedural, max(2, k_total // 2)), (substance, 2), (jurisdiction, 1)]

        merged: dict[int, dict] = {}
        for query, k in plan:
            for hit in await self.search(query, k):
                prev = merged.get(hit["id"])
                if prev is None or hit["score"] > prev["score"]:
                    merged[hit["id"]] = hit
        return sorted(merged.values(), key=lambda h: -h["score"])[:k_total]


def format_context(results: list[dict]) -> str:
    """Numbered, citable context block for the drafting prompt."""
    parts = []
    for n, r in enumerate(results, 1):
        label = f"{r['source']}"
        if r.get("citation"):
            label += f", {r['citation']}"
        parts.append(f"[{n}] {label}\n{r['text']}")
    return "\n\n---\n\n".join(parts)
