"""Query cache — stores GPT responses in MongoDB with TTL.

Uses a hash of the normalized query to detect repeated / similar questions.
Avoids hitting GPT for the same question within the TTL window.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta
from typing import Any, Optional

from beanie import Document
from pymongo import IndexModel, ASCENDING

from app.config import settings


class CachedQuery(Document):
    """Cached agent response — expires via TTL index."""

    query_hash: str
    original_query: str
    reply: str
    tool_used: Optional[str] = None
    data: Optional[Any] = None
    created_at: datetime = datetime.utcnow()
    expires_at: datetime = datetime.utcnow() + timedelta(seconds=settings.CACHE_TTL_SECONDS)

    class Settings:
        name = "query_cache"
        indexes = [
            IndexModel([("query_hash", ASCENDING)], unique=True),
            IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0),
        ]


def _normalize(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    return re.sub(r"\s+", " ", text)


def compute_hash(query: str) -> str:
    """SHA-256 of normalized query."""
    return hashlib.sha256(_normalize(query).encode()).hexdigest()


async def get_cached(query: str) -> Optional[CachedQuery]:
    """Look up a cached response for a query."""
    h = compute_hash(query)
    return await CachedQuery.find_one(CachedQuery.query_hash == h)


async def set_cache(query: str, reply: str, tool_used: Optional[str] = None, data: Any = None) -> None:
    """Store a response in cache."""
    h = compute_hash(query)
    existing = await CachedQuery.find_one(CachedQuery.query_hash == h)
    if existing:
        existing.reply = reply
        existing.tool_used = tool_used
        existing.data = data
        existing.created_at = datetime.utcnow()
        existing.expires_at = datetime.utcnow() + timedelta(seconds=settings.CACHE_TTL_SECONDS)
        await existing.save()
    else:
        doc = CachedQuery(
            query_hash=h,
            original_query=query,
            reply=reply,
            tool_used=tool_used,
            data=data,
        )
        await doc.insert()


async def invalidate_cache() -> int:
    """Wipe all cached responses (called after write operations)."""
    result = await CachedQuery.find({}).delete()
    return result.deleted_count if result else 0
