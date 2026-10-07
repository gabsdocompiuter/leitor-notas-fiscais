import re
from urllib.parse import parse_qs, urlsplit

from ..core.exceptions import ErroQrCode


def normalizar_url(entrada: str) -> str:
    """Converte chave ou link de consulta da SEFAZ RS em URL de QR Code."""
    entrada = entrada.strip()
    if re.fullmatch(r"[0-9]{44}", entrada):
        chave = entrada
    else:
        try:
            endereco = urlsplit(entrada)
            if (
                endereco.hostname == "www.sefaz.rs.gov.br"
                and endereco.path.casefold() == "/nfe/nfe-nfc.aspx"
            ):
                if (
                    endereco.scheme != "https"
                    or endereco.port not in (None, 443)
                    or endereco.username is not None
                    or endereco.password is not None
                    or endereco.fragment
                ):
                    raise ErroQrCode("Informe um link HTTPS de consulta da SEFAZ RS válido.")
                valores = parse_qs(endereco.query, keep_blank_values=True).get("chaveNFe", [])
                if len(valores) != 1 or not re.fullmatch(r"[0-9]{44}", valores[0]):
                    raise ErroQrCode(
                        "O link da SEFAZ deve conter um único parâmetro chaveNFe com 44 dígitos."
                    )
                chave = valores[0]
            else:
                extrair_chave(entrada)
                return entrada
        except ValueError as erro:
            raise ErroQrCode(f"Link de consulta inválido: {erro}") from erro

    url = f"https://dfe-portal.svrs.rs.gov.br/Dfe/QrCodeNFce?p={chave}|3|1"
    extrair_chave(url)
    return url


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
            raise ErroQrCode(
                "Informe uma chave de acesso de 44 dígitos, um link da SEFAZ RS "
                "ou uma URL HTTPS de QR Code da SEFAZ RS ou SVRS suportada."
            )
        parametros = parse_qs(endereco.query, keep_blank_values=True)
        valores = parametros.get("p", [])
        if len(valores) != 1:
            raise ErroQrCode("O QR Code deve conter um único parâmetro p.")
        partes = valores[0].split("|")
        if len(partes) < 3 or not re.fullmatch(r"\d{44}", partes[0]):
            raise ErroQrCode("O QR Code não contém uma chave de acesso de 44 dígitos.")
        if partes[0][:2] != "43":
            raise ErroQrCode("Somente notas do Rio Grande do Sul são suportadas nesta etapa.")
        return partes[0]
    except ValueError as erro:
        raise ErroQrCode(f"URL de QR Code inválida: {erro}") from erro


class QRCodeService:
    normalizar_url = staticmethod(normalizar_url)
    extrair_chave = staticmethod(extrair_chave)
