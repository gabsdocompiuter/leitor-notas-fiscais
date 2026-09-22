import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from bs4 import BeautifulSoup, Tag

from ..core.exceptions import ErroLeitura
from ..dtos.estabelecimento_dto import EstabelecimentoDTO
from ..dtos.item_dto import ItemDTO
from ..dtos.nota_dto import NotaDTO
from .qrcode_service import QRCodeService


def texto(elemento: Tag) -> str:
    return " ".join(elemento.stripped_strings)


def campo(raiz: Tag | BeautifulSoup, seletor: str) -> str:
    elemento = raiz.select_one(seletor)
    if elemento is None:
        raise ErroLeitura(f"Campo não encontrado no HTML: {seletor}")
    return texto(elemento)


def numero_br(valor: str) -> Decimal:
    """Converte números brasileiros sem passar por ponto flutuante."""
    if not re.fullmatch(r"(?:\d{1,3}(?:\.\d{3})+|\d+)(?:,\d+)?", valor):
        raise ErroLeitura(f"Número inválido: {valor!r}")
    try:
        return Decimal(valor.replace(".", "").replace(",", "."))
    except InvalidOperation as erro:
        raise ErroLeitura(f"Número inválido: {valor!r}") from erro


def extrair_numero(valor: str) -> Decimal:
    # Os campos numéricos podem conter rótulos como 'Qtde.:' e 'Vl. Unit.:'.
    return numero_br(valor.rsplit(":", 1)[-1].strip())


def dinheiro(valor: str) -> Decimal:
    resultado = extrair_numero(valor)
    if resultado != resultado.quantize(Decimal("0.01")):
        raise ErroLeitura(f"Total monetário com fração de centavo: {valor!r}")
    return resultado.quantize(Decimal("0.01"))


def capturar(padrao: str, conteudo: str, nome: str) -> str:
    resultado = re.search(padrao, conteudo, flags=re.IGNORECASE)
    if resultado is None:
        raise ErroLeitura(f"Não foi possível identificar {nome}.")
    return resultado.group(1)


def extrair_nota(html: bytes | str, url: str) -> NotaDTO:
    """Lê o layout QR Code da SVRS, sem acessar rede ou gravar no banco."""
    chave_esperada = QRCodeService.extrair_chave(url)
    pagina = BeautifulSoup(html, "html.parser")
    tabela = pagina.select_one("#tabResult")
    if tabela is None:
        raise ErroLeitura(
            "A resposta não contém a tabela de itens da SVRS. "
            "Pode ser uma página de erro ou um layout diferente."
        )

    itens = []
    for indice, linha in enumerate(tabela.select("tr"), start=1):
        descricao = campo(linha, "span.txtTit")
        unidade = campo(linha, ".RUN").rsplit(":", 1)[-1].strip().upper()
        alertas = []
        # Apenas sinaliza esta inconsistência observável; não converte nem corrige.
        if re.search(r"\bkg\s*$", descricao, re.IGNORECASE) and unidade != "KG":
            alertas.append(
                f"Descrição termina em kg, mas a unidade da nota é {unidade}. "
                "Confirmar a unidade na revisão."
            )
        itens.append(ItemDTO(
            numero=indice,
            codigo=capturar(r"Código:\s*([^()]+)", campo(linha, ".RCod"), "código").strip(),
            descricao_original=descricao,
            quantidade=extrair_numero(campo(linha, ".Rqtd")),
            unidade_original=unidade,
            valor_unitario=extrair_numero(campo(linha, ".RvlUnit")),
            valor_total=dinheiro(campo(linha, ".valor")),
            alertas=alertas,
        ))

    totais = {}
    for rotulo in pagina.select("#totalNota label"):
        valor = rotulo.find_next_sibling("span")
        if valor is not None:
            totais[texto(rotulo).rstrip(":").strip().casefold()] = texto(valor)

    def total(nome: str) -> str:
        try:
            return totais[nome.casefold()]
        except KeyError as erro:
            raise ErroLeitura(f"Total não encontrado: {nome}") from erro

    quantidade_texto = total("Qtd. total de itens")
    if not quantidade_texto.isdigit():
        raise ErroLeitura("A quantidade total de itens não é um inteiro.")
    quantidade = int(quantidade_texto)
    bruto_texto = totais.get("valor total r$")
    if bruto_texto is None:
        if "descontos r$" in totais:
            raise ErroLeitura("Total não encontrado: Valor total R$")
        # A SVRS pode omitir o valor total quando não há desconto.
        bruto_texto = total("Valor a pagar R$")
    bruto = dinheiro(bruto_texto)
    desconto = dinheiro(totais.get("descontos r$", "0,00"))
    liquido = dinheiro(total("Valor a pagar R$"))
    if not itens or quantidade != len(itens):
        raise ErroLeitura(f"Esperados {quantidade} itens, mas foram lidos {len(itens)}.")
    if sum((item.valor_total for item in itens), Decimal("0")) != bruto:
        raise ErroLeitura("A soma dos itens difere do valor total da nota.")
    if bruto - desconto != liquido:
        raise ErroLeitura("Total menos desconto não corresponde ao valor a pagar.")

    chave = re.sub(r"\s", "", campo(pagina, ".chave"))
    if chave != chave_esperada:
        raise ErroLeitura("A chave retornada não corresponde à URL consultada.")
    informacoes = campo(pagina, "#infos")
    data = capturar(r"Emissão:\s*(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2})", informacoes, "emissão")
    try:
        emissao = datetime.strptime(data, "%d/%m/%Y %H:%M:%S")
    except ValueError as erro:
        raise ErroLeitura(f"Data de emissão inválida: {data}") from erro
    cabecalho = pagina.select_one("#u20")
    if cabecalho is None or cabecalho.parent is None:
        raise ErroLeitura("Emitente não encontrado.")
    cnpj = capturar(r"CNPJ:\s*([\d./-]+)", texto(cabecalho.parent), "CNPJ do emitente")
    return NotaDTO(
        chave=chave,
        numero=capturar(r"Número:\s*(\d+)", informacoes, "número da nota"),
        serie=capturar(r"Série:\s*(\d+)", informacoes, "série"),
        estabelecimento=EstabelecimentoDTO(
            razao_social=texto(cabecalho),
            cnpj=re.sub(r"\D", "", cnpj),
        ),
        emissao=emissao,
        quantidade_itens=quantidade,
        valor_total=bruto,
        desconto=desconto,
        valor_a_pagar=liquido,
        itens=itens,
        url_origem=url,
    )


class LeituraService:
    numero_br = staticmethod(numero_br)
    extrair_nota = staticmethod(extrair_nota)
