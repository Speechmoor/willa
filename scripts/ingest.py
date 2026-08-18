#!/usr/bin/env python3
"""Chunk and embed the corpus into a local index.

    python scripts/ingest.py

Requires Ollama running with nomic-embed-text pulled. Embedding a few hundred
chunks on a laptop CPU takes a couple of minutes; it only needs to happen when
the corpus changes.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config          # noqa: E402
from app.rag import build_index  # noqa: E402


async def main() -> int:
    print(f"Corpus:  {config.CORPUS_DIR}")
    print(f"Index:   {config.INDEX_PATH}")
    print(f"Model:   {config.EMBED_MODEL} via {config.OLLAMA_HOST}\n")
    try:
        n = await build_index()
    except FileNotFoundError as exc:
        print(f"\n{exc}")
        return 1
    print(f"\nIndexed {n} chunks. Start the app: uvicorn app.main:app --reload")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
