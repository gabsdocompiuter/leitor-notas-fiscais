from uuid import UUID

from pydantic import BaseModel

from ...dtos.apresentacao_produto_dto import ApresentacaoProdutoDTO
from .marca_response import MarcaResponse
from .produto_response import ProdutoResponse


class ApresentacaoProdutoResponse(BaseModel):
    id: UUID
    produto: ProdutoResponse
    marca: MarcaResponse | None

    @classmethod
    def from_entity(cls, apresentacao: ApresentacaoProdutoDTO) -> "ApresentacaoProdutoResponse":
        return cls(
            id=apresentacao.id,
            produto=ProdutoResponse.from_entity(apresentacao.produto),
            marca=MarcaResponse.from_entity(apresentacao.marca) if apresentacao.marca else None,
        )
