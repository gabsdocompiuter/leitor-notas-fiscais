from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

if TYPE_CHECKING:
    from .apresentacao_produto import ApresentacaoProdutoEntity


class MarcaEntity(Base):
    __tablename__ = "marcas"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    nome: Mapped[str] = mapped_column(String(100, collation="NOCASE"), unique=True)
    apresentacoes: Mapped[list[ApresentacaoProdutoEntity]] = relationship(
        back_populates="marca"
    )

