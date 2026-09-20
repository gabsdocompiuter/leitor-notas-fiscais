from uuid import UUID

from sqlalchemy import or_, select

from ..entities import ApresentacaoProdutoEntity
from .base import Repository


class ApresentacaoProdutoRepository(Repository[ApresentacaoProdutoEntity]):
    def obter(self, entidade_id: UUID) -> ApresentacaoProdutoEntity | None:
        return self.session.get(ApresentacaoProdutoEntity, entidade_id)

    def obter_por_produto_marca(
        self, produto_id: UUID, marca_id: UUID | None
    ) -> ApresentacaoProdutoEntity | None:
        filtro_marca = (
            ApresentacaoProdutoEntity.marca_id == marca_id
            if marca_id is not None
            else ApresentacaoProdutoEntity.marca_id.is_(None)
        )
        return self.session.scalar(
            select(ApresentacaoProdutoEntity).where(
                ApresentacaoProdutoEntity.produto_id == produto_id, filtro_marca
            )
        )

    def adicionar(
        self, entidade: ApresentacaoProdutoEntity
    ) -> ApresentacaoProdutoEntity:
        self.session.add(entidade)
        self.session.flush()
        return entidade
