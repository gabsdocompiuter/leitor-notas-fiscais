from decimal import Decimal

from pydantic import BaseModel, Field

from ...enums.unidade_medida import UnidadeMedida


class VariacaoProdutoRequest(BaseModel):
    quantidade: Decimal = Field(gt=0, decimal_places=3)
    unidade_medida: UnidadeMedida
