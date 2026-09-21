from pydantic import BaseModel

from ...enums.unidade_medida import UnidadeMedida


class UnidadeMedidaResponse(BaseModel):
    codigo: UnidadeMedida
    descricao: str

    @classmethod
    def from_entity(cls, unidade: UnidadeMedida) -> "UnidadeMedidaResponse":
        return cls(codigo=unidade, descricao=unidade.descricao)
