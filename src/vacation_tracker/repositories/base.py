"""Thin generic repository base — shared CRUD only."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from vacation_tracker.db.base import Base


class BaseRepository[ModelT: Base]:
    """Minimal persistence helpers shared by concrete repositories."""

    def __init__(self, session: Session, model: type[ModelT]) -> None:
        self._session = session
        self._model = model

    def get_by_id(self, entity_id: uuid.UUID) -> ModelT | None:
        return self._session.get(self._model, entity_id)

    def add(self, entity: ModelT) -> ModelT:
        self._session.add(entity)
        return entity

    def delete(self, entity: ModelT) -> None:
        self._session.delete(entity)
