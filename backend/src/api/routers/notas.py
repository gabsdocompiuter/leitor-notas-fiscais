from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from ...core.exceptions import NaoEncontrado
from ...models.situacao_nota import SituacaoNota
from ...persistence.repositorio_notas import RepositorioNotas
from ..dependencies import obter_repositorio
from ..schemas.erro_response import ErroResponse
from ..schemas.nota_response import NotaResponse


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
