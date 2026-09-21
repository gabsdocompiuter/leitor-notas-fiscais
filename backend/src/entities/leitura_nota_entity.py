from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.persistence.base_entity import BaseEntity

if TYPE_CHECKING:
    from .nota_entity import NotaEntity


class LeituraNotaEntity(BaseEntity):
    __tablename__ = "leituras"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    chave: Mapped[str] = mapped_column(String(44), unique=True)
    url: Mapped[str] = mapped_column(String(2048))
    nota_id: Mapped[UUID | None] = mapped_column(ForeignKey("notas.id"))
    erro_consulta: Mapped[str | None] = mapped_column(String(1000))
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    nota: Mapped[NotaEntity | None] = relationship(back_populates="leituras")
