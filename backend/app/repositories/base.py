"""Base repository — DRY common CRUD operations for Beanie documents."""

from __future__ import annotations

from typing import Any, Generic, Optional, Type, TypeVar

from beanie import Document

T = TypeVar("T", bound=Document)


class BaseRepository(Generic[T]):
    """Generic async repository with common CRUD."""

    def __init__(self, model: Type[T]):
        self._model = model

    async def find_by_id(self, doc_id: Any) -> Optional[T]:
        return await self._model.get(doc_id)

    async def find_one(self, **filters) -> Optional[T]:
        return await self._model.find_one(filters)

    async def find_many(self, filters: dict | None = None, limit: int = 100) -> list[T]:
        q = self._model.find(filters or {})
        return await q.limit(limit).to_list()

    async def create(self, doc: T) -> T:
        await doc.insert()
        return doc

    async def update(self, doc: T) -> T:
        await doc.save()
        return doc

    async def delete(self, doc: T) -> None:
        await doc.delete()

    async def count(self, filters: dict | None = None) -> int:
        return await self._model.find(filters or {}).count()
