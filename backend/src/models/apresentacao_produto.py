from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID, uuid4

from .marca import Marca
from .produto import Produto
from .unidade_medida import UnidadeMedida


@dataclass
class ApresentacaoProduto:
    """Marca e conteúdo de uma embalagem, sem a quantidade comprada na nota."""

    id: UUID = field(default_factory=uuid4, kw_only=True)
    produto: Produto
    marca: Marca | None = None
    conteudo_embalagem: Decimal | None = None
    unidade_embalagem: UnidadeMedida | None = None
    marca_confirmada: bool = False
