from fastapi import Request

from ..services.categoria_service import CategoriaService
from ..services.estabelecimento_service import EstabelecimentoService
from ..services.leitura_nota_service import LeituraNotaService
from ..services.marca_service import MarcaService
from ..services.nota_service import NotaService
from ..services.produto_service import ProdutoService
from ..services.revisao_nota_service import RevisaoNotaService
from ..services.variacao_produto_service import VariacaoProdutoService


def obter_nota_service(request: Request) -> NotaService:
    return request.app.state.nota_service


def obter_leitura_nota_service(request: Request) -> LeituraNotaService:
    return request.app.state.leitura_nota_service


def obter_categoria_service(request: Request) -> CategoriaService:
    return request.app.state.categoria_service


def obter_marca_service(request: Request) -> MarcaService:
    return request.app.state.marca_service


def obter_produto_service(request: Request) -> ProdutoService:
    return request.app.state.produto_service


def obter_variacao_produto_service(request: Request) -> VariacaoProdutoService:
    return request.app.state.variacao_produto_service


def obter_estabelecimento_service(request: Request) -> EstabelecimentoService:
    return request.app.state.estabelecimento_service


def obter_revisao_nota_service(request: Request) -> RevisaoNotaService:
    return request.app.state.revisao_nota_service
