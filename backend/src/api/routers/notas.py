from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query

from ...core.exceptions import NaoEncontrado
from ...models.situacao_nota import SituacaoNota
from ...persistence.repositorio_notas import RepositorioNotas
from ...services.servico_revisao_notas import ServicoRevisaoNotas
from ..dependencies import obter_repositorio, obter_servico_revisao
from ..schemas.erro_response import ErroResponse
from ..schemas.nota_response import NotaResponse
from ..schemas.revisao_item_request import RevisaoItemRequest


router = APIRouter(prefix="/notas", tags=["Notas"])
Chave = Annotated[str, Path(pattern=r"^\d{44}$", description="Chave de acesso da NFC-e")]


@router.get("", response_model=list[NotaResponse], summary="Listar notas lidas")
def listar_notas(
    repositorio: Annotated[RepositorioNotas, Depends(obter_repositorio)],
    situacao: Annotated[SituacaoNota | None, Query(description="Filtrar pela situação")] = None,
    limite: Annotated[int, Query(ge=1, le=100)] = 50,
    deslocamento: Annotated[int, Query(ge=0)] = 0,
) -> list[NotaResponse]:
    return [
        NotaResponse.from_entity(nota)
        for nota in repositorio.listar(situacao, limite, deslocamento)
    ]


@router.get(
    "/{chave}",
    response_model=NotaResponse,
    summary="Consultar uma nota pela chave",
    responses={404: {"model": ErroResponse, "description": "Nota não encontrada"}},
)
def obter_nota(
    chave: Chave,
    repositorio: Annotated[RepositorioNotas, Depends(obter_repositorio)],
) -> NotaResponse:
    nota = repositorio.obter_por_chave(chave)
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
        entrada.marca_confirmada,
        entrada.conteudo_embalagem,
        entrada.unidade_embalagem,
        entrada.unidade_corrigida,
        entrada.quantidade_normalizada,
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
