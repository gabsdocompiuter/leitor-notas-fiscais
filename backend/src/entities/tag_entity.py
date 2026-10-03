from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Column, ForeignKey, Index, String, Table, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.persistence.base_entity import BaseEntity

if TYPE_CHECKING:
    from .item_entity import ItemEntity


itens_tags = Table(
    "itens_tags",
    BaseEntity.metadata,
    Column("item_id", Uuid, ForeignKey("itens.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Uuid, ForeignKey("tags.id"), primary_key=True),
    Index("idx_itens_tags_tag", "tag_id"),
)


class TagEntity(BaseEntity):
    __tablename__ = "tags"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    nome: Mapped[str] = mapped_column(String(100))
    nome_normalizado: Mapped[str] = mapped_column(String(200), unique=True)
    itens: Mapped[list[ItemEntity]] = relationship(
        secondary=itens_tags, back_populates="tags"
    )
