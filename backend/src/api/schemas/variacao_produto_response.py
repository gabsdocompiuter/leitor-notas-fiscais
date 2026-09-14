from uuid import UUID

from pydantic import BaseModel

from ...models.unidade_medida import UnidadeMedida
from ...models.variacao_produto import VariacaoProduto


class VariacaoProdutoResponse(BaseModel):
    id: UUID
    produto_id: UUID
    quantidade: str
    unidade_medida: UnidadeMedida
    descricao: str | None
    nome_exibicao: str

    @classmethod
    def from_entity(cls, variacao: VariacaoProduto) -> "VariacaoProdutoResponse":
        return cls(
            id=variacao.id,
            produto_id=variacao.produto.id,
            quantidade=str(variacao.quantidade),
            unidade_medida=variacao.unidade_medida,
            descricao=variacao.descricao,
            nome_exibicao=variacao.nome_exibicao,
        )
