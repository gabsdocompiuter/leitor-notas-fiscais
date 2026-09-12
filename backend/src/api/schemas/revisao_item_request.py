from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from ...models.unidade_medida import UnidadeMedida


class RevisaoItemRequest(BaseModel):
    produto_id: UUID
    marca_id: UUID | None = None
    marca_confirmada: bool
    conteudo_embalagem: Decimal | None = Field(default=None, gt=0)
    unidade_embalagem: UnidadeMedida | None = None
    unidade_corrigida: UnidadeMedida
    quantidade_normalizada: Decimal = Field(gt=0)

    @model_validator(mode="after")
    def validar_embalagem(self) -> "RevisaoItemRequest":
        if (self.conteudo_embalagem is None) != (self.unidade_embalagem is None):
            raise ValueError(
                "Conteúdo e unidade da embalagem devem ser informados juntos."
            )
        return self
