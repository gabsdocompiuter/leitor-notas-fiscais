from decimal import Decimal

from ..models.nota import Nota


def moeda(valor: Decimal) -> str:
    return f"R$ {valor:.2f}".replace(".", ",")


def mostrar(nota: Nota) -> None:
    print(f"{nota.estabelecimento.nome_exibicao}\nEmissão: {nota.emissao.isoformat(sep=' ')}")
    print(f"Nota {nota.numero} / série {nota.serie} — {nota.situacao.value}\n")
    for item in nota.itens:
        quantidade = str(item.quantidade).replace(".", ",")
        print(f"{item.numero:02d}. {item.descricao_original}")
        print(f"    {quantidade} {item.unidade_original} x {moeda(item.valor_unitario)} = {moeda(item.valor_total)}")
        for alerta in item.alertas:
            print(f"    ALERTA: {alerta}")
    print(f"\nItens: {nota.quantidade_itens}")
    print(f"Total: {moeda(nota.valor_total)} | Desconto: {moeda(nota.desconto)}")
    print(f"A pagar: {moeda(nota.valor_a_pagar)}")
