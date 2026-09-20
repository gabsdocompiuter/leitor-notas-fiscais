from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query

from ...core.exceptions import NaoEncontrado
from ...models.situacao_nota import SituacaoNota
from ...services.servico_notas import ServicoNotas
from ...services.servico_revisao_notas import ServicoRevisaoNotas
from ..dependencies import obter_servico_notas, obter_servico_revisao
from ..schemas.erro_response import ErroResponse
from ..schemas.nota_response import NotaResponse
from ..schemas.revisao_item_request import RevisaoItemRequest


router = APIRouter(prefix="/notas", tags=["Notas"])
Chave = Annotated[str, Path(pattern=r"^\d{44}$", description="Chave de acesso da NFC-e")]


@router.get("", response_model=list[NotaResponse], summary="Listar notas lidas")
def listar_notas(
    servico: Annotated[ServicoNotas, Depends(obter_servico_notas)],
    situacao: Annotated[SituacaoNota | None, Query(description="Filtrar pela situação")] = None,
    limite: Annotated[int, Query(ge=1, le=100)] = 50,
    deslocamento: Annotated[int, Query(ge=0)] = 0,
) -> list[NotaResponse]:
    return [
        NotaResponse.from_entity(nota)
        for nota in servico.listar(situacao, limite, deslocamento)
    ]


@router.get(
    "/{chave}",
    response_model=NotaResponse,
    summary="Consultar uma nota pela chave",
    responses={404: {"model": ErroResponse, "description": "Nota não encontrada"}},
)
def obter_nota(
    chave: Chave,
    servico: Annotated[ServicoNotas, Depends(obter_servico_notas)],
) -> NotaResponse:
    nota = servico.obter_por_chave(chave)
    if nota is None:
        raise NaoEncontrado("Nota não encontrada.")
    return NotaResponse.from_entity(nota)


@router.patch(
    "/{chave}/itens/{item_id}",
    response_model=NotaResponse,
    summary="Revisar um item da nota",
    responses={
        404: {"model": ErroResponse, "description": "Nota, item ou cadastro não encontrado"},
        409: {"model": ErroResponse, "description": "A nota já foi importada"},
        422: {"model": ErroResponse, "description": "Classificação incompleta ou inválida"},
    },
)
def revisar_item(
    chave: Chave,
    item_id: UUID,
    entrada: RevisaoItemRequest,
    servico: Annotated[ServicoRevisaoNotas, Depends(obter_servico_revisao)],
) -> NotaResponse:
    nota = servico.revisar_item(
        chave,
        item_id,
        entrada.produto_id,
        entrada.marca_id,
        entrada.variacao_id,
        entrada.quantidade_confirmada,
    )
    return NotaResponse.from_entity(nota)


@router.post(
    "/{chave}/importacao",
    response_model=NotaResponse,
    summary="Concluir a importação da nota",
    responses={
        404: {"model": ErroResponse, "description": "Nota não encontrada"},
        409: {"model": ErroResponse, "description": "Existem itens sem revisão"},
    },
)
def concluir_importacao(
    chave: Chave,
    servico: Annotated[ServicoRevisaoNotas, Depends(obter_servico_revisao)],
) -> NotaResponse:
    return NotaResponse.from_entity(servico.concluir_importacao(chave))
