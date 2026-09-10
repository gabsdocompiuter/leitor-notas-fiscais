from uuid import UUID

from pydantic import BaseModel

from ...models.marca import Marca


class MarcaResponse(BaseModel):
    id: UUID
    nome: str

    @classmethod
    def from_entity(cls, marca: Marca) -> "MarcaResponse":
        return cls(id=marca.id, nome=marca.nome)
