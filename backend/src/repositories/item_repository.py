from uuid import UUID

from sqlalchemy import select

from ..entities import ItemEntity
from .base_repository import BaseRepository


class ItemRepository(BaseRepository[ItemEntity]):
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
