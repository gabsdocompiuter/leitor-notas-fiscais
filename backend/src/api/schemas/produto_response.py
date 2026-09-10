from uuid import UUID

from pydantic import BaseModel

from ...models.produto import Produto
from ...models.unidade_medida import UnidadeMedida
from .categoria_response import CategoriaResponse


class ProdutoResponse(BaseModel):
    id: UUID
    nome: str
    categoria: CategoriaResponse
    unidade_base: UnidadeMedida

    @classmethod
    def from_entity(cls, produto: Produto) -> "ProdutoResponse":
        return cls(
            id=produto.id,
            nome=produto.nome,
            categoria=CategoriaResponse.from_entity(produto.categoria),
            unidade_base=produto.unidade_base,
        )
