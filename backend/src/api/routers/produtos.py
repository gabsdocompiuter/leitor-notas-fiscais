from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from ...services.produto_service import ProdutoService
from ..dependencies import obter_produto_service
from ..schemas.erro_response import ErroResponse
from ..schemas.produto_request import ProdutoRequest
from ..schemas.produto_response import ProdutoResponse


router = APIRouter(prefix="/produtos", tags=["Catálogos"])
Servico = Annotated[ProdutoService, Depends(obter_produto_service)]


@router.get("", response_model=list[ProdutoResponse], summary="Listar produtos")
def listar_produtos(
    servico: Servico,
    busca: Annotated[str | None, Query(max_length=150)] = None,
    categoria_id: UUID | None = None,
) -> list[ProdutoResponse]:
    return [
        ProdutoResponse.from_entity(item)
        for item in servico.listar(busca, categoria_id)
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
        servico.criar(
            entrada.nome,
            entrada.categoria_id,
            entrada.nao_solicitar_marca,
            entrada.tratar_apenas_como_unidades,
            entrada.contem_variacoes,
            entrada.unidade_medida,
        )
    )


@router.get(
    "/{produto_id}",
    response_model=ProdutoResponse,
    responses={404: {"model": ErroResponse}},
    summary="Consultar produto",
)
def obter_produto(produto_id: UUID, servico: Servico) -> ProdutoResponse:
    return ProdutoResponse.from_entity(servico.obter(produto_id))


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
        servico.atualizar(
            produto_id,
            entrada.nome,
            entrada.categoria_id,
            entrada.nao_solicitar_marca,
            entrada.tratar_apenas_como_unidades,
            entrada.contem_variacoes,
            entrada.unidade_medida,
        )
    )
