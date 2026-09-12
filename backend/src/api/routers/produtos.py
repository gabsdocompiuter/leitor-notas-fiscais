from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from ...services.servico_catalogo import ServicoCatalogo
from ..dependencies import obter_servico_catalogo
from ..schemas.erro_response import ErroResponse
from ..schemas.produto_request import ProdutoRequest
from ..schemas.produto_response import ProdutoResponse


router = APIRouter(prefix="/produtos", tags=["Catálogos"])
Servico = Annotated[ServicoCatalogo, Depends(obter_servico_catalogo)]


@router.get("", response_model=list[ProdutoResponse], summary="Listar produtos")
def listar_produtos(
    servico: Servico,
    busca: Annotated[str | None, Query(max_length=150)] = None,
    categoria_id: UUID | None = None,
) -> list[ProdutoResponse]:
    return [
        ProdutoResponse.from_entity(item)
        for item in servico.listar_produtos(busca, categoria_id)
    ]


@router.post(
    "",
    response_model=ProdutoResponse,
    status_code=status.HTTP_201_CREATED,
    responses={404: {"model": ErroResponse}},
    summary="Criar produto",
)
def criar_produto(entrada: ProdutoRequest, servico: Servico) -> ProdutoResponse:
    return ProdutoResponse.from_entity(
        servico.criar_produto(entrada.nome, entrada.categoria_id, entrada.unidade_base)
    )


@router.get(
    "/{produto_id}",
    response_model=ProdutoResponse,
    responses={404: {"model": ErroResponse}},
    summary="Consultar produto",
)
def obter_produto(produto_id: UUID, servico: Servico) -> ProdutoResponse:
    return ProdutoResponse.from_entity(servico.obter_produto(produto_id))


@router.patch(
    "/{produto_id}",
    response_model=ProdutoResponse,
    responses={404: {"model": ErroResponse}, 409: {"model": ErroResponse}},
    summary="Alterar produto",
)
def atualizar_produto(
    produto_id: UUID, entrada: ProdutoRequest, servico: Servico
) -> ProdutoResponse:
    return ProdutoResponse.from_entity(
        servico.atualizar_produto(
            produto_id, entrada.nome, entrada.categoria_id, entrada.unidade_base
        )
    )


@router.delete(
    "/{produto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErroResponse}, 409: {"model": ErroResponse}},
    summary="Excluir produto",
)
def excluir_produto(produto_id: UUID, servico: Servico) -> Response:
    servico.excluir_produto(produto_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
