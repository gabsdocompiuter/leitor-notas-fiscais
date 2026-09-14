from dataclasses import dataclass, field
from uuid import UUID, uuid4

from .marca import Marca
from .produto import Produto


@dataclass
class ApresentacaoProduto:
    """Associação entre um produto padronizado e sua marca, quando aplicável."""

    id: UUID = field(default_factory=uuid4, kw_only=True)
    produto: Produto
    marca: Marca | None = None
