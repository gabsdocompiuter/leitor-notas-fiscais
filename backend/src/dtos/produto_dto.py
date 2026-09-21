from dataclasses import dataclass, field
from uuid import UUID, uuid4

from .categoria_dto import CategoriaDTO
from ..enums.unidade_medida import UnidadeMedida


@dataclass
class ProdutoDTO:
    """Produto padronizado; variações como integral e desnatado são distintos."""

    id: UUID = field(default_factory=uuid4, kw_only=True)
    nome: str
    categoria: CategoriaDTO
    nao_solicitar_marca: bool = False
    tratar_apenas_como_unidades: bool = False
    contem_variacoes: bool = False
    unidade_medida: UnidadeMedida | None = None
