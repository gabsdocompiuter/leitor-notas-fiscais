from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base
from ..types import DecimalText

if TYPE_CHECKING:
    from .apresentacao_produto import ApresentacaoProdutoEntity
    from .estabelecimento import EstabelecimentoEntity
    from .variacao_produto import VariacaoProdutoEntity


class AssociacaoProdutoEntity(Base):
    __tablename__ = "associacoes_produto"
    __table_args__ = (
        UniqueConstraint(
            "estabelecimento_id", "codigo_item", name="uq_associacao_estabelecimento_codigo"
        ),
        Index("idx_associacoes_descricao", "descricao_normalizada"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    estabelecimento_id: Mapped[UUID] = mapped_column(ForeignKey("estabelecimentos.id"))
    codigo_item: Mapped[str] = mapped_column(String(100))
    descricao_original: Mapped[str] = mapped_column(String(500))
    descricao_normalizada: Mapped[str] = mapped_column(String(500))
    apresentacao_id: Mapped[UUID] = mapped_column(ForeignKey("apresentacoes_produto.id"))
    variacao_id: Mapped[UUID | None] = mapped_column(ForeignKey("variacoes_produto.id"))
    fator_conversao: Mapped[Decimal] = mapped_column(DecimalText)
    estabelecimento: Mapped[EstabelecimentoEntity] = relationship(
        back_populates="associacoes"
    )
    apresentacao: Mapped[ApresentacaoProdutoEntity] = relationship(
        back_populates="associacoes"
    )
    variacao: Mapped[VariacaoProdutoEntity | None] = relationship()
