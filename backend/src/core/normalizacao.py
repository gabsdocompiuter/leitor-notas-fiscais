from decimal import Decimal


def limpar_nome(valor: str) -> str:
    return " ".join(valor.split())


def normalizar_nome(valor: str) -> str:
    return limpar_nome(valor).casefold()


def decimal_texto(valor: Decimal) -> str:
    texto = format(valor, "f")
    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")
    return texto or "0"
