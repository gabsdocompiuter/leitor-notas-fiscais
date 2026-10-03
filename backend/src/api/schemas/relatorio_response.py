from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from ...dtos.relatorio_dto import (
    GrupoRelatorioDTO, ItemRelatorioDTO, ItensRelatorioDTO, RelatorioMensalDTO,
)
from .tag_response import TagResponse


class GrupoRelatorioResponse(BaseModel):
    id: UUID
    nome: str
    total_pago: str
    quantidade_itens: int

    @classmethod
    def from_entity(cls, grupo: GrupoRelatorioDTO) -> "GrupoRelatorioResponse":
        return cls(id=grupo.id, nome=grupo.nome, total_pago=f"{grupo.total_pago:.2f}",
                   quantidade_itens=grupo.quantidade_itens)


class RelatorioMensalResponse(BaseModel):
    mes: str
    total_pago: str
    total_desconto: str
    quantidade_notas: int
    quantidade_itens: int
    total_mes_anterior: str
    categorias: list[GrupoRelatorioResponse]
    tags: list[GrupoRelatorioResponse]

    @classmethod
    def from_entity(cls, relatorio: RelatorioMensalDTO) -> "RelatorioMensalResponse":
        return cls(
            mes=relatorio.mes, total_pago=f"{relatorio.total_pago:.2f}",
            total_desconto=f"{relatorio.total_desconto:.2f}",
            quantidade_notas=relatorio.quantidade_notas, quantidade_itens=relatorio.quantidade_itens,
            total_mes_anterior=f"{relatorio.total_mes_anterior:.2f}",
            categorias=[GrupoRelatorioResponse.from_entity(grupo) for grupo in relatorio.categorias],
            tags=[GrupoRelatorioResponse.from_entity(grupo) for grupo in relatorio.tags],
        )


class ItemRelatorioResponse(BaseModel):
    id: UUID
    chave_nota: str
    numero_nota: str
    emissao: datetime
    estabelecimento: str
    produto: str
    categoria_id: UUID
    categoria: str
    valor_bruto: str
    desconto_rateado: str
    valor_pago: str
    tags: list[TagResponse]
    considerar_proximo_mes: bool

    @classmethod
    def from_entity(cls, item: ItemRelatorioDTO) -> "ItemRelatorioResponse":
        return cls(
            id=item.id, chave_nota=item.chave_nota, numero_nota=item.numero_nota,
            emissao=item.emissao, estabelecimento=item.estabelecimento, produto=item.produto,
            categoria_id=item.categoria_id, categoria=item.categoria,
            valor_bruto=f"{item.valor_bruto:.2f}", desconto_rateado=f"{item.desconto_rateado:.2f}",
            valor_pago=f"{item.valor_pago:.2f}",
            tags=[TagResponse.from_entity(tag) for tag in item.tags],
            considerar_proximo_mes=item.considerar_proximo_mes,
        )


class ItensRelatorioResponse(BaseModel):
    itens: list[ItemRelatorioResponse]
    total: int

    @classmethod
    def from_entity(cls, pagina: ItensRelatorioDTO) -> "ItensRelatorioResponse":
        return cls(itens=[ItemRelatorioResponse.from_entity(item) for item in pagina.itens],
                   total=pagina.total)
