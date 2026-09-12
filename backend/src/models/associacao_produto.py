from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID, uuid4

from .apresentacao_produto import ApresentacaoProduto
from .estabelecimento import Estabelecimento
from .unidade_medida import UnidadeMedida


@dataclass
class AssociacaoProduto:
    """Associação reutilizável de um código interno de um estabelecimento."""

    id: UUID = field(default_factory=uuid4, kw_only=True)
    estabelecimento: Estabelecimento
    codigo_item: str
    apresentacao: ApresentacaoProduto
    descricao_original: str | None = None
    unidade_corrigida: UnidadeMedida | None = None
    fator_normalizacao: Decimal | None = None
