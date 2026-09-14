from dataclasses import dataclass, field
from uuid import UUID, uuid4

from .categoria import Categoria
from .unidade_medida import UnidadeMedida


@dataclass
class Produto:
    """Produto padronizado; variações como integral e desnatado são distintos."""

    id: UUID = field(default_factory=uuid4, kw_only=True)
    nome: str
    categoria: Categoria
    unidade_base: UnidadeMedida
    nao_solicitar_marca: bool = False
