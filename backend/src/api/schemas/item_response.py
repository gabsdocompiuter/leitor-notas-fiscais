from uuid import UUID

from pydantic import BaseModel

from ...dtos.item_dto import ItemDTO
from .apresentacao_produto_response import ApresentacaoProdutoResponse
from .variacao_produto_response import VariacaoProdutoResponse


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
    variacao: VariacaoProdutoResponse | None
    quantidade_confirmada: str | None
    revisado: bool

    @classmethod
    def from_entity(cls, item: ItemDTO) -> "ItemResponse":
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
            variacao=(
                VariacaoProdutoResponse.from_entity(item.variacao) if item.variacao else None
            ),
            quantidade_confirmada=(
                str(item.quantidade_confirmada)
                if item.quantidade_confirmada is not None
                else None
            ),
            revisado=item.revisado,
        )
