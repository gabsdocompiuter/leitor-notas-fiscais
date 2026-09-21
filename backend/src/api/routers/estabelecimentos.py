from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from ...services.estabelecimento_service import EstabelecimentoService
from ..dependencies import obter_estabelecimento_service
from ..schemas.erro_response import ErroResponse
from ..schemas.estabelecimento_request import EstabelecimentoRequest
from ..schemas.estabelecimento_response import EstabelecimentoResponse


router = APIRouter(prefix="/estabelecimentos", tags=["Catálogos"])
Servico = Annotated[EstabelecimentoService, Depends(obter_estabelecimento_service)]


@router.get("", response_model=list[EstabelecimentoResponse], summary="Listar estabelecimentos")
def listar_estabelecimentos(
    servico: Servico,
    busca: Annotated[str | None, Query(max_length=150)] = None,
) -> list[EstabelecimentoResponse]:
    return [
        EstabelecimentoResponse.from_entity(item)
        for item in servico.listar(busca)
    ]


@router.get(
    "/{estabelecimento_id}",
    response_model=EstabelecimentoResponse,
    responses={404: {"model": ErroResponse}},
    summary="Consultar estabelecimento",
)
def obter_estabelecimento(
    estabelecimento_id: UUID, servico: Servico
) -> EstabelecimentoResponse:
    return EstabelecimentoResponse.from_entity(
        servico.obter(estabelecimento_id)
    )


@router.patch(
    "/{estabelecimento_id}",
    response_model=EstabelecimentoResponse,
    responses={404: {"model": ErroResponse}},
    summary="Alterar apelido do estabelecimento",
)
def atualizar_estabelecimento(
    estabelecimento_id: UUID, entrada: EstabelecimentoRequest, servico: Servico
) -> EstabelecimentoResponse:
    return EstabelecimentoResponse.from_entity(
        servico.atualizar_apelido(estabelecimento_id, entrada.apelido)
    )
