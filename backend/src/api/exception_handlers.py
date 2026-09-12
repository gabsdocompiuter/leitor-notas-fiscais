from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ..core.exceptions import (
    ErroConsulta,
    ErroLeitura,
    ErroPersistencia,
    ErroQrCode,
    NaoEncontrado,
    Conflito,
    DadosInvalidos,
)


def _resposta(status: int, codigo: str, mensagem: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"codigo": codigo, "mensagem": mensagem})


def registrar_tratadores(app: FastAPI) -> None:
    @app.exception_handler(DadosInvalidos)
    async def tratar_dados_invalidos(_: Request, erro: DadosInvalidos) -> JSONResponse:
        return _resposta(422, "dados_invalidos", str(erro))

    @app.exception_handler(Conflito)
    async def tratar_conflito(_: Request, erro: Conflito) -> JSONResponse:
        return _resposta(409, "conflito", str(erro))

    @app.exception_handler(NaoEncontrado)
    async def tratar_nao_encontrado(_: Request, erro: NaoEncontrado) -> JSONResponse:
        return _resposta(404, "nao_encontrado", str(erro))

    @app.exception_handler(ErroQrCode)
    async def tratar_qrcode(_: Request, erro: ErroQrCode) -> JSONResponse:
        return _resposta(422, "qrcode_invalido", str(erro))

    @app.exception_handler(ErroConsulta)
    async def tratar_consulta(_: Request, erro: ErroConsulta) -> JSONResponse:
        return _resposta(502, "falha_consulta_sefaz", str(erro))

    @app.exception_handler(ErroLeitura)
    async def tratar_leitura(_: Request, erro: ErroLeitura) -> JSONResponse:
        return _resposta(502, "resposta_sefaz_invalida", str(erro))

    @app.exception_handler(ErroPersistencia)
    async def tratar_persistencia(_: Request, erro: ErroPersistencia) -> JSONResponse:
        return _resposta(500, "falha_persistencia", str(erro))
