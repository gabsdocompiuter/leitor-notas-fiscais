from uuid import UUID

from sqlalchemy import func, or_, select

from ..entities import EstabelecimentoEntity
from .base import Repository


class EstabelecimentoRepository(Repository[EstabelecimentoEntity]):
    def listar(self, busca: str | None = None) -> list[EstabelecimentoEntity]:
        consulta = select(EstabelecimentoEntity)
        if busca:
            termo = f"%{busca}%"
            consulta = consulta.where(
                or_(
                    EstabelecimentoEntity.razao_social.ilike(termo),
                    EstabelecimentoEntity.apelido.ilike(termo),
                )
            )
        ordem = func.coalesce(
            EstabelecimentoEntity.apelido, EstabelecimentoEntity.razao_social
        )
        return list(self.session.scalars(consulta.order_by(ordem)))

    def obter(self, entidade_id: UUID) -> EstabelecimentoEntity | None:
        return self.session.get(EstabelecimentoEntity, entidade_id)

    def obter_por_cnpj(self, cnpj: str) -> EstabelecimentoEntity | None:
        return self.session.scalar(
            select(EstabelecimentoEntity).where(EstabelecimentoEntity.cnpj == cnpj)
        )

    def adicionar(self, entidade: EstabelecimentoEntity) -> EstabelecimentoEntity:
        self.session.add(entidade)
        self.session.flush()
        return entidade
