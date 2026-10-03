from fastapi import HTTPException
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from ..core.config import LIMITE_IMPORTACAO_BANCO
from ..core.persistence.coordenacao_banco import CoordenacaoBanco


class MiddlewareBanco:
    def __init__(self, app: ASGIApp, coordenacao: CoordenacaoBanco, permitir_importacao: bool):
        self.app = app
        self.coordenacao = coordenacao
        self.permitir_importacao = permitir_importacao

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http" and self.coordenacao.indisponivel:
            await JSONResponse({"codigo": "banco_indisponivel", "mensagem": "O banco está indisponível. Restaure a cópia anterior no servidor."}, status_code=503)(scope, receive, send)
            return
        livres = {"/health", "/version", "/docs", "/docs/oauth2-redirect", "/redoc", "/openapi.json", "/banco/configuracao"}
        if scope["type"] != "http" or scope["method"] == "OPTIONS" or scope["path"].rstrip("/") in livres:
            await self.app(scope, receive, send)
            return
        importacao = scope["method"] == "POST" and scope["path"].rstrip("/") == "/banco/importacao"
        if importacao and not self.permitir_importacao:
            await JSONResponse({"codigo": "importacao_desabilitada", "mensagem": "Importação de banco desabilitada."}, status_code=403)(scope, receive, send)
            return
        status = self.coordenacao.entrar(importacao)
        if status:
            await JSONResponse({"codigo": "banco_ocupado", "mensagem": "Há uma importação em andamento. Tente novamente."}, status_code=status)(scope, receive, send)
            return
        total = 0

        async def receber_limitado():
            nonlocal total
            mensagem = await receive()
            total += len(mensagem.get("body", b""))
            # Um MiB extra acomoda os campos e cabeçalhos do multipart.
            if total > LIMITE_IMPORTACAO_BANCO + 1024 * 1024:
                raise HTTPException(413, {"codigo": "arquivo_muito_grande", "mensagem": "O arquivo deve ter no máximo 100 MiB."})
            return mensagem

        try:
            await self.app(scope, receber_limitado if importacao else receive, send)
        finally:
            self.coordenacao.sair(importacao)
