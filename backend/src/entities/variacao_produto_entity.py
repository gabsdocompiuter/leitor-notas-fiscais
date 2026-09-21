from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..enums.unidade_medida import UnidadeMedida
from ..core.persistence.base_entity import BaseEntity
from ..core.persistence.types.decimal_text import DecimalText

if TYPE_CHECKING:
    from .produto_entity import ProdutoEntity


class VariacaoProdutoEntity(BaseEntity):
    __tablename__ = "variacoes_produto"
    __table_args__ = (
        UniqueConstraint(
            "produto_id", "quantidade", "unidade_medida", name="uq_variacao_produto"
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    produto_id: Mapped[UUID] = mapped_column(ForeignKey("produtos.id"))
    quantidade: Mapped[Decimal] = mapped_column(DecimalText)
    unidade_medida: Mapped[UnidadeMedida] = mapped_column(
        Enum(UnidadeMedida, values_callable=lambda enum: [item.value for item in enum])
    )
    descricao: Mapped[str | None] = mapped_column(String(100))
    produto: Mapped[ProdutoEntity] = relationship(back_populates="variacoes")
