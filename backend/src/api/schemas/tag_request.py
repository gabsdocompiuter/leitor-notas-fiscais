from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from ...core.utils import limpar_nome


class TagRequest(BaseModel):
    nome: str = Field(min_length=1, max_length=100)

    @field_validator("nome", mode="before")
    @classmethod
    def limpar(cls, valor: object) -> object:
        return limpar_nome(valor) if isinstance(valor, str) else valor


class TagsItemRequest(BaseModel):
    tag_ids: list[UUID]
