from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.persistence.base_entity import BaseEntity
from ..core.persistence.types.decimal_text import DecimalText
from ..core.persistence.types.string_list import StringList

if TYPE_CHECKING:
    from .apresentacao_produto_entity import ApresentacaoProdutoEntity
    from .nota_entity import NotaEntity
    from .variacao_produto_entity import VariacaoProdutoEntity


class ItemEntity(BaseEntity):
    __tablename__ = "itens"
    __table_args__ = (UniqueConstraint("nota_id", "numero", name="uq_item_nota_numero"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    nota_id: Mapped[UUID] = mapped_column(ForeignKey("notas.id"))
    numero: Mapped[int] = mapped_column(Integer)
    codigo: Mapped[str] = mapped_column(String(100))
    descricao_original: Mapped[str] = mapped_column(String(500))
    quantidade: Mapped[Decimal] = mapped_column(DecimalText)
    unidade_original: Mapped[str] = mapped_column(String(20))
    valor_unitario: Mapped[Decimal] = mapped_column(DecimalText)
    valor_total: Mapped[Decimal] = mapped_column(DecimalText)
    alertas: Mapped[list[str]] = mapped_column(StringList)
    apresentacao_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("apresentacoes_produto.id")
    )
    variacao_id: Mapped[UUID | None] = mapped_column(ForeignKey("variacoes_produto.id"))
    quantidade_confirmada: Mapped[Decimal | None] = mapped_column(DecimalText)
    revisado: Mapped[bool] = mapped_column(Boolean, default=False)
    nota: Mapped[NotaEntity] = relationship(back_populates="itens")
    apresentacao: Mapped[ApresentacaoProdutoEntity | None] = relationship(
        back_populates="itens"
    )
    variacao: Mapped[VariacaoProdutoEntity | None] = relationship()
