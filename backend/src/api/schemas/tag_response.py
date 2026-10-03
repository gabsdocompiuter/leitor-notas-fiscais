from uuid import UUID
from pydantic import BaseModel

from ...dtos.tag_dto import TagDTO


class TagResponse(BaseModel):
    id: UUID
    nome: str

    @classmethod
    def from_entity(cls, tag: TagDTO) -> "TagResponse":
        return cls(id=tag.id, nome=tag.nome)
