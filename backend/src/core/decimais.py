from decimal import Decimal, ROUND_HALF_UP

from .exceptions import DadosInvalidos


def formatar_decimal(valor: Decimal) -> str:
    texto = format(valor.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP), ',.3f')
    return texto.rstrip('0').rstrip('.').translate(str.maketrans({',': '.', '.': ','}))


def validar_quantidade(valor: Decimal) -> None:
    if not valor.is_finite() or valor <= 0:
        raise DadosInvalidos('A quantidade deve ser maior que zero.')
    if valor != valor.quantize(Decimal('0.001')):
        raise DadosInvalidos('A quantidade deve ter no máximo 3 casas decimais.')
