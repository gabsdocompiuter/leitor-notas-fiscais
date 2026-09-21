from uuid import UUID

from pydantic import BaseModel

from ...dtos.produto_dto import ProdutoDTO
from ...enums.unidade_medida import UnidadeMedida
from .categoria_response import CategoriaResponse


class ProdutoResponse(BaseModel):
    id: UUID
    nome: str
    categoria: CategoriaResponse
    nao_solicitar_marca: bool
    tratar_apenas_como_unidades: bool
    contem_variacoes: bool
    unidade_medida: UnidadeMedida | None

    @classmethod
    def from_entity(cls, produto: ProdutoDTO) -> "ProdutoResponse":
        return cls(
            id=produto.id,
            nome=produto.nome,
            categoria=CategoriaResponse.from_entity(produto.categoria),
            nao_solicitar_marca=produto.nao_solicitar_marca,
            tratar_apenas_como_unidades=produto.tratar_apenas_como_unidades,
            contem_variacoes=produto.contem_variacoes,
            unidade_medida=produto.unidade_medida,
        )
