from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

class RevisaoItemRequest(BaseModel):
    produto_id: UUID
    marca_id: UUID | None = None
    variacao_id: UUID | None = None
    quantidade_confirmada: Decimal = Field(gt=0)
