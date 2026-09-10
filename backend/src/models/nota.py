from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from .estabelecimento import Estabelecimento
from .item import Item
from .situacao_nota import SituacaoNota


@dataclass
class Nota:
    id: UUID = field(default_factory=uuid4, kw_only=True)
    chave: str
    numero: str
    serie: str
    estabelecimento: Estabelecimento
    emissao: datetime
    quantidade_itens: int
    valor_total: Decimal
    desconto: Decimal
    valor_a_pagar: Decimal
    itens: list[Item]
    url_origem: str
    situacao: SituacaoNota = SituacaoNota.LIDA
