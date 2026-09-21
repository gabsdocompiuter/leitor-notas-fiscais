from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.persistence.base_entity import BaseEntity

if TYPE_CHECKING:
    from .apresentacao_produto_entity import ApresentacaoProdutoEntity


class MarcaEntity(BaseEntity):
    __tablename__ = "marcas"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    nome: Mapped[str] = mapped_column(String(100, collation="NOCASE"), unique=True)
    apresentacoes: Mapped[list[ApresentacaoProdutoEntity]] = relationship(
        back_populates="marca"
    )
