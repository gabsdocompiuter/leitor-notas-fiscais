from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID, uuid4

from .produto_dto import ProdutoDTO
from ..enums.unidade_medida import UnidadeMedida


@dataclass
class VariacaoProdutoDTO:
    id: UUID = field(default_factory=uuid4, kw_only=True)
    produto: ProdutoDTO
    quantidade: Decimal
    unidade_medida: UnidadeMedida
    descricao: str | None = None

    @property
    def nome_exibicao(self) -> str:
        return self.descricao or f"{self.quantidade:g} {self.unidade_medida.value}"
