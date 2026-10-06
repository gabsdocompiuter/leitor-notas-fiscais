from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

class RevisaoItemRequest(BaseModel):
    produto_id: UUID
    marca_id: UUID | None = None
    variacao_id: UUID | None = None
    quantidade_confirmada: Decimal = Field(gt=0, decimal_places=3)
    quantidade_pacotes: Decimal | None = Field(default=None, gt=0, decimal_places=0)
    unidades_por_pacote: Decimal | None = Field(default=None, gt=0, decimal_places=0)
