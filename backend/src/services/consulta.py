from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..core.config import LIMITE_HTML
from ..core.exceptions import ErroConsulta
from .qrcode import extrair_chave


def consultar_nota(url: str) -> bytes:
    """Consulta a URL de QR Code recebida, com TLS verificado."""
    extrair_chave(url)
    requisicao = Request(
        url,
        headers={"User-Agent": "LeitorNFCePessoal/0.1", "Accept": "text/html"},
    )
    try:
        with urlopen(requisicao, timeout=30) as resposta:
            conteudo = resposta.read(LIMITE_HTML + 1)
            if len(conteudo) > LIMITE_HTML:
                raise ErroConsulta("A resposta ultrapassou o limite de 5 MB.")
            return conteudo
    except HTTPError as erro:
        raise ErroConsulta(f"A SEFAZ respondeu com HTTP {erro.code}.") from erro
    except (URLError, TimeoutError, OSError) as erro:
        raise ErroConsulta(f"Não foi possível consultar a SEFAZ: {erro}") from erro
