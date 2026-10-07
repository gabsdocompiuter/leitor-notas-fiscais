from uuid import UUID

from sqlalchemy import delete, exists, func, or_, select, update
from sqlalchemy.orm import joinedload

from ..enums.situacao_nota import SituacaoNota
from ..entities import (
    ApresentacaoProdutoEntity, AssociacaoProdutoEntity, ItemEntity,
    NotaEntity, ProdutoEntity, VariacaoProdutoEntity,
)
from .base_repository import BaseRepository


class ProdutoRepository(BaseRepository[ProdutoEntity]):
    def listar(
        self, busca: str | None = None, categoria_id: UUID | None = None
    ) -> list[ProdutoEntity]:
        consulta = select(ProdutoEntity).options(joinedload(ProdutoEntity.categoria))
        if busca:
            consulta = consulta.where(ProdutoEntity.nome.ilike(f"%{busca}%"))
        if categoria_id:
            consulta = consulta.where(ProdutoEntity.categoria_id == categoria_id)
        return list(self.session.scalars(consulta.order_by(ProdutoEntity.nome)))

    def obter(self, entidade_id: UUID) -> ProdutoEntity | None:
        return self.session.scalar(
            select(ProdutoEntity)
            .options(joinedload(ProdutoEntity.categoria))
            .where(ProdutoEntity.id == entidade_id)
        )

    def obter_por_identidade(self, nome: str, categoria_id: UUID) -> ProdutoEntity | None:
        return self.session.scalar(
            select(ProdutoEntity)
            .options(joinedload(ProdutoEntity.categoria))
            .where(
                func.lower(ProdutoEntity.nome) == nome.lower(),
                ProdutoEntity.categoria_id == categoria_id,
            )
        )

    def adicionar(self, entidade: ProdutoEntity) -> ProdutoEntity:
        self.session.add(entidade)
        self.session.flush()
        return entidade

    def excluir(self, entidade: ProdutoEntity) -> None:
        # Exclusões explícitas evitam o ORM tentar anular FKs obrigatórias.
        self.session.execute(delete(AssociacaoProdutoEntity).where(
            self._vinculo_produto(AssociacaoProdutoEntity, entidade.id)
        ))
        self.session.execute(delete(ApresentacaoProdutoEntity).where(
            ApresentacaoProdutoEntity.produto_id == entidade.id
        ))
        self.session.execute(delete(VariacaoProdutoEntity).where(
            VariacaoProdutoEntity.produto_id == entidade.id
        ))
        self.session.execute(delete(ProdutoEntity).where(ProdutoEntity.id == entidade.id))

    @staticmethod
    def _vinculo_produto(modelo, produto_id: UUID):
        return or_(
            modelo.apresentacao_id.in_(select(ApresentacaoProdutoEntity.id).where(
                ApresentacaoProdutoEntity.produto_id == produto_id
            )),
            modelo.variacao_id.in_(select(VariacaoProdutoEntity.id).where(
                VariacaoProdutoEntity.produto_id == produto_id
            )),
        )

    def possui_itens(self, produto_id: UUID) -> bool:
        return bool(self.session.scalar(select(exists().where(
            self._vinculo_produto(ItemEntity, produto_id)
        ))))

    def possui_associacoes(self, produto_id: UUID) -> bool:
        return bool(self.session.scalar(select(exists().where(
            self._vinculo_produto(AssociacaoProdutoEntity, produto_id)
        ))))

    def possui_variacoes(self, produto_id: UUID) -> bool:
        return bool(self.session.scalar(select(exists().where(
            VariacaoProdutoEntity.produto_id == produto_id
        ))))

    def invalidar_revisoes_sem_marca(self, produto_id: UUID) -> None:
        self.session.execute(update(ItemEntity).where(
            ItemEntity.apresentacao_id.in_(select(ApresentacaoProdutoEntity.id).where(
                ApresentacaoProdutoEntity.produto_id == produto_id,
                ApresentacaoProdutoEntity.marca_id.is_(None),
            )),
            ItemEntity.nota_id.in_(select(NotaEntity.id).where(
                NotaEntity.situacao != SituacaoNota.IMPORTADA
            )),
        ).values(revisado=False))

    def possui_apresentacoes(self, entidade_id: UUID) -> bool:
        return bool(self.session.scalar(select(exists().where(ApresentacaoProdutoEntity.produto_id == entidade_id))))

    def esta_em_nota_importada(self, entidade_id: UUID) -> bool:
        consulta = (
            select(1)
            .select_from(ItemEntity)
            .join(NotaEntity, NotaEntity.id == ItemEntity.nota_id)
            .join(ApresentacaoProdutoEntity, ApresentacaoProdutoEntity.id == ItemEntity.apresentacao_id)
            .where(NotaEntity.situacao == SituacaoNota.IMPORTADA, ApresentacaoProdutoEntity.produto_id == entidade_id)
        )
        return bool(self.session.scalar(select(exists(consulta))))
