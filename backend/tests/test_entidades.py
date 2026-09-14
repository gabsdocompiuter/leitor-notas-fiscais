import json
import unittest
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from src.models.apresentacao_produto import ApresentacaoProduto
from src.models.associacao_produto import AssociacaoProduto
from src.models.categoria import Categoria
from src.models.estabelecimento import Estabelecimento
from src.models.leitura_nota import LeituraNota
from src.models.marca import Marca
from src.models.produto import Produto
from src.models.situacao_nota import SituacaoNota
from src.models.unidade_medida import UnidadeMedida
from src.presentation.serializacao import serializar
from src.services.leitura import extrair_nota
from test_leitura import HTML, URL_TESTE


class EntidadesTests(unittest.TestCase):
    def test_apelido_opcional_sem_perder_razao_social(self):
        estabelecimento = Estabelecimento("00000000000100", "Mercado de teste")
        self.assertIsNone(estabelecimento.apelido)
        self.assertEqual(estabelecimento.nome_exibicao, "Mercado de teste")
        estabelecimento.apelido = "Mercado perto de casa"
        self.assertEqual(estabelecimento.nome_exibicao, "Mercado perto de casa")
        self.assertEqual(estabelecimento.razao_social, "Mercado de teste")
        estabelecimento.apelido = " "
        self.assertEqual(estabelecimento.nome_exibicao, "Mercado de teste")

    def test_refinamento_preserva_item_original_e_situacao_lida(self):
        nota = extrair_nota(HTML, URL_TESTE)
        item = nota.itens[0]
        original = (item.descricao_original, item.quantidade, item.unidade_original, item.valor_total)
        produto = Produto("Pão", Categoria("Alimentação"), unidade_medida=UnidadeMedida.QUILOGRAMA)
        item.apresentacao = ApresentacaoProduto(produto)
        item.quantidade_confirmada = Decimal("0.15")
        item.revisado = True
        self.assertEqual(original, (item.descricao_original, item.quantidade, item.unidade_original, item.valor_total))
        self.assertEqual(nota.situacao, SituacaoNota.LIDA)

    def test_marcas_compartilham_produto_mas_variantes_nao(self):
        categoria = Categoria("Alimentação")
        integral = Produto("Leite integral", categoria, unidade_medida=UnidadeMedida.LITRO)
        desnatado = Produto("Leite desnatado", categoria, unidade_medida=UnidadeMedida.LITRO)
        tirol = ApresentacaoProduto(integral, Marca("Tirol"))
        dalia = ApresentacaoProduto(integral, Marca("Dália"))
        self.assertEqual(tirol.produto.id, dalia.produto.id)
        self.assertNotEqual(integral.id, desnatado.id)
        self.assertNotEqual(tirol.id, dalia.id)

    def test_mesmo_codigo_pode_pertencer_a_estabelecimentos_diferentes(self):
        produto = Produto("Queijo", Categoria("Alimentação"), unidade_medida=UnidadeMedida.QUILOGRAMA)
        apresentacao = ApresentacaoProduto(produto)
        a = AssociacaoProduto(Estabelecimento("00000000000100", "Loja A"), "20", apresentacao)
        b = AssociacaoProduto(Estabelecimento("00000000000200", "Loja B"), "20", apresentacao)
        self.assertNotEqual((a.estabelecimento.cnpj, a.codigo_item), (b.estabelecimento.cnpj, b.codigo_item))

    def test_captura_pode_existir_antes_da_consulta_e_apos_falha(self):
        leitura = LeituraNota(URL_TESTE)
        self.assertIsNone(leitura.nota)
        self.assertIsNotNone(leitura.criada_em.tzinfo)
        leitura.erro_consulta = "Serviço indisponível"
        self.assertEqual(leitura.url, URL_TESTE)
        self.assertIsNone(leitura.nota)

    def test_json_contem_estabelecimento_identidades_e_data_iso(self):
        nota = extrair_nota(HTML, URL_TESTE)
        nota.estabelecimento.apelido = "Meu mercado"
        dados = json.loads(serializar(nota))
        self.assertEqual(dados["estabelecimento"]["apelido"], "Meu mercado")
        self.assertEqual(dados["estabelecimento"]["cnpj"], "00000000000100")
        self.assertEqual(dados["emissao"], "2026-09-08T19:53:11")
        self.assertIsInstance(nota.emissao, datetime)
        self.assertEqual(UUID(dados["id"]), nota.id)
        self.assertEqual(dados["itens"][0]["quantidade"], "0.15")
        self.assertEqual(dados["situacao"], "lida")
        self.assertNotIn("emitente", dados)
