from uuid import UUID

from pydantic import BaseModel

from ...models.item import Item
from ...models.unidade_medida import UnidadeMedida
from .apresentacao_produto_response import ApresentacaoProdutoResponse


class ItemResponse(BaseModel):
    id: UUID
    numero: int
    codigo: str
    descricao_original: str
    quantidade: str
    unidade_original: str
    valor_unitario: str
    valor_total: str
    alertas: list[str]
    apresentacao: ApresentacaoProdutoResponse | None
    unidade_corrigida: UnidadeMedida | None
    quantidade_normalizada: str | None
    revisado: bool

    @classmethod
    def from_entity(cls, item: Item) -> "ItemResponse":
        return cls(
            id=item.id,
            numero=item.numero,
            codigo=item.codigo,
            descricao_original=item.descricao_original,
            quantidade=str(item.quantidade),
            unidade_original=item.unidade_original,
            valor_unitario=str(item.valor_unitario),
            valor_total=str(item.valor_total),
            alertas=item.alertas,
            apresentacao=(
                ApresentacaoProdutoResponse.from_entity(item.apresentacao)
                if item.apresentacao
                else None
            ),
            unidade_corrigida=item.unidade_corrigida,
            quantidade_normalizada=(
                str(item.quantidade_normalizada)
                if item.quantidade_normalizada is not None
                else None
            ),
            revisado=item.revisado,
        )
