from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID, uuid4

from .apresentacao_produto_dto import ApresentacaoProdutoDTO
from .estabelecimento_dto import EstabelecimentoDTO
from .variacao_produto_dto import VariacaoProdutoDTO


@dataclass
class AssociacaoProdutoDTO:
    """Associação reutilizável de um código interno de um estabelecimento."""

    id: UUID = field(default_factory=uuid4, kw_only=True)
    estabelecimento: EstabelecimentoDTO
    codigo_item: str
    apresentacao: ApresentacaoProdutoDTO
    descricao_original: str | None = None
    variacao: VariacaoProdutoDTO | None = None
    fator_conversao: Decimal | None = None
