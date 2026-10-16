from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from .estabelecimento_dto import EstabelecimentoDTO
from .item_dto import ItemDTO
from ..enums.situacao_nota import SituacaoNota


@dataclass
class NotaDTO:
    id: UUID = field(default_factory=uuid4, kw_only=True)
    chave: str | None
    numero: str | None
    serie: str | None
    estabelecimento: EstabelecimentoDTO
    emissao: datetime
    quantidade_itens: int
    valor_total: Decimal
    desconto: Decimal
    valor_a_pagar: Decimal
    itens: list[ItemDTO]
    url_origem: str | None
    origem: str = "sefaz"
    situacao: SituacaoNota = SituacaoNota.LIDA
    importada_em: datetime | None = None
    considerar_proximo_mes: bool = False
    ignorada: bool = False
