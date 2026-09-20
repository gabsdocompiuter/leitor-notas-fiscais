from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from ..entities import (
    ApresentacaoProdutoEntity,
    ItemEntity,
    LeituraNotaEntity,
    NotaEntity,
    ProdutoEntity,
    VariacaoProdutoEntity,
)
from .base import Repository


class LeituraNotaRepository(Repository[LeituraNotaEntity]):
    @staticmethod
    def _opcoes() -> tuple[object, ...]:
        apresentacao = joinedload(ItemEntity.apresentacao)
        nota = joinedload(LeituraNotaEntity.nota)
        return (
            nota.joinedload(NotaEntity.estabelecimento),
            nota.selectinload(NotaEntity.itens).options(
                apresentacao.joinedload(ApresentacaoProdutoEntity.produto).joinedload(
                    ProdutoEntity.categoria
                ),
                apresentacao.joinedload(ApresentacaoProdutoEntity.marca),
                joinedload(ItemEntity.variacao)
                .joinedload(VariacaoProdutoEntity.produto)
                .joinedload(ProdutoEntity.categoria),
            ),
        )

    def obter(self, entidade_id: UUID) -> LeituraNotaEntity | None:
        return self.session.scalar(
            select(LeituraNotaEntity)
            .options(*self._opcoes())
            .where(LeituraNotaEntity.id == entidade_id)
        )

    def obter_por_chave(self, chave: str) -> LeituraNotaEntity | None:
        return self.session.scalar(
            select(LeituraNotaEntity)
            .options(*self._opcoes())
            .where(LeituraNotaEntity.chave == chave)
        )

    def adicionar(
        self, chave: str, url: str, criada_em: datetime
    ) -> LeituraNotaEntity:
        entidade = LeituraNotaEntity(chave=chave, url=url, criada_em=criada_em)
        self.session.add(entidade)
        self.session.flush()
        return entidade
