from uuid import UUID

from sqlalchemy import exists, func, select

from ..enums.situacao_nota import SituacaoNota
from ..entities import (
    ApresentacaoProdutoEntity, CategoriaEntity, ItemEntity, NotaEntity, ProdutoEntity,
)
from .base_repository import BaseRepository


class CategoriaRepository(BaseRepository[CategoriaEntity]):
    def listar(self, busca: str | None = None) -> list[CategoriaEntity]:
        consulta = select(CategoriaEntity)
        if busca:
            consulta = consulta.where(CategoriaEntity.nome.ilike(f"%{busca}%"))
        return list(self.session.scalars(consulta.order_by(CategoriaEntity.nome)))

    def obter(self, entidade_id: UUID) -> CategoriaEntity | None:
        return self.session.get(CategoriaEntity, entidade_id)

    def obter_por_nome(self, nome: str) -> CategoriaEntity | None:
        return self.session.scalar(
            select(CategoriaEntity).where(func.lower(CategoriaEntity.nome) == nome.lower())
        )

    def adicionar(self, entidade: CategoriaEntity) -> CategoriaEntity:
        self.session.add(entidade)
        self.session.flush()
        return entidade

    def excluir(self, entidade: CategoriaEntity) -> None:
        self.session.delete(entidade)

    def possui_produtos(self, entidade_id: UUID) -> bool:
        return bool(self.session.scalar(select(exists().where(ProdutoEntity.categoria_id == entidade_id))))

    def esta_em_nota_importada(self, entidade_id: UUID) -> bool:
        consulta = (
            select(1)
            .select_from(ItemEntity)
            .join(NotaEntity, NotaEntity.id == ItemEntity.nota_id)
            .join(ApresentacaoProdutoEntity, ApresentacaoProdutoEntity.id == ItemEntity.apresentacao_id)
            .join(ProdutoEntity, ProdutoEntity.id == ApresentacaoProdutoEntity.produto_id)
            .where(NotaEntity.situacao == SituacaoNota.IMPORTADA, ProdutoEntity.categoria_id == entidade_id)
        )
        return bool(self.session.scalar(select(exists(consulta))))
