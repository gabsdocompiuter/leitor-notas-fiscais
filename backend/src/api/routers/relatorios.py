from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from ...services.relatorio_service import RelatorioService
from ..dependencies import obter_relatorio_service
from ..schemas.relatorio_response import ItensRelatorioResponse, RelatorioMensalResponse

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
) -> ItensRelatorioResponse:
    return ItensRelatorioResponse.from_entity(
        servico.itens_mes(mes, categoria_id, tag_id, limite, deslocamento)
    )
