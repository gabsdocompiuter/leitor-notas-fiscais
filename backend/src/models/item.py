from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID, uuid4

from .apresentacao_produto import ApresentacaoProduto
from .unidade_medida import UnidadeMedida


@dataclass
class Item:
    id: UUID = field(default_factory=uuid4, kw_only=True)
    numero: int
    codigo: str
    descricao_original: str
    quantidade: Decimal
    unidade_original: str
    valor_unitario: Decimal
    valor_total: Decimal
    alertas: list[str]
    apresentacao: ApresentacaoProduto | None = None
    unidade_corrigida: UnidadeMedida | None = None
    quantidade_normalizada: Decimal | None = None
    revisado: bool = False
