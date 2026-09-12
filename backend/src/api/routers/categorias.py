from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from ...services.servico_catalogo import ServicoCatalogo
from ..dependencies import obter_servico_catalogo
from ..schemas.categoria_request import CategoriaRequest
from ..schemas.categoria_response import CategoriaResponse
from ..schemas.erro_response import ErroResponse


router = APIRouter(prefix="/categorias", tags=["Catálogos"])
Servico = Annotated[ServicoCatalogo, Depends(obter_servico_catalogo)]


@router.get("", response_model=list[CategoriaResponse], summary="Listar categorias")
def listar_categorias(
    servico: Servico,
    busca: Annotated[str | None, Query(max_length=100)] = None,
) -> list[CategoriaResponse]:
    return [CategoriaResponse.from_entity(item) for item in servico.listar_categorias(busca)]


@router.post(
    "",
    response_model=CategoriaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar categoria",
)
def criar_categoria(entrada: CategoriaRequest, servico: Servico) -> CategoriaResponse:
    return CategoriaResponse.from_entity(servico.criar_categoria(entrada.nome))


@router.get(
    "/{categoria_id}",
    response_model=CategoriaResponse,
    responses={404: {"model": ErroResponse}},
    summary="Consultar categoria",
)
def obter_categoria(categoria_id: UUID, servico: Servico) -> CategoriaResponse:
    return CategoriaResponse.from_entity(servico.obter_categoria(categoria_id))


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
        servico.atualizar_categoria(categoria_id, entrada.nome)
    )


@router.delete(
    "/{categoria_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErroResponse}, 409: {"model": ErroResponse}},
    summary="Excluir categoria",
)
def excluir_categoria(categoria_id: UUID, servico: Servico) -> Response:
    servico.excluir_categoria(categoria_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
