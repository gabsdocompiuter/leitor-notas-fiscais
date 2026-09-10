import re
from urllib.parse import parse_qs, urlsplit

from ..core.exceptions import ErroConsulta


def extrair_chave(url: str) -> str:
    """Valida os endereços QR Code suportados do RS e obtém a chave informada."""
    try:
        endereco = urlsplit(url)
        permitidos = {
            ("dfe-portal.svrs.rs.gov.br", "/dfe/qrcodenfce"),
            ("www.sefaz.rs.gov.br", "/nfce/nfce-com.aspx"),
        }
        if (
            endereco.scheme != "https"
            or (endereco.hostname, endereco.path.casefold()) not in permitidos
            or endereco.port not in (None, 443)
            or endereco.username is not None
            or endereco.password is not None
            or endereco.fragment
        ):
            raise ErroConsulta("Informe uma URL HTTPS de QR Code da SEFAZ RS ou SVRS suportada.")
        parametros = parse_qs(endereco.query, keep_blank_values=True)
        valores = parametros.get("p", [])
        if len(valores) != 1:
            raise ErroConsulta("O QR Code deve conter um único parâmetro p.")
        partes = valores[0].split("|")
        if len(partes) < 3 or not re.fullmatch(r"\d{44}", partes[0]):
            raise ErroConsulta("O QR Code não contém uma chave de acesso de 44 dígitos.")
        if partes[0][:2] != "43":
            raise ErroConsulta("Somente notas do Rio Grande do Sul são suportadas nesta etapa.")
        return partes[0]
    except ValueError as erro:
        raise ErroConsulta(f"URL de QR Code inválida: {erro}") from erro
