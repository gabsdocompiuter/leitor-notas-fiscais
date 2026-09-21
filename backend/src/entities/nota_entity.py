from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..enums.situacao_nota import SituacaoNota
from ..core.persistence.base_entity import BaseEntity
from ..core.persistence.types.decimal_text import DecimalText

if TYPE_CHECKING:
    from .estabelecimento_entity import EstabelecimentoEntity
    from .item_entity import ItemEntity
    from .leitura_nota_entity import LeituraNotaEntity


class NotaEntity(BaseEntity):
    __tablename__ = "notas"
    __table_args__ = (Index("idx_notas_emissao", "emissao"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    chave: Mapped[str] = mapped_column(String(44), unique=True)
    numero: Mapped[str] = mapped_column(String(20))
    serie: Mapped[str] = mapped_column(String(10))
    estabelecimento_id: Mapped[UUID] = mapped_column(ForeignKey("estabelecimentos.id"))
    emissao: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    quantidade_itens: Mapped[int] = mapped_column(Integer)
    valor_total: Mapped[Decimal] = mapped_column(DecimalText)
    desconto: Mapped[Decimal] = mapped_column(DecimalText)
    valor_a_pagar: Mapped[Decimal] = mapped_column(DecimalText)
    url_origem: Mapped[str] = mapped_column(String(2048))
    situacao: Mapped[SituacaoNota] = mapped_column(
        Enum(SituacaoNota, values_callable=lambda enum: [item.value for item in enum]),
        default=SituacaoNota.LIDA,
    )
    importada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    estabelecimento: Mapped[EstabelecimentoEntity] = relationship(back_populates="notas")
    itens: Mapped[list[ItemEntity]] = relationship(
        back_populates="nota", cascade="all, delete-orphan", order_by="ItemEntity.numero"
    )
    leituras: Mapped[list[LeituraNotaEntity]] = relationship(back_populates="nota")
