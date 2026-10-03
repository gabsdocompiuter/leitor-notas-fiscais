from decimal import Decimal
from uuid import uuid4
import unittest

from pydantic import ValidationError
from src.api.schemas.variacao_produto_request import VariacaoProdutoRequest
from src.api.schemas.revisao_item_request import RevisaoItemRequest
from src.core.decimais import formatar_decimal, validar_quantidade
from src.core.exceptions import DadosInvalidos


class DecimaisTests(unittest.TestCase):
    def test_formatacao(self):
        for valor, esperado in [('1.15', '1,15'), ('1123.1500', '1.123,15'),
                                ('1.001', '1,001'), ('1.12356', '1,124'), ('250', '250')]:
            self.assertEqual(formatar_decimal(Decimal(valor)), esperado)

    def test_validacao_dos_servicos(self):
        validar_quantidade(Decimal('1.001'))
        validar_quantidade(Decimal('1.15000'))
        for valor in ['1.0001', '0.000001', '0', '-1', 'NaN', 'Infinity']:
            with self.assertRaises(DadosInvalidos):
                validar_quantidade(Decimal(valor))

    def test_requisicoes_recusam_mais_de_tres_casas(self):
        for valor in ['1.0001', '0.000001']:
            with self.assertRaises(ValidationError):
                VariacaoProdutoRequest(quantidade=valor, unidade_medida='KG')
            with self.assertRaises(ValidationError):
                RevisaoItemRequest(produto_id=uuid4(), quantidade_confirmada=valor)
        self.assertEqual(VariacaoProdutoRequest(quantidade='1.15000', unidade_medida='KG').quantidade, Decimal('1.15'))
