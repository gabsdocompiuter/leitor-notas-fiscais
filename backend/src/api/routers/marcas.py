from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from ...services.marca_service import MarcaService
from ..dependencies import obter_marca_service
from ..schemas.erro_response import ErroResponse
from ..schemas.marca_request import MarcaRequest
from ..schemas.marca_response import MarcaResponse


router = APIRouter(prefix="/marcas", tags=["Catálogos"])
Servico = Annotated[MarcaService, Depends(obter_marca_service)]


@router.get("", response_model=list[MarcaResponse], summary="Listar marcas")
def listar_marcas(
    servico: Servico,
    busca: Annotated[str | None, Query(max_length=100)] = None,
) -> list[MarcaResponse]:
    return [MarcaResponse.from_entity(item) for item in servico.listar(busca)]


@router.post(
    "",
    response_model=MarcaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar marca",
)
def criar_marca(entrada: MarcaRequest, servico: Servico) -> MarcaResponse:
    return MarcaResponse.from_entity(servico.criar(entrada.nome))


@router.get(
    "/{marca_id}",
    response_model=MarcaResponse,
    responses={404: {"model": ErroResponse}},
    summary="Consultar marca",
)
def obter_marca(marca_id: UUID, servico: Servico) -> MarcaResponse:
    return MarcaResponse.from_entity(servico.obter(marca_id))


@router.patch(
    "/{marca_id}",
    response_model=MarcaResponse,
    responses={404: {"model": ErroResponse}, 409: {"model": ErroResponse}},
    summary="Alterar marca",
)
def atualizar_marca(
    marca_id: UUID, entrada: MarcaRequest, servico: Servico
) -> MarcaResponse:
    return MarcaResponse.from_entity(servico.atualizar(marca_id, entrada.nome))
