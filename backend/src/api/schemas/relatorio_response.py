from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from ...dtos.relatorio_dto import (
    GrupoRelatorioDTO, ItemRelatorioDTO, ItensRelatorioDTO, RelatorioMensalDTO, ProdutoRelatorioDTO,
    QuantidadeRelatorioDTO,
    AgrupamentoRelatorioDTO,
)
from .tag_response import TagResponse


UnidadeQuantidade = Literal["UN", "KG", "G", "L", "ML"]


def decimal_quantidade(valor: Decimal | None) -> str | None:
    return format(valor, "f") if valor is not None else None


class QuantidadeRelatorioResponse(BaseModel):
    quantidade: str
    unidade: UnidadeQuantidade

    @classmethod
    def from_entity(cls, quantidade: QuantidadeRelatorioDTO) -> "QuantidadeRelatorioResponse":
        return cls(quantidade=format(quantidade.quantidade, "f"), unidade=quantidade.unidade)


class GrupoRelatorioResponse(BaseModel):
    id: UUID
    nome: str
    total_pago: str
    quantidade_itens: int
    quantidades_compradas: list[QuantidadeRelatorioResponse]

    @classmethod
    def from_entity(cls, grupo: GrupoRelatorioDTO) -> "GrupoRelatorioResponse":
        return cls(id=grupo.id, nome=grupo.nome, total_pago=f"{grupo.total_pago:.2f}",
                   quantidade_itens=grupo.quantidade_itens,
                   quantidades_compradas=[QuantidadeRelatorioResponse.from_entity(q)
                                         for q in grupo.quantidades_compradas])


class RelatorioMensalResponse(BaseModel):
    mes: str
    total_pago: str
    total_desconto: str
    quantidade_notas: int
    quantidade_itens: int
    total_mes_anterior: str
    categorias: list[GrupoRelatorioResponse]
    tags: list[GrupoRelatorioResponse]
    quantidades_compradas: list[QuantidadeRelatorioResponse]

    @classmethod
    def from_entity(cls, relatorio: RelatorioMensalDTO) -> "RelatorioMensalResponse":
        return cls(
            mes=relatorio.mes, total_pago=f"{relatorio.total_pago:.2f}",
            total_desconto=f"{relatorio.total_desconto:.2f}",
            quantidade_notas=relatorio.quantidade_notas, quantidade_itens=relatorio.quantidade_itens,
            total_mes_anterior=f"{relatorio.total_mes_anterior:.2f}",
            categorias=[GrupoRelatorioResponse.from_entity(grupo) for grupo in relatorio.categorias],
            tags=[GrupoRelatorioResponse.from_entity(grupo) for grupo in relatorio.tags],
            quantidades_compradas=[QuantidadeRelatorioResponse.from_entity(q)
                                  for q in relatorio.quantidades_compradas],
        )


class ItemRelatorioResponse(BaseModel):
    id: UUID
    chave_nota: str
    numero_nota: str
    emissao: datetime
    estabelecimento: str
    produto: str
    produto_id: UUID
    categoria_id: UUID
    categoria: str
    valor_bruto: str
    desconto_rateado: str
    valor_pago: str
    tags: list[TagResponse]
    considerar_proximo_mes: bool
    quantidade_comprada: str | None
    unidade_quantidade: UnidadeQuantidade | None
    estabelecimento_id: UUID | None
    marca_id: UUID | None
    marca: str | None
    variacao_id: UUID | None
    variacao: str | None
    quantidade_unidades: str | None

    @classmethod
    def from_entity(cls, item: ItemRelatorioDTO) -> "ItemRelatorioResponse":
        return cls(
            id=item.id, chave_nota=item.chave_nota, numero_nota=item.numero_nota,
            emissao=item.emissao, estabelecimento=item.estabelecimento, produto=item.produto,
            produto_id=item.produto_id,
            categoria_id=item.categoria_id, categoria=item.categoria,
            valor_bruto=f"{item.valor_bruto:.2f}", desconto_rateado=f"{item.desconto_rateado:.2f}",
            valor_pago=f"{item.valor_pago:.2f}",
            tags=[TagResponse.from_entity(tag) for tag in item.tags],
            considerar_proximo_mes=item.considerar_proximo_mes,
            quantidade_comprada=decimal_quantidade(item.quantidade_comprada),
            unidade_quantidade=item.unidade_quantidade,
            estabelecimento_id=item.estabelecimento_id,
            marca_id=item.marca_id, marca=item.marca,
            variacao_id=item.variacao_id, variacao=item.variacao,
            quantidade_unidades=decimal_quantidade(item.quantidade_unidades),
        )


class ItensRelatorioResponse(BaseModel):
    itens: list[ItemRelatorioResponse]
    total: int

    @classmethod
    def from_entity(cls, pagina: ItensRelatorioDTO) -> "ItensRelatorioResponse":
        return cls(itens=[ItemRelatorioResponse.from_entity(item) for item in pagina.itens],
                   total=pagina.total)


class ProdutoRelatorioResponse(BaseModel):
    id: UUID
    nome: str
    total_pago: str
    valor_bruto: str
    desconto_rateado: str
    quantidade_itens: int
    quantidade_comprada: str | None
    unidade_quantidade: UnidadeQuantidade | None

    @classmethod
    def from_entity(cls, produto: ProdutoRelatorioDTO) -> "ProdutoRelatorioResponse":
        return cls(
            id=produto.id, nome=produto.nome, total_pago=f"{produto.total_pago:.2f}",
            valor_bruto=f"{produto.valor_bruto:.2f}",
            desconto_rateado=f"{produto.desconto_rateado:.2f}",
            quantidade_itens=produto.quantidade_itens,
            quantidade_comprada=decimal_quantidade(produto.quantidade_comprada),
            unidade_quantidade=produto.unidade_quantidade,
        )


class AgrupamentoRelatorioResponse(BaseModel):
    id: UUID | None
    nome: str
    quantidade_registros: int
    quantidade_comprada: str | None
    unidade_quantidade: UnidadeQuantidade | None
    total_pago: str
    media_por_compra: str
    quantidade_unidades: str | None

    @classmethod
    def from_entity(cls, grupo: AgrupamentoRelatorioDTO) -> "AgrupamentoRelatorioResponse":
        return cls(id=grupo.id, nome=grupo.nome, quantidade_registros=grupo.quantidade_registros,
                   quantidade_comprada=decimal_quantidade(grupo.quantidade_comprada),
                   unidade_quantidade=grupo.unidade_quantidade, total_pago=f"{grupo.total_pago:.2f}",
                   media_por_compra=f"{grupo.media_por_compra:.2f}",
                   quantidade_unidades=decimal_quantidade(grupo.quantidade_unidades))
