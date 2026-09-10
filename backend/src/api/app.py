from collections.abc import Callable
from pathlib import Path

from fastapi import FastAPI

from ..core.config import CAMINHO_BANCO
from ..core.version import __version__
from ..persistence.banco_sqlite import BancoSQLite
from ..persistence.repositorio_notas import RepositorioNotas
from ..services.consulta import consultar_nota
from ..services.servico_leitura_notas import ServicoLeituraNotas
from .exception_handlers import registrar_tratadores
from .routers import health, leituras, notas, versao


def criar_app(
    caminho_banco: str | Path = CAMINHO_BANCO,
    consultar: Callable[[str], bytes] = consultar_nota,
) -> FastAPI:
    app = FastAPI(
        title="Leitor de notas fiscais",
        summary="Leitura e consulta de NFC-e para revisão posterior.",
        description=(
            "A API lê o QR Code de uma NFC-e do Rio Grande do Sul, consulta a "
            "SVRS e armazena a nota como **lida** no SQLite. Ler uma nota não "
            "confirma sua importação para o dashboard."
        ),
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        openapi_tags=[
            {"name": "Sistema", "description": "Estado e versão da API."},
            {"name": "Leituras", "description": "Captura do QR Code e consulta à SEFAZ."},
            {"name": "Notas", "description": "Notas já lidas e salvas no SQLite."},
        ],
    )
    repositorio = RepositorioNotas(BancoSQLite(caminho_banco))
    app.state.repositorio_notas = repositorio
    app.state.servico_leitura_notas = ServicoLeituraNotas(repositorio, consultar)
    registrar_tratadores(app)
    app.include_router(health.router)
    app.include_router(versao.router)
    app.include_router(leituras.router)
    app.include_router(notas.router)
    return app
