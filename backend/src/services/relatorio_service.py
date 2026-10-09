from collections.abc import Callable
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session, sessionmaker

from ..core.persistence.entity_mapper import EntityMapper
from ..dtos.nota_dto import NotaDTO
from ..dtos.item_dto import ItemDTO
from ..dtos.relatorio_dto import (
    GrupoRelatorioDTO, ItemRelatorioDTO, ItensRelatorioDTO, RelatorioMensalDTO, ProdutoRelatorioDTO,
    QuantidadeRelatorioDTO,
    AgrupadorRelatorio, AgrupamentoRelatorioDTO,
)
from ..repositories.relatorio_repository import RelatorioRepository
from .calculos_relatorio import deslocar_mes, inicio_mes, ratear_desconto


class RelatorioService:
    def __init__(self, session_factory: sessionmaker[Session]):
        self.session_factory = session_factory

    def mensal(self, mes: str) -> RelatorioMensalDTO:
        inicio = inicio_mes(mes)
        with self.session_factory() as session:
            notas = self._notas_mes(session, inicio)
            anteriores = self._notas_mes(session, deslocar_mes(inicio, -1))
            itens = self._itens(notas)
            return RelatorioMensalDTO(
                mes=mes,
                total_pago=sum((nota.valor_a_pagar for nota in notas), Decimal("0.00")),
                total_desconto=sum((nota.desconto for nota in notas), Decimal("0.00")),
                quantidade_notas=len(notas),
                quantidade_itens=len(itens),
                total_mes_anterior=sum((nota.valor_a_pagar for nota in anteriores), Decimal("0.00")),
                categorias=self._agrupar(itens, lambda item: [(item.categoria_id, item.categoria)]),
                tags=self._agrupar(itens, lambda item: [(tag.id, tag.nome) for tag in item.tags]),
                quantidades_compradas=self._quantidades(itens),
            )

    def itens_mes(
        self, mes: str, categoria_id: UUID | None = None, tag_id: UUID | None = None,
        limite: int = 50, deslocamento: int = 0,
        produto_id: UUID | None = None,
        agrupador: AgrupadorRelatorio | None = None,
        grupo_id: UUID | str | None = None,
    ) -> ItensRelatorioDTO:
        with self.session_factory() as session:
            itens = self._itens(self._notas_mes(session, inicio_mes(mes)))
            filtrados = [
                item for item in itens
                if (categoria_id is None or item.categoria_id == categoria_id)
                and (tag_id is None or any(tag.id == tag_id for tag in item.tags))
                and (produto_id is None or item.produto_id == produto_id)
                and (agrupador is None or getattr(item, f"{agrupador}_id") ==
                     (None if grupo_id == "sem_grupo" else grupo_id))
            ]
            return ItensRelatorioDTO(
                itens=filtrados[deslocamento:deslocamento + limite], total=len(filtrados)
            )

    def agrupamentos_mes(
        self, mes: str, categoria_id: UUID, produto_id: UUID, agrupador: AgrupadorRelatorio,
    ) -> list[AgrupamentoRelatorioDTO]:
        with self.session_factory() as session:
            itens = self._itens(self._notas_mes(session, inicio_mes(mes)))
            grupos: dict[UUID | None, AgrupamentoRelatorioDTO] = {}
            unidades_incompletas: set[UUID | None] = set()
            for item in itens:
                if item.categoria_id != categoria_id or item.produto_id != produto_id:
                    continue
                id_ = getattr(item, f"{agrupador}_id")
                nome = getattr(item, agrupador) or {"marca": "Sem marca", "variacao": "Sem variação"}.get(agrupador, "Sem estabelecimento")
                grupo = grupos.setdefault(id_, AgrupamentoRelatorioDTO(id_, nome))
                grupo.quantidade_registros += 1
                grupo.total_pago += item.valor_pago
                grupo.unidade_quantidade = item.unidade_quantidade
                if item.quantidade_unidades is None:
                    unidades_incompletas.add(id_)
                else:
                    grupo.quantidade_unidades = (grupo.quantidade_unidades or Decimal(0)) + item.quantidade_unidades
                if item.quantidade_comprada is not None:
                    grupo.quantidade_comprada = (grupo.quantidade_comprada or Decimal(0)) + item.quantidade_comprada
            for grupo in grupos.values():
                if grupo.id in unidades_incompletas:
                    grupo.quantidade_unidades = None
                grupo.media_por_compra = (grupo.total_pago / grupo.quantidade_registros).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP)
            return sorted(grupos.values(), key=lambda grupo: (-grupo.total_pago, grupo.nome.casefold(), str(grupo.id)))

    def produtos_mes(self, mes: str, categoria_id: UUID) -> list[ProdutoRelatorioDTO]:
        with self.session_factory() as session:
            itens = self._itens(self._notas_mes(session, inicio_mes(mes)))
            grupos: dict[UUID, ProdutoRelatorioDTO] = {}
            for item in itens:
                if item.categoria_id != categoria_id:
                    continue
                grupo = grupos.setdefault(item.produto_id, ProdutoRelatorioDTO(
                    item.produto_id, item.produto, Decimal("0.00"),
                    Decimal("0.00"), Decimal("0.00"), 0,
                ))
                grupo.total_pago += item.valor_pago
                grupo.valor_bruto += item.valor_bruto
                grupo.desconto_rateado += item.desconto_rateado
                grupo.quantidade_itens += 1
                if item.quantidade_comprada is not None:
                    grupo.quantidade_comprada = (grupo.quantidade_comprada or Decimal(0)) + item.quantidade_comprada
                    grupo.unidade_quantidade = item.unidade_quantidade
            return sorted(grupos.values(), key=lambda grupo: (
                -grupo.total_pago, grupo.nome.casefold(), str(grupo.id),
            ))

    @staticmethod
    def _notas_mes(session: Session, inicio: datetime) -> list[NotaDTO]:
        entidades = RelatorioRepository(session).listar_notas_mes(
            deslocar_mes(inicio, -1), inicio, deslocar_mes(inicio, 1)
        )
        return [EntityMapper.nota(nota) for nota in entidades]

    @staticmethod
    def _itens(notas: list[NotaDTO]) -> list[ItemRelatorioDTO]:
        resultado = []
        for nota in notas:
            parcelas = ratear_desconto([item.valor_total for item in nota.itens], nota.desconto)
            for item, desconto in zip(nota.itens, parcelas):
                produto = item.apresentacao.produto
                quantidade, unidade = RelatorioService._quantidade_item(item)
                resultado.append(ItemRelatorioDTO(
                    id=item.id, chave_nota=nota.chave, numero_nota=nota.numero,
                    emissao=nota.emissao, estabelecimento=nota.estabelecimento.nome_exibicao,
                    produto=produto.nome, produto_id=produto.id, categoria_id=produto.categoria.id,
                    categoria=produto.categoria.nome, valor_bruto=item.valor_total,
                    desconto_rateado=desconto, valor_pago=item.valor_total - desconto,
                    tags=item.tags, considerar_proximo_mes=nota.considerar_proximo_mes,
                    quantidade_comprada=quantidade, unidade_quantidade=unidade,
                    estabelecimento_id=nota.estabelecimento.id,
                    marca_id=item.apresentacao.marca.id if item.apresentacao.marca else None,
                    marca=item.apresentacao.marca.nome if item.apresentacao.marca else None,
                    variacao_id=item.variacao.id if item.variacao else None,
                    variacao=item.variacao.nome_exibicao if item.variacao else None,
                    quantidade_unidades=(item.quantidade_confirmada
                                         if produto.tratar_apenas_como_unidades or produto.contem_variacoes
                                         else None),
                ))
        return resultado

    @staticmethod
    def _quantidade_item(item: ItemDTO) -> tuple[Decimal | None, str | None]:
        produto = item.apresentacao.produto
        unidade = "UN" if produto.tratar_apenas_como_unidades else produto.unidade_medida.value
        quantidade = item.quantidade_confirmada
        if quantidade is None:
            return None, unidade
        if produto.contem_variacoes:
            if item.variacao is None:
                return None, unidade
            fatores = {"KG": Decimal(1000), "G": Decimal(1),
                       "L": Decimal(1000), "ML": Decimal(1)}
            origem = item.variacao.unidade_medida.value
            if (origem in ("KG", "G")) != (unidade in ("KG", "G")):
                return None, unidade
            quantidade = quantidade * item.variacao.quantidade * fatores[origem] / fatores[unidade]
        return quantidade, unidade

    @staticmethod
    def _quantidades(itens: list[ItemRelatorioDTO]) -> list[QuantidadeRelatorioDTO]:
        totais: dict[str, Decimal] = {}
        for item in itens:
            if item.quantidade_comprada is not None and item.unidade_quantidade is not None:
                unidade = item.unidade_quantidade
                totais[unidade] = totais.get(unidade, Decimal(0)) + item.quantidade_comprada
        return [QuantidadeRelatorioDTO(totais[unidade], unidade)
                for unidade in ("UN", "KG", "G", "L", "ML") if unidade in totais]

    @staticmethod
    def _agrupar(
        itens: list[ItemRelatorioDTO],
        grupos_item: Callable[[ItemRelatorioDTO], list[tuple[UUID, str]]],
    ) -> list[GrupoRelatorioDTO]:
        grupos: dict[UUID, GrupoRelatorioDTO] = {}
        itens_por_grupo: dict[UUID, list[ItemRelatorioDTO]] = {}
        for item in itens:
            for id_, nome in grupos_item(item):
                grupo = grupos.setdefault(id_, GrupoRelatorioDTO(id_, nome, Decimal("0.00"), 0))
                grupo.total_pago += item.valor_pago
                grupo.quantidade_itens += 1
                itens_por_grupo.setdefault(id_, []).append(item)
        for id_, grupo in grupos.items():
            grupo.quantidades_compradas = RelatorioService._quantidades(itens_por_grupo[id_])
        return sorted(grupos.values(), key=lambda grupo: (-grupo.total_pago, grupo.nome.casefold()))
