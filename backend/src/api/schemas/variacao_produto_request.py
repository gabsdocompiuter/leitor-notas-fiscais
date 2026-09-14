from decimal import Decimal

from pydantic import BaseModel, Field

from ...models.unidade_medida import UnidadeMedida


class VariacaoProdutoRequest(BaseModel):
    quantidade: Decimal = Field(gt=0)
    unidade_medida: UnidadeMedida
    descricao: str | None = Field(default=None, max_length=100)
