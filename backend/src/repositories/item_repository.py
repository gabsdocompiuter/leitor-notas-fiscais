from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from ..entities import ItemEntity, NotaEntity
from ..enums.situacao_nota import SituacaoNota
from .base_repository import BaseRepository


class ItemRepository(BaseRepository[ItemEntity]):
    def listar_pendentes_aguardando(self) -> list[ItemEntity]:
        return list(self.session.scalars(
            select(ItemEntity)
            .join(ItemEntity.nota)
            .options(joinedload(ItemEntity.nota))
            .where(
                ItemEntity.revisado.is_(False),
                NotaEntity.situacao.in_((SituacaoNota.LIDA, SituacaoNota.EM_REVISAO)),
            )
            .order_by(ItemEntity.nota_id, ItemEntity.numero)
        ))

    def obter_na_nota(self, entidade_id: UUID, nota_id: UUID) -> ItemEntity | None:
        return self.session.scalar(
            select(ItemEntity).where(
                ItemEntity.id == entidade_id, ItemEntity.nota_id == nota_id
            )
        )

    def listar_pendentes(self, nota_id: UUID) -> list[ItemEntity]:
        return list(
            self.session.scalars(
                select(ItemEntity)
                .where(ItemEntity.nota_id == nota_id, ItemEntity.revisado.is_(False))
                .order_by(ItemEntity.numero)
            )
        )
