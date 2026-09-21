from collections.abc import Callable
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from ..core.config import CAMINHO_BANCO
from ..core.version import __version__
from ..core.persistence.banco_sqlite import BancoSQLite
from ..services.categoria_service import CategoriaService
from ..services.consulta_service import ConsultaService
from ..services.estabelecimento_service import EstabelecimentoService
from ..services.leitura_nota_service import LeituraNotaService
from ..services.marca_service import MarcaService
from ..services.nota_service import NotaService
from ..services.produto_service import ProdutoService
from ..services.revisao_nota_service import RevisaoNotaService
from ..services.variacao_produto_service import VariacaoProdutoService
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
    consultar: Callable[[str], bytes] = ConsultaService.consultar_nota,
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
    nota_service = NotaService(banco.session_factory)
    revisao_service = RevisaoNotaService(banco.session_factory)
    app.state.banco = banco
    app.state.nota_service = nota_service
    app.state.categoria_service = CategoriaService(banco.session_factory)
    app.state.marca_service = MarcaService(banco.session_factory)
    app.state.produto_service = ProdutoService(banco.session_factory)
    app.state.variacao_produto_service = VariacaoProdutoService(banco.session_factory)
    app.state.estabelecimento_service = EstabelecimentoService(banco.session_factory)
    app.state.revisao_nota_service = revisao_service
    app.state.leitura_nota_service = LeituraNotaService(
        banco.session_factory, consultar, revisao_service
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
