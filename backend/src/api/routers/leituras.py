from typing import Annotated

from fastapi import APIRouter, Depends, Path

from ...core.exceptions import NaoEncontrado
from ...services.servico_leitura_notas import ServicoLeituraNotas
from ...services.servico_notas import ServicoNotas
from ..dependencies import obter_servico_leitura, obter_servico_notas
from ..schemas.erro_response import ErroResponse
from ..schemas.leitura_request import LeituraRequest
from ..schemas.leitura_response import LeituraResponse


router = APIRouter(prefix="/leituras", tags=["Leituras"])
Chave = Annotated[str, Path(pattern=r"^\d{44}$", description="Chave de acesso da NFC-e")]


@router.post(
    "",
    response_model=LeituraResponse,
    summary="Ler e salvar uma NFC-e",
    responses={
        422: {"model": ErroResponse, "description": "QR Code inválido ou não suportado"},
        502: {"model": ErroResponse, "description": "Falha ou resposta inválida da SEFAZ"},
        500: {"model": ErroResponse, "description": "Falha ao acessar o SQLite"},
    },
)
def criar_leitura(
    entrada: LeituraRequest,
    servico: Annotated[ServicoLeituraNotas, Depends(obter_servico_leitura)],
) -> LeituraResponse:
    return LeituraResponse.from_entity(servico.ler(entrada.url))


@router.get(
    "/{chave}",
    response_model=LeituraResponse,
    summary="Consultar uma leitura pela chave",
    responses={404: {"model": ErroResponse, "description": "Leitura não encontrada"}},
)
def obter_leitura(
    chave: Chave,
    servico: Annotated[ServicoNotas, Depends(obter_servico_notas)],
) -> LeituraResponse:
    leitura = servico.obter_leitura_por_chave(chave)
    if leitura is None:
        raise NaoEncontrado("Leitura não encontrada.")
    return LeituraResponse.from_entity(leitura)
