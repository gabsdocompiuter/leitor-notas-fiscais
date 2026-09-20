from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, Enum, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...models.unidade_medida import UnidadeMedida
from ..base import Base

if TYPE_CHECKING:
    from .apresentacao_produto import ApresentacaoProdutoEntity
    from .categoria import CategoriaEntity
    from .variacao_produto import VariacaoProdutoEntity


class ProdutoEntity(Base):
    __tablename__ = "produtos"
    __table_args__ = (
        UniqueConstraint("nome", "categoria_id", name="uq_produto_nome_categoria"),
        CheckConstraint(
            "(tratar_apenas_como_unidades = 1 AND contem_variacoes = 0 "
            "AND unidade_medida IS NULL) OR "
            "(tratar_apenas_como_unidades = 0 AND unidade_medida IS NOT NULL)",
            name="ck_produto_tipo",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    nome: Mapped[str] = mapped_column(String(150, collation="NOCASE"))
    categoria_id: Mapped[UUID] = mapped_column(ForeignKey("categorias.id"))
    nao_solicitar_marca: Mapped[bool] = mapped_column(Boolean, default=False)
    tratar_apenas_como_unidades: Mapped[bool] = mapped_column(Boolean, default=False)
    contem_variacoes: Mapped[bool] = mapped_column(Boolean, default=False)
    unidade_medida: Mapped[UnidadeMedida | None] = mapped_column(
        Enum(UnidadeMedida, values_callable=lambda enum: [item.value for item in enum])
    )
    categoria: Mapped[CategoriaEntity] = relationship(back_populates="produtos")
    variacoes: Mapped[list[VariacaoProdutoEntity]] = relationship(
        back_populates="produto"
    )
    apresentacoes: Mapped[list[ApresentacaoProdutoEntity]] = relationship(
        back_populates="produto"
    )

