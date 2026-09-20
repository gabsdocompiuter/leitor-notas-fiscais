from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

if TYPE_CHECKING:
    from .produto import ProdutoEntity


class CategoriaEntity(Base):
    __tablename__ = "categorias"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    nome: Mapped[str] = mapped_column(String(100, collation="NOCASE"), unique=True)
    produtos: Mapped[list[ProdutoEntity]] = relationship(back_populates="categoria")

