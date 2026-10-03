from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..entities.tag_entity import TagEntity, itens_tags


class TagRepository:
    def __init__(self, session: Session):
        self.session = session

    def listar(self, busca: str | None = None) -> list[TagEntity]:
        consulta = (
            select(TagEntity)
            .outerjoin(itens_tags, itens_tags.c.tag_id == TagEntity.id)
            .group_by(TagEntity.id)
        )
        if busca:
            # contains escapa % e _, que fazem parte do nome informado.
            consulta = consulta.where(TagEntity.nome_normalizado.contains(busca, autoescape=True))
        return list(self.session.scalars(
            consulta.order_by(
                func.count(itens_tags.c.item_id).desc(), TagEntity.nome_normalizado
            ).limit(5)
        ))

    def obter_por_nome(self, nome_normalizado: str) -> TagEntity | None:
        return self.session.scalar(select(TagEntity).where(
            TagEntity.nome_normalizado == nome_normalizado
        ))

    def obter_varias(self, ids: set[UUID]) -> list[TagEntity]:
        return list(self.session.scalars(select(TagEntity).where(TagEntity.id.in_(ids))))

    def adicionar(self, entidade: TagEntity) -> TagEntity:
        self.session.add(entidade)
        self.session.flush()
        return entidade
