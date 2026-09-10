from uuid import UUID

from pydantic import BaseModel

from ...models.apresentacao_produto import ApresentacaoProduto
from ...models.unidade_medida import UnidadeMedida
from .marca_response import MarcaResponse
from .produto_response import ProdutoResponse


class ApresentacaoProdutoResponse(BaseModel):
    id: UUID
    produto: ProdutoResponse
    marca: MarcaResponse | None
    conteudo_embalagem: str | None
    unidade_embalagem: UnidadeMedida | None
    marca_confirmada: bool

    @classmethod
    def from_entity(cls, apresentacao: ApresentacaoProduto) -> "ApresentacaoProdutoResponse":
        return cls(
            id=apresentacao.id,
            produto=ProdutoResponse.from_entity(apresentacao.produto),
            marca=MarcaResponse.from_entity(apresentacao.marca) if apresentacao.marca else None,
            conteudo_embalagem=(
                str(apresentacao.conteudo_embalagem)
                if apresentacao.conteudo_embalagem is not None
                else None
            ),
            unidade_embalagem=apresentacao.unidade_embalagem,
            marca_confirmada=apresentacao.marca_confirmada,
        )
