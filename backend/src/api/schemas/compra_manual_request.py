from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from .revisao_item_request import RevisaoItemRequest


class ItemCompraManualRequest(RevisaoItemRequest):
    @model_validator(mode="after")
    def exigir_valor(self):
        if self.valor_total is None and self.valor_unitario is None:
            raise ValueError("Informe o valor total ou unitário do item.")
        return self


class CompraManualRequest(BaseModel):
    estabelecimento_id: UUID
    data: date
    itens: list[ItemCompraManualRequest] = Field(min_length=1)
