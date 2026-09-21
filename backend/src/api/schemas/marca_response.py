from uuid import UUID

from pydantic import BaseModel

from ...dtos.marca_dto import MarcaDTO


class MarcaResponse(BaseModel):
    id: UUID
    nome: str

    @classmethod
    def from_entity(cls, marca: MarcaDTO) -> "MarcaResponse":
        return cls(id=marca.id, nome=marca.nome)
