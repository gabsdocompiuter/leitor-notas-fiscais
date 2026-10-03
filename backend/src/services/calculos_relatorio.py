from datetime import datetime
from decimal import Decimal

from ..core.exceptions import DadosInvalidos

CENTAVO = Decimal("0.01")


def deslocar_mes(inicio: datetime, quantidade: int) -> datetime:
    indice = inicio.year * 12 + inicio.month - 1 + quantidade
    ano, mes = divmod(indice, 12)
    return datetime(ano, mes + 1, 1)


def inicio_mes(mes: str) -> datetime:
    try:
        inicio = datetime.strptime(mes, "%Y-%m")
        if not 2 <= inicio.year <= 9998:
            raise ValueError()
        return inicio
    except ValueError as erro:
        raise DadosInvalidos("Informe um mês válido no formato AAAA-MM.") from erro


def ratear_desconto(valores: list[Decimal], desconto: Decimal) -> list[Decimal]:
    """Rateio proporcional em centavos; maiores restos recebem os centavos restantes.

    Em empates, prevalece a ordem dos itens da nota. Não utiliza ponto flutuante.
    """
    pesos = [int(valor * 100) for valor in valores]
    total = sum(pesos)
    if total == 0:
        return [Decimal("0.00") for _ in valores]
    centavos = int(desconto * 100)
    parcelas = [divmod(centavos * peso, total) for peso in pesos]
    distribuido = [parte for parte, _ in parcelas]
    restantes = centavos - sum(distribuido)
    ordem = sorted(range(len(valores)), key=lambda i: (-parcelas[i][1], i))
    for indice in ordem[:restantes]:
        distribuido[indice] += 1
    return [(Decimal(parte) / 100).quantize(CENTAVO) for parte in distribuido]
