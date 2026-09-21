from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from ...services.variacao_produto_service import VariacaoProdutoService
from ..dependencies import obter_variacao_produto_service
from ..schemas.erro_response import ErroResponse
from ..schemas.variacao_produto_request import VariacaoProdutoRequest
from ..schemas.variacao_produto_response import VariacaoProdutoResponse


router = APIRouter(tags=["Catálogos"])
Servico = Annotated[VariacaoProdutoService, Depends(obter_variacao_produto_service)]


@router.get(
    "/produtos/{produto_id}/variacoes",
    response_model=list[VariacaoProdutoResponse],
    summary="Listar variações do produto",
)
def listar_variacoes(produto_id: UUID, servico: Servico) -> list[VariacaoProdutoResponse]:
    return [
        VariacaoProdutoResponse.from_entity(item)
        for item in servico.listar(produto_id)
    ]


@router.post(
    "/produtos/{produto_id}/variacoes",
    response_model=VariacaoProdutoResponse,
    status_code=status.HTTP_201_CREATED,
    responses={404: {"model": ErroResponse}, 409: {"model": ErroResponse}},
    summary="Criar variação do produto",
)
def criar_variacao(
    produto_id: UUID, entrada: VariacaoProdutoRequest, servico: Servico
) -> VariacaoProdutoResponse:
    return VariacaoProdutoResponse.from_entity(
        servico.criar(
            produto_id, entrada.quantidade, entrada.unidade_medida, entrada.descricao
        )
    )


@router.patch(
    "/variacoes/{variacao_id}",
    response_model=VariacaoProdutoResponse,
    responses={404: {"model": ErroResponse}, 409: {"model": ErroResponse}},
    summary="Alterar variação do produto",
)
def atualizar_variacao(
    variacao_id: UUID, entrada: VariacaoProdutoRequest, servico: Servico
) -> VariacaoProdutoResponse:
    return VariacaoProdutoResponse.from_entity(
        servico.atualizar(
            variacao_id, entrada.quantidade, entrada.unidade_medida, entrada.descricao
        )
    )
