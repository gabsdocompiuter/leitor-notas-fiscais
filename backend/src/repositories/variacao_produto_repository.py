from decimal import Decimal
from uuid import UUID

from sqlalchemy import exists, select
from sqlalchemy.orm import joinedload

from ..enums.unidade_medida import UnidadeMedida
from ..enums.situacao_nota import SituacaoNota
from ..entities import ItemEntity, NotaEntity, ProdutoEntity, VariacaoProdutoEntity
from .base_repository import BaseRepository


class VariacaoProdutoRepository(BaseRepository[VariacaoProdutoEntity]):
    _carregamento = joinedload(VariacaoProdutoEntity.produto).joinedload(
        ProdutoEntity.categoria
    )

    def listar_por_produto(self, produto_id: UUID) -> list[VariacaoProdutoEntity]:
        consulta = (
            select(VariacaoProdutoEntity)
            .options(self._carregamento)
            .where(VariacaoProdutoEntity.produto_id == produto_id)
            .order_by(
                VariacaoProdutoEntity.quantidade,
                VariacaoProdutoEntity.unidade_medida,
                VariacaoProdutoEntity.descricao,
            )
        )
        return list(self.session.scalars(consulta))

    def obter(self, entidade_id: UUID) -> VariacaoProdutoEntity | None:
        return self.session.scalar(
            select(VariacaoProdutoEntity)
            .options(self._carregamento)
            .where(VariacaoProdutoEntity.id == entidade_id)
        )

    def obter_por_identidade(
        self, produto_id: UUID, quantidade: Decimal, unidade: UnidadeMedida
    ) -> VariacaoProdutoEntity | None:
        return self.session.scalar(
            select(VariacaoProdutoEntity)
            .options(self._carregamento)
            .where(
                VariacaoProdutoEntity.produto_id == produto_id,
                VariacaoProdutoEntity.quantidade == quantidade,
                VariacaoProdutoEntity.unidade_medida == unidade,
            )
        )

    def adicionar(self, entidade: VariacaoProdutoEntity) -> VariacaoProdutoEntity:
        self.session.add(entidade)
        self.session.flush()
        return entidade

    def esta_em_nota_importada(self, entidade_id: UUID) -> bool:
        consulta = (
            select(1)
            .select_from(ItemEntity)
            .join(NotaEntity, NotaEntity.id == ItemEntity.nota_id)
            .where(NotaEntity.situacao == SituacaoNota.IMPORTADA, ItemEntity.variacao_id == entidade_id)
        )
        return bool(self.session.scalar(select(exists(consulta))))
