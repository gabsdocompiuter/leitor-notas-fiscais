from collections.abc import Callable
from decimal import Decimal
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session, sessionmaker

from ..core.persistence.entity_mapper import EntityMapper
from ..dtos.nota_dto import NotaDTO
from ..dtos.relatorio_dto import (
    GrupoRelatorioDTO, ItemRelatorioDTO, ItensRelatorioDTO, RelatorioMensalDTO,
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
            )

    def itens_mes(
        self, mes: str, categoria_id: UUID | None = None, tag_id: UUID | None = None,
        limite: int = 50, deslocamento: int = 0,
    ) -> ItensRelatorioDTO:
        with self.session_factory() as session:
            itens = self._itens(self._notas_mes(session, inicio_mes(mes)))
            filtrados = [
                item for item in itens
                if (categoria_id is None or item.categoria_id == categoria_id)
                and (tag_id is None or any(tag.id == tag_id for tag in item.tags))
            ]
            return ItensRelatorioDTO(
                itens=filtrados[deslocamento:deslocamento + limite], total=len(filtrados)
            )

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
                resultado.append(ItemRelatorioDTO(
                    id=item.id, chave_nota=nota.chave, numero_nota=nota.numero,
                    emissao=nota.emissao, estabelecimento=nota.estabelecimento.nome_exibicao,
                    produto=produto.nome, categoria_id=produto.categoria.id,
                    categoria=produto.categoria.nome, valor_bruto=item.valor_total,
                    desconto_rateado=desconto, valor_pago=item.valor_total - desconto,
                    tags=item.tags, considerar_proximo_mes=nota.considerar_proximo_mes,
                ))
        return resultado

    @staticmethod
    def _agrupar(
        itens: list[ItemRelatorioDTO],
        grupos_item: Callable[[ItemRelatorioDTO], list[tuple[UUID, str]]],
    ) -> list[GrupoRelatorioDTO]:
        grupos: dict[UUID, GrupoRelatorioDTO] = {}
        for item in itens:
            for id_, nome in grupos_item(item):
                grupo = grupos.setdefault(id_, GrupoRelatorioDTO(id_, nome, Decimal("0.00"), 0))
                grupo.total_pago += item.valor_pago
                grupo.quantidade_itens += 1
        return sorted(grupos.values(), key=lambda grupo: (-grupo.total_pago, grupo.nome.casefold()))
