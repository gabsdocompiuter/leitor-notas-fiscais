from uuid import UUID

from pydantic import BaseModel

from ...models.categoria import Categoria


class CategoriaResponse(BaseModel):
    id: UUID
    nome: str

    @classmethod
    def from_entity(cls, categoria: Categoria) -> "CategoriaResponse":
        return cls(id=categoria.id, nome=categoria.nome)
