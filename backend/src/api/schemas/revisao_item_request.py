from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from ...models.unidade_medida import UnidadeMedida


class RevisaoItemRequest(BaseModel):
    produto_id: UUID
    marca_id: UUID | None = None
    unidade_corrigida: UnidadeMedida
    quantidade_normalizada: Decimal = Field(gt=0)
