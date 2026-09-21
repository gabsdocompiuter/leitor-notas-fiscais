from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID, uuid4

from .apresentacao_produto_dto import ApresentacaoProdutoDTO
from .variacao_produto_dto import VariacaoProdutoDTO


@dataclass
class ItemDTO:
    id: UUID = field(default_factory=uuid4, kw_only=True)
    numero: int
    codigo: str
    descricao_original: str
    quantidade: Decimal
    unidade_original: str
    valor_unitario: Decimal
    valor_total: Decimal
    alertas: list[str]
    apresentacao: ApresentacaoProdutoDTO | None = None
    variacao: VariacaoProdutoDTO | None = None
    quantidade_confirmada: Decimal | None = None
    revisado: bool = False
