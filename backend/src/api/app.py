from collections.abc import Callable
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from ..core.config import CAMINHO_BANCO
from ..core.version import __version__
from ..persistence.banco_sqlite import BancoSQLite
from ..services.consulta import consultar_nota
from ..services.servico_catalogo import ServicoCatalogo
from ..services.servico_leitura_notas import ServicoLeituraNotas
from ..services.servico_notas import ServicoNotas
from ..services.servico_revisao_notas import ServicoRevisaoNotas
from .exception_handlers import registrar_tratadores
from .routers import (
    categorias,
    estabelecimentos,
    health,
    leituras,
    marcas,
    notas,
    produtos,
    unidades_medida,
    variacoes,
    versao,
)


def criar_app(
    caminho_banco: str | Path = CAMINHO_BANCO,
    consultar: Callable[[str], bytes] = consultar_nota,
) -> FastAPI:
    banco = BancoSQLite(caminho_banco)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield
        banco.fechar()

    app = FastAPI(
        title="Leitor de notas fiscais",
        summary="Leitura e consulta de NFC-e para revisão posterior.",
        description=(
            "A API lê o QR Code de uma NFC-e do Rio Grande do Sul, consulta a "
            "SVRS e armazena a nota como **lida** no SQLite. Ler uma nota não "
            "confirma sua importação para o dashboard."
        ),
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        openapi_tags=[
            {"name": "Sistema", "description": "Estado e versão da API."},
            {"name": "Leituras", "description": "Captura do QR Code e consulta à SEFAZ."},
            {"name": "Notas", "description": "Notas já lidas e salvas no SQLite."},
            {"name": "Catálogos", "description": "Categorias, marcas e produtos reutilizáveis."},
        ],
    )
    servico_notas = ServicoNotas(banco.session_factory)
    servico_catalogo = ServicoCatalogo(banco.session_factory)
    servico_revisao = ServicoRevisaoNotas(banco.session_factory)
    app.state.banco = banco
    app.state.servico_notas = servico_notas
    app.state.servico_catalogo = servico_catalogo
    app.state.servico_revisao_notas = servico_revisao
    app.state.servico_leitura_notas = ServicoLeituraNotas(
        banco.session_factory, consultar, servico_revisao
    )
    registrar_tratadores(app)
    app.include_router(health.router)
    app.include_router(versao.router)
    app.include_router(leituras.router)
    app.include_router(notas.router)
    app.include_router(categorias.router)
    app.include_router(marcas.router)
    app.include_router(produtos.router)
    app.include_router(variacoes.router)
    app.include_router(estabelecimentos.router)
    app.include_router(unidades_medida.router)
    return app
