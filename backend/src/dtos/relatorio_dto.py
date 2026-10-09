from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from typing import Literal

from .tag_dto import TagDTO

AgrupadorRelatorio = Literal["marca", "estabelecimento", "variacao"]


@dataclass
class QuantidadeRelatorioDTO:
    quantidade: Decimal
    unidade: str


@dataclass
class GrupoRelatorioDTO:
    id: UUID
    nome: str
    total_pago: Decimal
    quantidade_itens: int
    quantidades_compradas: list[QuantidadeRelatorioDTO] = field(default_factory=list)


@dataclass
class ItemRelatorioDTO:
    id: UUID
    chave_nota: str
    numero_nota: str
    emissao: datetime
    estabelecimento: str
    produto: str
    produto_id: UUID
    categoria_id: UUID
    categoria: str
    valor_bruto: Decimal
    desconto_rateado: Decimal
    valor_pago: Decimal
    tags: list[TagDTO]
    considerar_proximo_mes: bool
    quantidade_comprada: Decimal | None = None
    unidade_quantidade: str | None = None
    estabelecimento_id: UUID | None = None
    marca_id: UUID | None = None
    marca: str | None = None
    variacao_id: UUID | None = None
    variacao: str | None = None
    quantidade_unidades: Decimal | None = None


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
    quantidades_compradas: list[QuantidadeRelatorioDTO] = field(default_factory=list)


@dataclass
class ItensRelatorioDTO:
    itens: list[ItemRelatorioDTO]
    total: int


@dataclass
class ProdutoRelatorioDTO:
    id: UUID
    nome: str
    total_pago: Decimal
    valor_bruto: Decimal
    desconto_rateado: Decimal
    quantidade_itens: int
    quantidade_comprada: Decimal | None = None
    unidade_quantidade: str | None = None


@dataclass
class AgrupamentoRelatorioDTO:
    id: UUID | None
    nome: str
    quantidade_registros: int = 0
    quantidade_comprada: Decimal | None = None
    unidade_quantidade: str | None = None
    total_pago: Decimal = Decimal("0.00")
    media_por_compra: Decimal = Decimal("0.00")
    quantidade_unidades: Decimal | None = None
