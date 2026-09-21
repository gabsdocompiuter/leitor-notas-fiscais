import json
import unittest
from decimal import Decimal
from datetime import datetime

from src.core.exceptions import ErroLeitura
from src.services.leitura_service import LeituraService
from src.core.utils import serializar

extrair_nota = LeituraService.extrair_nota
numero_br = LeituraService.numero_br


URL_TESTE = (
    "https://dfe-portal.svrs.rs.gov.br/Dfe/QrCodeNFce"
    "?p=43260907718633007868650080002005971056148317|3|1"
)

# Amostra sintética do layout, sem dados do consumidor ou dependência de rede.
HTML = """
<meta charset="utf-8">
<div><div id="u20">Mercado de teste</div><div>CNPJ: 00.000.000/0001-00</div></div>
<table id="tabResult">
  <tr><td>
    <span class="txtTit">PAO kg</span><span class="RCod">(Código: 10)</span>
    <span class="Rqtd"><strong>Qtde.:</strong>0,15</span>
    <span class="RUN"><strong>UN:</strong>UN</span>
    <span class="RvlUnit"><strong>Vl. Unit.:</strong>&nbsp;69,9</span>
  </td><td><span class="valor">10,48</span></td></tr>
  <tr><td>
    <span class="txtTit">QUEIJO 300g</span><span class="RCod">(Código: 20)</span>
    <span class="Rqtd"><strong>Qtde.:</strong>2</span>
    <span class="RUN"><strong>UN:</strong>UN</span>
    <span class="RvlUnit"><strong>Vl. Unit.:</strong>13,9</span>
  </td><td><span class="valor">27,80</span></td></tr>
</table>
<div id="totalNota">
  <div id="linhaTotal"><label>Qtd. total de itens:</label><span>2</span></div>
  <div id="linhaTotal"><label>Valor total R$:</label><span>38,28</span></div>
  <div id="linhaTotal"><label>Descontos R$:</label><span>2,60</span></div>
  <div id="linhaTotal"><label>Valor a pagar R$:</label><span>35,68</span></div>
</div>
<div id="infos">
  <strong>Número:</strong>200597 <strong>Série:</strong>8
  <strong>Emissão:</strong>08/09/2026 19:53:11
  <span class="chave">4326 0907 7186 3300 7868 6500 8000 2005 9710 5614 8317</span>
</div>
"""


class LeituraTests(unittest.TestCase):
    def test_leitura_preserva_total_da_origem_e_nao_importa(self):
        nota = extrair_nota(HTML.encode("utf-8"), URL_TESTE)
        self.assertEqual(nota.situacao, "lida")
        self.assertEqual(nota.emissao, datetime(2026, 9, 8, 19, 53, 11))
        self.assertEqual(nota.valor_a_pagar, Decimal("35.68"))
        self.assertEqual(nota.quantidade_itens, 2)
        # A origem contém 10,48; não se deve substituir por um recálculo de 10,485.
        self.assertEqual(nota.itens[0].valor_total, Decimal("10.48"))

    def test_alerta_nao_corrige_unidade_automaticamente(self):
        item = extrair_nota(HTML, URL_TESTE).itens[0]
        self.assertEqual(item.quantidade, Decimal("0.15"))
        self.assertEqual(item.unidade_original, "UN")
        self.assertEqual(len(item.alertas), 1)
        self.assertEqual(extrair_nota(HTML, URL_TESTE).itens[1].alertas, [])

    def test_json_preserva_decimais(self):
        dados = json.loads(serializar(extrair_nota(HTML, URL_TESTE)))
        self.assertEqual(dados["itens"][0]["quantidade"], "0.15")
        self.assertEqual(dados["itens"][1]["valor_total"], "27.80")

    def test_rejeita_item_ausente(self):
        with self.assertRaisesRegex(ErroLeitura, "Esperados 3 itens"):
            extrair_nota(HTML.replace("<span>2</span>", "<span>3</span>"), URL_TESTE)

    def test_rejeita_soma_incorreta(self):
        with self.assertRaisesRegex(ErroLeitura, "soma dos itens"):
            extrair_nota(HTML.replace("27,80", "27,81"), URL_TESTE)

    def test_rejeita_desconto_incompativel(self):
        with self.assertRaisesRegex(ErroLeitura, "Total menos desconto"):
            extrair_nota(HTML.replace("2,60", "2,61"), URL_TESTE)

    def test_aceita_nota_sem_desconto(self):
        sem_desconto = HTML.replace(
            '<div id="linhaTotal"><label>Descontos R$:</label><span>2,60</span></div>', ""
        ).replace("35,68", "38,28")
        self.assertEqual(extrair_nota(sem_desconto, URL_TESTE).desconto, Decimal("0.00"))

    def test_rejeita_resposta_de_outra_nota(self):
        with self.assertRaisesRegex(ErroLeitura, "chave retornada"):
            extrair_nota(HTML.replace("8317</span>", "8318</span>"), URL_TESTE)

    def test_rejeita_pagina_de_erro_com_http_200(self):
        with self.assertRaisesRegex(ErroLeitura, "tabela de itens"):
            extrair_nota("<html><h1>Serviço indisponível</h1></html>", URL_TESTE)

    def test_rejeita_campo_ausente_e_data_invalida(self):
        for alterado in (
            HTML.replace('class="Rqtd"', 'class="mudou"'),
            HTML.replace("08/09/2026", "31/02/2026"),
        ):
            with self.subTest(html=alterado), self.assertRaises(ErroLeitura):
                extrair_nota(alterado, URL_TESTE)

    def test_numeros_brasileiros_e_valores_invalidos(self):
        self.assertEqual(numero_br("1.234,567"), Decimal("1234.567"))
        for invalido in ("", "NaN", "1,2,3", "1.23", "-1", "R$ 10,00"):
            with self.subTest(numero=invalido), self.assertRaises(ErroLeitura):
                numero_br(invalido)


if __name__ == "__main__":
    unittest.main()
