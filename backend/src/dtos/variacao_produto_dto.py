from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID, uuid4

from .produto_dto import ProdutoDTO
from ..enums.unidade_medida import UnidadeMedida
from ..core.decimais import formatar_decimal


@dataclass
class VariacaoProdutoDTO:
    id: UUID = field(default_factory=uuid4, kw_only=True)
    produto: ProdutoDTO
    quantidade: Decimal
    unidade_medida: UnidadeMedida

    @property
    def nome_exibicao(self) -> str:
        return f"{formatar_decimal(self.quantidade)} {self.unidade_medida.value}"
