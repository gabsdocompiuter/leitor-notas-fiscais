from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query

from ...core.exceptions import NaoEncontrado
from ...enums.situacao_nota import SituacaoNota
from ...services.nota_service import NotaService
from ...services.tag_service import TagService
from ...services.revisao_nota_service import RevisaoNotaService
from ..dependencies import obter_nota_service, obter_revisao_nota_service
from ..schemas.erro_response import ErroResponse
from ..schemas.nota_response import NotaResponse
from ..schemas.revisao_item_request import RevisaoItemRequest
from ..schemas.competencia_nota_request import CompetenciaNotaRequest
from ..schemas.tag_request import TagsItemRequest
from ..dependencies import obter_tag_service


router = APIRouter(prefix="/notas", tags=["Notas"])
Chave = Annotated[str, Path(pattern=r"^\d{44}$", description="Chave de acesso da NFC-e")]


@router.get("", response_model=list[NotaResponse], summary="Listar notas lidas")
def listar_notas(
    servico: Annotated[NotaService, Depends(obter_nota_service)],
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
    servico: Annotated[NotaService, Depends(obter_nota_service)],
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
        422: {"model": ErroResponse, "description": "Classificação incompleta ou inválida"},
    },
)
def revisar_item(
    chave: Chave,
    item_id: UUID,
    entrada: RevisaoItemRequest,
    servico: Annotated[RevisaoNotaService, Depends(obter_revisao_nota_service)],
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
    servico: Annotated[RevisaoNotaService, Depends(obter_revisao_nota_service)],
) -> NotaResponse:
    return NotaResponse.from_entity(servico.concluir_importacao(chave))


@router.patch("/{chave}", response_model=NotaResponse, summary="Definir mês considerado da nota")
def definir_competencia(
    chave: Chave,
    entrada: CompetenciaNotaRequest,
    servico: Annotated[NotaService, Depends(obter_nota_service)],
) -> NotaResponse:
    return NotaResponse.from_entity(servico.definir_competencia(chave, entrada.considerar_proximo_mes))


@router.put("/{chave}/itens/{item_id}/tags", response_model=NotaResponse, summary="Definir tags do item")
def definir_tags_item(
    chave: Chave,
    item_id: UUID,
    entrada: TagsItemRequest,
    servico: Annotated[TagService, Depends(obter_tag_service)],
) -> NotaResponse:
    return NotaResponse.from_entity(servico.definir_no_item(chave, item_id, entrada.tag_ids))


@router.post("/{chave}/itens/tags", response_model=NotaResponse, summary="Adicionar tags a todos os itens")
def adicionar_tags_em_todos(
    chave: Chave,
    entrada: TagsItemRequest,
    servico: Annotated[TagService, Depends(obter_tag_service)],
) -> NotaResponse:
    return NotaResponse.from_entity(servico.adicionar_em_todos(chave, entrada.tag_ids))
