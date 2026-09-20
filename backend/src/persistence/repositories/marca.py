from uuid import UUID

from sqlalchemy import exists, func, select

from ...models.situacao_nota import SituacaoNota
from ..entities import ApresentacaoProdutoEntity, ItemEntity, MarcaEntity, NotaEntity
from .base import Repository


class MarcaRepository(Repository[MarcaEntity]):
    def listar(self, busca: str | None = None) -> list[MarcaEntity]:
        consulta = select(MarcaEntity)
        if busca:
            consulta = consulta.where(MarcaEntity.nome.ilike(f"%{busca}%"))
        return list(self.session.scalars(consulta.order_by(MarcaEntity.nome)))

    def obter(self, entidade_id: UUID) -> MarcaEntity | None:
        return self.session.get(MarcaEntity, entidade_id)

    def obter_por_nome(self, nome: str) -> MarcaEntity | None:
        return self.session.scalar(
            select(MarcaEntity).where(func.lower(MarcaEntity.nome) == nome.lower())
        )

    def adicionar(self, entidade: MarcaEntity) -> MarcaEntity:
        self.session.add(entidade)
        self.session.flush()
        return entidade

    def excluir(self, entidade: MarcaEntity) -> None:
        self.session.delete(entidade)

    def possui_apresentacoes(self, entidade_id: UUID) -> bool:
        return bool(self.session.scalar(select(exists().where(ApresentacaoProdutoEntity.marca_id == entidade_id))))

    def esta_em_nota_importada(self, entidade_id: UUID) -> bool:
        consulta = (
            select(1)
            .select_from(ItemEntity)
            .join(NotaEntity, NotaEntity.id == ItemEntity.nota_id)
            .join(ApresentacaoProdutoEntity, ApresentacaoProdutoEntity.id == ItemEntity.apresentacao_id)
            .where(NotaEntity.situacao == SituacaoNota.IMPORTADA, ApresentacaoProdutoEntity.marca_id == entidade_id)
        )
        return bool(self.session.scalar(select(exists(consulta))))
