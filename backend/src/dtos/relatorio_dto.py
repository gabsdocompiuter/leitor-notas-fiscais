from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from .tag_dto import TagDTO


@dataclass
class GrupoRelatorioDTO:
    id: UUID
    nome: str
    total_pago: Decimal
    quantidade_itens: int


@dataclass
class ItemRelatorioDTO:
    id: UUID
    chave_nota: str
    numero_nota: str
    emissao: datetime
    estabelecimento: str
    produto: str
    categoria_id: UUID
    categoria: str
    valor_bruto: Decimal
    desconto_rateado: Decimal
    valor_pago: Decimal
    tags: list[TagDTO]
    considerar_proximo_mes: bool


@dataclass
class RelatorioMensalDTO:
    mes: str
    total_pago: Decimal
    total_desconto: Decimal
    quantidade_notas: int
    quantidade_itens: int
    total_mes_anterior: Decimal
    categorias: list[GrupoRelatorioDTO]
    tags: list[GrupoRelatorioDTO]


@dataclass
class ItensRelatorioDTO:
    itens: list[ItemRelatorioDTO]
    total: int
