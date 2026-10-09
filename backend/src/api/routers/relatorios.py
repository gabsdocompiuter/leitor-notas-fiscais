from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException

from ...services.relatorio_service import RelatorioService
from ...dtos.relatorio_dto import AgrupadorRelatorio
from ..dependencies import obter_relatorio_service
from ..schemas.relatorio_response import ItensRelatorioResponse, RelatorioMensalResponse, ProdutoRelatorioResponse, AgrupamentoRelatorioResponse

router = APIRouter(prefix="/relatorios", tags=["Relatórios"])
Mes = Annotated[str, Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$", description="Mês considerado, AAAA-MM")]
Servico = Annotated[RelatorioService, Depends(obter_relatorio_service)]


@router.get("/mensal", response_model=RelatorioMensalResponse, summary="Resumo mensal, categorias e tags")
def mensal(mes: Mes, servico: Servico) -> RelatorioMensalResponse:
    return RelatorioMensalResponse.from_entity(servico.mensal(mes))


@router.get("/mensal/itens", response_model=ItensRelatorioResponse, summary="Itens que compõem o relatório")
def itens(
    mes: Mes,
    servico: Servico,
    categoria_id: UUID | None = None,
    tag_id: UUID | None = None,
    limite: Annotated[int, Query(ge=1, le=100)] = 50,
    deslocamento: Annotated[int, Query(ge=0)] = 0,
    produto_id: UUID | None = None,
    agrupador: AgrupadorRelatorio | None = None,
    grupo_id: UUID | Literal["sem_grupo"] | None = None,
) -> ItensRelatorioResponse:
    if (agrupador is None) != (grupo_id is None):
        raise HTTPException(422, "Informe agrupador e grupo_id em conjunto.")
    if agrupador == "estabelecimento" and grupo_id == "sem_grupo":
        raise HTTPException(422, "Estabelecimento exige um identificador.")
    return ItensRelatorioResponse.from_entity(
        servico.itens_mes(mes, categoria_id, tag_id, limite, deslocamento, produto_id, agrupador, grupo_id)
    )


@router.get("/mensal/produtos", response_model=list[ProdutoRelatorioResponse],
            summary="Produtos que compõem uma categoria do relatório")
def produtos(mes: Mes, categoria_id: UUID, servico: Servico) -> list[ProdutoRelatorioResponse]:
    return [ProdutoRelatorioResponse.from_entity(produto)
            for produto in servico.produtos_mes(mes, categoria_id)]


@router.get("/mensal/agrupamentos", response_model=list[AgrupamentoRelatorioResponse])
def agrupamentos(mes: Mes, categoria_id: UUID, produto_id: UUID,
                 agrupador: AgrupadorRelatorio, servico: Servico) -> list[AgrupamentoRelatorioResponse]:
    return [AgrupamentoRelatorioResponse.from_entity(grupo)
            for grupo in servico.agrupamentos_mes(mes, categoria_id, produto_id, agrupador)]
