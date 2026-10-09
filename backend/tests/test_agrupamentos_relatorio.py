import unittest
from decimal import Decimal
from types import SimpleNamespace as Dados
from unittest.mock import patch
from uuid import UUID, uuid4

from tests import test_produtos_relatorio as dados_produtos
from src.api.schemas.relatorio_response import AgrupamentoRelatorioResponse, ItemRelatorioResponse
from src.enums.unidade_medida import UnidadeMedida


class AgrupamentosRelatorioTests(unittest.TestCase):
    def setUp(self):
        self.dados = dados_produtos.ProdutosRelatorioTests()
        self.dados.setUp()
        self.servico = self.dados.servico

    def grupos(self, agrupador):
        return self.servico.agrupamentos_mes("2026-10", self.dados.categoria.id, self.dados.produto.id, agrupador)

    def test_marcas_homonimas_sem_marca_e_media_exata(self):
        marca = Dados(id=UUID(int=10), nome="Igual")
        outra = Dados(id=UUID(int=11), nome="Igual")
        notas = [self.dados.nota([self.dados.produto], ["10"], "1", marca),
                 self.dados.nota([self.dados.produto], ["5.01"], marca=marca),
                 self.dados.nota([self.dados.produto], ["8"], marca=outra),
                 self.dados.nota([self.dados.produto], ["0"], marca=None)]
        notas[0].itens[0].quantidade_confirmada = Decimal(2)
        with patch.object(self.servico, "_notas_mes", return_value=notas):
            grupos = self.grupos("marca")
            self.assertEqual([g.id for g in grupos], [marca.id, outra.id, None])
            self.assertEqual(grupos[0].quantidade_registros, 2)
            self.assertEqual(grupos[0].quantidade_comprada, Decimal(3))
            self.assertEqual(grupos[0].quantidade_unidades, Decimal(3))
            self.assertEqual(grupos[0].total_pago, Decimal("14.01"))
            self.assertEqual(grupos[0].media_por_compra, Decimal("7.01"))
            self.assertEqual(AgrupamentoRelatorioResponse.from_entity(grupos[0]).media_por_compra, "7.01")
            self.assertEqual(grupos[-1].nome, "Sem marca")
            self.assertEqual(grupos[-1].total_pago, 0)
            itens = self.servico.itens_mes("2026-10", produto_id=self.dados.produto.id,
                                          agrupador="marca", grupo_id=marca.id)
            self.assertEqual(itens.total, 2)
            resposta = ItemRelatorioResponse.from_entity(itens.itens[0])
            self.assertEqual(resposta.marca_id, marca.id)
            self.assertEqual(resposta.marca, "Igual")
            self.assertEqual(self.servico.itens_mes("2026-10", agrupador="marca", grupo_id="sem_grupo").total, 1)
            self.assertEqual(self.servico.itens_mes("2026-10", categoria_id=uuid4(), agrupador="marca", grupo_id=marca.id).total, 0)
            self.assertEqual(self.servico.itens_mes("2026-10", tag_id=uuid4(), agrupador="marca", grupo_id=marca.id).total, 0)

    def test_estabelecimentos_variacoes_e_duas_linhas_da_mesma_nota(self):
        variacao = Dados(id=UUID(int=30), nome_exibicao="500 G")
        outra = Dados(id=UUID(int=31), nome_exibicao="1 KG")
        notas = [self.dados.nota([self.dados.produto, self.dados.produto], ["10", "15"], variacao=variacao),
                 self.dados.nota([self.dados.produto], ["8"], variacao=outra),
                 self.dados.nota([self.dados.produto], ["1"], variacao=None)]
        notas[1].estabelecimento = Dados(id=UUID(int=101), nome_exibicao="Mercado")
        with patch.object(self.servico, "_notas_mes", return_value=notas):
            grupos = self.grupos("variacao")
            self.assertEqual([g.nome for g in grupos], ["500 G", "1 KG", "Sem variação"])
            self.assertEqual(grupos[0].quantidade_registros, 2)
            estabelecimentos = self.grupos("estabelecimento")
            self.assertEqual(len(estabelecimentos), 2)
            self.assertEqual(estabelecimentos[0].total_pago, Decimal(26))
            compras = self.servico.itens_mes("2026-10", agrupador="variacao", grupo_id=variacao.id)
            self.assertEqual(compras.total, 2)
            self.assertEqual(compras.itens[0].variacao, "500 G")
            self.assertEqual(self.servico.itens_mes("2026-10", agrupador="estabelecimento", grupo_id=UUID(int=101)).total, 1)

    def test_grupos_inteiros_acima_de_50_compras_e_desempate(self):
        notas = [self.dados.nota([self.dados.produto], ["1"]) for _ in range(52)]
        with patch.object(self.servico, "_notas_mes", return_value=notas):
            grupo = self.grupos("marca")[0]
            self.assertEqual(grupo.quantidade_registros, 52)
            self.assertEqual(grupo.total_pago, Decimal(52))
            self.assertEqual(grupo.media_por_compra, Decimal(1))
            pagina = self.servico.itens_mes("2026-10", deslocamento=50, agrupador="marca", grupo_id=grupo.id)
            self.assertEqual(len(pagina.itens), 2)
            self.assertEqual(pagina.total, 52)
        marcas = [Dados(id=UUID(int=i), nome="Mesmo") for i in range(51, 0, -1)]
        notas = [self.dados.nota([self.dados.produto], ["0"], marca=m) for m in marcas]
        with patch.object(self.servico, "_notas_mes", return_value=notas):
            grupos = self.grupos("marca")
            self.assertEqual(len(grupos), 51)
            self.assertEqual([str(g.id) for g in grupos], sorted(str(m.id) for m in marcas))
        with patch.object(self.servico, "_notas_mes", return_value=[]):
            self.assertEqual(self.grupos("marca"), [])

    def test_duas_embalagens_em_um_registro_e_soma_de_tamanhos(self):
        produto = self.dados.produto
        produto.tratar_apenas_como_unidades = False
        produto.contem_variacoes = True
        produto.unidade_medida = UnidadeMedida.QUILOGRAMA
        notas = [self.dados.nota([produto], ["31.8"], "0.29", variacao=Dados(
            quantidade=Decimal(400), unidade_medida=UnidadeMedida.GRAMA))]
        notas[0].itens[0].quantidade_confirmada = Decimal(2)
        with patch.object(self.servico, "_notas_mes", return_value=notas):
            grupo = self.grupos("marca")[0]
            self.assertEqual(grupo.quantidade_registros, 1)
            self.assertEqual(grupo.quantidade_unidades, Decimal(2))
            self.assertEqual(grupo.quantidade_comprada, Decimal("0.8"))
            self.assertEqual(grupo.media_por_compra, Decimal("31.51"))
            self.assertEqual(AgrupamentoRelatorioResponse.from_entity(grupo).quantidade_unidades, "2")
            item = self.servico.itens_mes("2026-10").itens[0]
            self.assertEqual(ItemRelatorioResponse.from_entity(item).quantidade_unidades, "2")
        notas.append(self.dados.nota([produto], ["10"], variacao=Dados(
            quantidade=Decimal("0.25"), unidade_medida=UnidadeMedida.QUILOGRAMA)))
        with patch.object(self.servico, "_notas_mes", return_value=notas):
            grupo = self.grupos("marca")[0]
            self.assertEqual(grupo.quantidade_unidades, Decimal(3))
            self.assertEqual(grupo.quantidade_comprada, Decimal("1.05"))

    def test_pacotes_soma_completa_e_ausencia_nao_exibe_parcial(self):
        notas = [self.dados.nota([self.dados.produto], ["1"]) for _ in range(52)]
        for nota in notas:
            item = nota.itens[0]
            item.quantidade_confirmada = Decimal(60)
            item.quantidade_pacotes = Decimal(2)
            item.unidades_por_pacote = Decimal(30)
        with patch.object(self.servico, "_notas_mes", return_value=notas):
            self.assertEqual(self.grupos("marca")[0].quantidade_unidades, Decimal(3120))
            pagina = self.servico.itens_mes("2026-10", deslocamento=50)
            self.assertEqual(len(pagina.itens), 2)
            self.assertEqual(pagina.itens[0].quantidade_unidades, Decimal(60))
            notas[-1].itens[0].quantidade_confirmada = None
            self.assertIsNone(self.grupos("marca")[0].quantidade_unidades)
            notas.reverse()
            self.assertIsNone(self.grupos("marca")[0].quantidade_unidades)

    def test_peso_e_volume_diretos_nao_inventam_unidades(self):
        produto = self.dados.produto
        produto.tratar_apenas_como_unidades = False
        for unidade in [UnidadeMedida.QUILOGRAMA, UnidadeMedida.LITRO]:
            produto.unidade_medida = unidade
            nota = self.dados.nota([produto], ["5"])
            nota.itens[0].quantidade_confirmada = Decimal("0.8")
            with patch.object(self.servico, "_notas_mes", return_value=[nota]):
                grupo = self.grupos("marca")[0]
                self.assertIsNone(grupo.quantidade_unidades)
                self.assertEqual(grupo.quantidade_comprada, Decimal("0.8"))
                self.assertIsNone(self.servico.itens_mes("2026-10").itens[0].quantidade_unidades)
