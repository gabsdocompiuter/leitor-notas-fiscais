from uuid import UUID

from sqlalchemy import exists, func, select
from sqlalchemy.orm import joinedload

from ..enums.situacao_nota import SituacaoNota
from ..entities import ApresentacaoProdutoEntity, ItemEntity, NotaEntity, ProdutoEntity
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
        self.session.delete(entidade)

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
