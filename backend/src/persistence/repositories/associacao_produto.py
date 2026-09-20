from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from ..entities import (
    ApresentacaoProdutoEntity,
    AssociacaoProdutoEntity,
    ProdutoEntity,
)
from .base import Repository


class AssociacaoProdutoRepository(Repository[AssociacaoProdutoEntity]):
    _carregamento = (
        joinedload(AssociacaoProdutoEntity.apresentacao)
        .joinedload(ApresentacaoProdutoEntity.produto)
        .joinedload(ProdutoEntity.categoria)
    )

    def obter_por_codigo(
        self, estabelecimento_id: UUID, codigo_item: str
    ) -> AssociacaoProdutoEntity | None:
        return self.session.scalar(
            select(AssociacaoProdutoEntity)
            .options(self._carregamento)
            .where(
                AssociacaoProdutoEntity.estabelecimento_id == estabelecimento_id,
                AssociacaoProdutoEntity.codigo_item == codigo_item,
            )
        )

    def listar_por_descricao(
        self, descricao_normalizada: str
    ) -> list[AssociacaoProdutoEntity]:
        return list(
            self.session.scalars(
                select(AssociacaoProdutoEntity)
                .options(self._carregamento)
                .where(
                    AssociacaoProdutoEntity.descricao_normalizada
                    == descricao_normalizada
                )
            )
        )

    def adicionar(self, entidade: AssociacaoProdutoEntity) -> AssociacaoProdutoEntity:
        self.session.add(entidade)
        self.session.flush()
        return entidade
