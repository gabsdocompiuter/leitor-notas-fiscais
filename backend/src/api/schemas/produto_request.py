from uuid import UUID

from pydantic import BaseModel, Field

from ...models.unidade_medida import UnidadeMedida


class ProdutoRequest(BaseModel):
    nome: str = Field(min_length=1, max_length=150, examples=["Leite integral"])
    categoria_id: UUID
    unidade_base: UnidadeMedida
    nao_solicitar_marca: bool = False
