"""Chat-memory adapter seam.

``ChatMemoryAdapter`` is the thin interface every platform bot (Discord, Slack,
Telegram) talks to, so the bot layer never calls cognee directly. This mirrors
the shared adapter proposed in #3608 — when that lands, its implementation drops
in here and the bot/service layers are untouched.

This branch ships ``CogneeSdkAdapter``, the in-process implementation that calls
the cognee Python SDK (``remember`` / ``recall`` / ``forget``) directly. A
sibling branch provides an HTTP-client implementation for talking to a running
cognee server instead.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class RecallResult:
    """Normalized recall payload the bot layer can render without knowing cognee."""

    answer: str
    sources: list[str] = field(default_factory=list)


class ChatMemoryAdapter(ABC):
    """Minimal memory surface a chat bot needs: remember, recall, forget."""

    @abstractmethod
    async def remember(
        self, text: str, *, dataset: str, session: str, provenance: Optional[dict] = None
    ) -> None:
        """Persist a message into memory under the given dataset/session."""

    @abstractmethod
    async def recall(
        self, query: str, *, dataset: str, session: str, top_k: int = 5
    ) -> RecallResult:
        """Answer a question from the dataset/session memory."""

    @abstractmethod
    async def forget(self, *, dataset: str, everything: bool = False) -> None:
        """Remove a dataset's memory (or everything the bot owns)."""


class CogneeSdkAdapter(ChatMemoryAdapter):
    """In-process adapter backed by the cognee Python SDK."""

    async def remember(
        self, text: str, *, dataset: str, session: str, provenance: Optional[dict] = None
    ) -> None:
        import cognee

        await cognee.remember(text, dataset_name=dataset, session_id=session)

    async def recall(
        self, query: str, *, dataset: str, session: str, top_k: int = 5
    ) -> RecallResult:
        import cognee

        results = await cognee.recall(
            query_text=query,
            datasets=[dataset],
            session_id=session,
            top_k=top_k,
            include_references=True,
        )
        texts = [t for t in (_result_text(r) for r in results) if t]
        return RecallResult(answer=texts[0] if texts else "", sources=texts)

    async def forget(self, *, dataset: str, everything: bool = False) -> None:
        import cognee

        await cognee.forget(dataset=dataset, everything=everything)


def _result_text(result: Any) -> str:
    """Best-effort text extraction across cognee recall result shapes.

    Recall returns graph entries (``.text``) and session QA entries
    (``.answer``); fall back to ``str`` so nothing silently disappears.
    """
    for attr in ("text", "answer"):
        value = getattr(result, attr, None)
        if isinstance(value, str) and value.strip():
            return value.strip()
    if isinstance(result, str):
        return result.strip()
    return ""
