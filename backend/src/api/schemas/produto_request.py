from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from ...enums.unidade_medida import UnidadeMedida


class ProdutoRequest(BaseModel):
    nome: str = Field(min_length=1, max_length=150, examples=["Leite integral"])
    categoria_id: UUID
    nao_solicitar_marca: bool = False
    tratar_apenas_como_unidades: bool = False
    contem_variacoes: bool = False
    unidade_medida: UnidadeMedida | None = None

    @model_validator(mode="after")
    def validar_tipo(self) -> "ProdutoRequest":
        if self.tratar_apenas_como_unidades:
            if self.contem_variacoes or self.unidade_medida is not None:
                raise ValueError(
                    "Produtos tratados como unidades não aceitam variações ou unidade de medida."
                )
        elif self.unidade_medida is None:
            raise ValueError("A unidade de medida é obrigatória para este produto.")
        return self
