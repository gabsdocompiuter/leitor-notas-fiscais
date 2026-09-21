from dataclasses import dataclass, field
from uuid import UUID, uuid4

from .marca_dto import MarcaDTO
from .produto_dto import ProdutoDTO


@dataclass
class ApresentacaoProdutoDTO:
    """Associação entre um produto padronizado e sua marca, quando aplicável."""

    id: UUID = field(default_factory=uuid4, kw_only=True)
    produto: ProdutoDTO
    marca: MarcaDTO | None = None
