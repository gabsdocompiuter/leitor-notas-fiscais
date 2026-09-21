from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from ...services.categoria_service import CategoriaService
from ..dependencies import obter_categoria_service
from ..schemas.categoria_request import CategoriaRequest
from ..schemas.categoria_response import CategoriaResponse
from ..schemas.erro_response import ErroResponse


router = APIRouter(prefix="/categorias", tags=["Catálogos"])
Servico = Annotated[CategoriaService, Depends(obter_categoria_service)]


@router.get("", response_model=list[CategoriaResponse], summary="Listar categorias")
def listar_categorias(
    servico: Servico,
    busca: Annotated[str | None, Query(max_length=100)] = None,
) -> list[CategoriaResponse]:
    return [CategoriaResponse.from_entity(item) for item in servico.listar(busca)]


@router.post(
    "",
    response_model=CategoriaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar categoria",
)
def criar_categoria(entrada: CategoriaRequest, servico: Servico) -> CategoriaResponse:
    return CategoriaResponse.from_entity(servico.criar(entrada.nome))


@router.get(
    "/{categoria_id}",
    response_model=CategoriaResponse,
    responses={404: {"model": ErroResponse}},
    summary="Consultar categoria",
)
def obter_categoria(categoria_id: UUID, servico: Servico) -> CategoriaResponse:
    return CategoriaResponse.from_entity(servico.obter(categoria_id))


@router.patch(
    "/{categoria_id}",
    response_model=CategoriaResponse,
    responses={404: {"model": ErroResponse}, 409: {"model": ErroResponse}},
    summary="Alterar categoria",
)
def atualizar_categoria(
    categoria_id: UUID, entrada: CategoriaRequest, servico: Servico
) -> CategoriaResponse:
    return CategoriaResponse.from_entity(
        servico.atualizar(categoria_id, entrada.nome)
    )
