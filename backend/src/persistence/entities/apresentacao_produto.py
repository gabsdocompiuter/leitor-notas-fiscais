from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Index, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

if TYPE_CHECKING:
    from .associacao_produto import AssociacaoProdutoEntity
    from .item import ItemEntity
    from .marca import MarcaEntity
    from .produto import ProdutoEntity


class ApresentacaoProdutoEntity(Base):
    __tablename__ = "apresentacoes_produto"
    __table_args__ = (
        Index(
            "uq_apresentacao_produto_marca",
            "produto_id",
            "marca_id",
            unique=True,
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    produto_id: Mapped[UUID] = mapped_column(ForeignKey("produtos.id"))
    marca_id: Mapped[UUID | None] = mapped_column(ForeignKey("marcas.id"))
    produto: Mapped[ProdutoEntity] = relationship(back_populates="apresentacoes")
    marca: Mapped[MarcaEntity | None] = relationship(back_populates="apresentacoes")
    itens: Mapped[list[ItemEntity]] = relationship(back_populates="apresentacao")
    associacoes: Mapped[list[AssociacaoProdutoEntity]] = relationship(
        back_populates="apresentacao"
    )

