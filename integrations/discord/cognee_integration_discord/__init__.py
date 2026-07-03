"""Cognee-backed memory for Discord servers (per-guild/per-channel isolation).

Public surface:
    - ChatMemoryAdapter / CogneeSdkAdapter — the memory seam (see #3608)
    - MemoryService — platform-agnostic bot behavior
    - build_cog / run — discord.py wiring
"""

from .adapter import ChatMemoryAdapter, CogneeSdkAdapter, RecallResult
from .service import AnswerResult, MemoryService

__all__ = [
    "ChatMemoryAdapter",
    "CogneeSdkAdapter",
    "RecallResult",
    "MemoryService",
    "AnswerResult",
]
