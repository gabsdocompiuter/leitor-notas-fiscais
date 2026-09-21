from uuid import UUID

from pydantic import BaseModel

from ...dtos.categoria_dto import CategoriaDTO


class CategoriaResponse(BaseModel):
    id: UUID
    nome: str

    @classmethod
    def from_entity(cls, categoria: CategoriaDTO) -> "CategoriaResponse":
        return cls(id=categoria.id, nome=categoria.nome)
