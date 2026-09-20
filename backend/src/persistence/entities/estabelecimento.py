from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

if TYPE_CHECKING:
    from .associacao_produto import AssociacaoProdutoEntity
    from .nota import NotaEntity


class EstabelecimentoEntity(Base):
    __tablename__ = "estabelecimentos"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    cnpj: Mapped[str] = mapped_column(String(14), unique=True)
    razao_social: Mapped[str] = mapped_column(String(200))
    apelido: Mapped[str | None] = mapped_column(String(100))
    notas: Mapped[list[NotaEntity]] = relationship(back_populates="estabelecimento")
    associacoes: Mapped[list[AssociacaoProdutoEntity]] = relationship(
        back_populates="estabelecimento"
    )

