from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

class RevisaoItemRequest(BaseModel):
    valor_total: Decimal | None = Field(default=None, ge=0, decimal_places=2, max_digits=15)
    valor_unitario: Decimal | None = Field(default=None, ge=0, decimal_places=2, max_digits=15)
    produto_id: UUID
    marca_id: UUID | None = None
    variacao_id: UUID | None = None
    quantidade_confirmada: Decimal = Field(gt=0, decimal_places=3)
    quantidade_pacotes: Decimal | None = Field(default=None, gt=0, decimal_places=0)
    unidades_por_pacote: Decimal | None = Field(default=None, gt=0, decimal_places=0)

    @model_validator(mode="after")
    def validar_valores(self):
        if self.valor_total is not None and self.valor_unitario is not None:
            raise ValueError("Informe o valor total ou o valor unitário, apenas um deles.")
        return self
