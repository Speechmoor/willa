"""Local inference provider.

One interface so a second backend can be added without touching callers. The
only implementation talks to Ollama over loopback.

This module never reads an API key and never resolves a non-loopback host, so
adding a remote backend would be a visible change here rather than a
configuration accident.
"""

from __future__ import annotations

import re
from typing import Protocol

import httpx

from . import config

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


class InferenceError(RuntimeError):
    pass


def _strip_thinking(text: str) -> str:
    if not config.STRIP_THINKING:
        return text
    cleaned = _THINK_RE.sub("", text)
    # An unterminated <think> means the model ran out of budget mid-reasoning.
    if "<think>" in cleaned:
        cleaned = cleaned.split("<think>")[0]
    return cleaned.strip()


class Provider(Protocol):
    async def chat(self, system: str, user: str, *, temperature: float = 0.2) -> str: ...
    async def embed(self, texts: list[str]) -> list[list[float]]: ...


class OllamaProvider:
    """Local Ollama. Loopback only."""

    def __init__(self, host: str | None = None, model: str | None = None) -> None:
        self.host = (host or config.OLLAMA_HOST).rstrip("/")
        # Normally None, meaning "use the configured model". Set only by
        # scripts/evaluate.py, which has to run the same prompt through several
        # models to compare them.
        self.model = model or config.CHAT_MODEL
        if not self.host.startswith(("http://127.0.0.1", "http://localhost")):
            raise InferenceError(
                f"Refusing to start: OLLAMA_HOST is {self.host!r}, which is not "
                "loopback. Willa's privacy guarantee depends on local inference."
            )

    async def chat(self, system: str, user: str, *, temperature: float = 0.2) -> str:
        payload = {
            "model": self.model,
            "stream": False,
            "options": {"temperature": temperature},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        async with httpx.AsyncClient(timeout=300.0) as client:
            try:
                r = await client.post(f"{self.host}/api/chat", json=payload)
                r.raise_for_status()
            except httpx.ConnectError as exc:
                raise InferenceError(
                    "Cannot reach Ollama on 127.0.0.1:11434. Start it with "
                    "`ollama serve`, then `ollama pull qwen3:8b`."
                ) from exc
            data = r.json()
        return _strip_thinking(data["message"]["content"])

    async def embed(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        async with httpx.AsyncClient(timeout=300.0) as client:
            for text in texts:
                try:
                    r = await client.post(
                        f"{self.host}/api/embeddings",
                        json={"model": config.EMBED_MODEL, "prompt": text},
                    )
                    r.raise_for_status()
                except httpx.ConnectError as exc:
                    raise InferenceError(
                        "Cannot reach Ollama. Run `ollama pull nomic-embed-text`."
                    ) from exc
                out.append(r.json()["embedding"])
        return out


def get_provider() -> Provider:
    return OllamaProvider()
