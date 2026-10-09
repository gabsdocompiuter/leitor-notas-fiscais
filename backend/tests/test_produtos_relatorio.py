import unittest
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace as Dados
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

from src.services.relatorio_service import RelatorioService
from src.enums.unidade_medida import UnidadeMedida
from src.api.schemas.relatorio_response import RelatorioMensalResponse, ProdutoRelatorioResponse, ItemRelatorioResponse


class ProdutosRelatorioTests(unittest.TestCase):
    def setUp(self):
        self.categoria = Dados(id=uuid4(), nome="Categoria")
        self.produto = Dados(id=UUID(int=1), nome="Mesmo nome", categoria=self.categoria,
                             tratar_apenas_como_unidades=True, contem_variacoes=False, unidade_medida=None)
        self.outro = Dados(id=UUID(int=2), nome="Mesmo nome", categoria=self.categoria,
                           tratar_apenas_como_unidades=True, contem_variacoes=False, unidade_medida=None)
        self.servico = RelatorioService(MagicMock())

    def nota(self, produtos, valores, desconto="0", marca="A", variacao=None):
        if isinstance(marca, str):
            marca = Dados(id=UUID(int=ord(marca)), nome=marca)
        if isinstance(variacao, str):
            variacao = Dados(id=uuid4(), nome_exibicao=variacao)
        elif variacao is not None and not hasattr(variacao, "id"):
            variacao.id = uuid4()
            variacao.nome_exibicao = f"{variacao.quantidade} {variacao.unidade_medida.value}"
        return Dados(
            chave=str(uuid4()), numero="1", emissao=datetime(2026, 10, 1),
            estabelecimento=Dados(id=UUID(int=100), nome_exibicao="Mercado"), considerar_proximo_mes=False,
            valor_a_pagar=sum(map(Decimal, valores)) - Decimal(desconto),
            desconto=Decimal(desconto), itens=[Dados(
                id=uuid4(), apresentacao=Dados(produto=produto, marca=marca),
                variacao=variacao, valor_total=Decimal(valor), tags=[],
                quantidade_confirmada=Decimal(1),
            ) for produto, valor in zip(produtos, valores)],
        )

    def test_agrupa_identidade_preserva_homonimos_marcas_variacoes_e_rateio(self):
        notas = [self.nota([self.produto, self.outro], ["10", "20"], "3"),
                 self.nota([self.produto], ["5"], "1", marca="B", variacao="Grande")]
        with patch.object(self.servico, "_notas_mes", return_value=notas):
            grupos = self.servico.produtos_mes("2026-10", self.categoria.id)
            self.assertEqual([grupo.id for grupo in grupos], [self.outro.id, self.produto.id])
            compartilhado = grupos[1]
            self.assertEqual(compartilhado.quantidade_itens, 2)
            self.assertEqual(compartilhado.valor_bruto, Decimal("15.00"))
            self.assertEqual(compartilhado.desconto_rateado, Decimal("2.00"))
            self.assertEqual(compartilhado.total_pago, Decimal("13.00"))
            compras = self.servico.itens_mes("2026-10", self.categoria.id,
                                             produto_id=self.produto.id, limite=1, deslocamento=1)
            self.assertEqual(compras.total, 2)
            self.assertEqual(compras.itens[0].valor_pago, Decimal("4.00"))
            self.assertEqual(self.servico.itens_mes("2026-10", uuid4(), produto_id=self.produto.id).total, 0)
            self.assertEqual(self.servico.itens_mes("2026-10", self.categoria.id,
                             tag_id=uuid4(), produto_id=self.produto.id).total, 0)

    def test_desempata_por_id_e_mantem_produtos_zero(self):
        notas = [self.nota([self.outro, self.produto], ["0", "0"])]
        with patch.object(self.servico, "_notas_mes", return_value=notas):
            grupos = self.servico.produtos_mes("2026-10", self.categoria.id)
            self.assertEqual([grupo.id for grupo in grupos], [self.produto.id, self.outro.id])
            self.assertTrue(all(grupo.total_pago == Decimal("0.00") for grupo in grupos))
            self.assertEqual(self.servico.produtos_mes("2026-10", uuid4()), [])

    def test_pao_soma_tres_unidades_em_duas_compras_e_serializa(self):
        notas = [self.nota([self.produto], ["18.38"]), self.nota([self.produto], ["5.99"], "0.11")]
        notas[0].itens[0].quantidade_confirmada = Decimal(2)
        notas[0].itens[0].quantidade_pacotes = Decimal(1)
        notas[0].itens[0].unidades_por_pacote = Decimal(2)
        with patch.object(self.servico, "_notas_mes", return_value=notas):
            grupo = self.servico.produtos_mes("2026-10", self.categoria.id)[0]
            self.assertEqual(grupo.quantidade_itens, 2)
            self.assertEqual(grupo.quantidade_comprada, Decimal(3))
            self.assertEqual(ProdutoRelatorioResponse.from_entity(grupo).quantidade_comprada, "3")
            compra = self.servico.itens_mes("2026-10", produto_id=self.produto.id, limite=1).itens[0]
            self.assertEqual(ItemRelatorioResponse.from_entity(compra).quantidade_comprada, "2")

    def test_variacoes_convertem_conteudo_em_peso_e_volume(self):
        for destino, origem, tamanho, confirmado, esperado in [
            ("G", "G", "500", "2", "1000"), ("KG", "G", "500", "2", "1"),
            ("G", "KG", "0.5", "3", "1500"), ("L", "ML", "250", "3", "0.75"),
            ("ML", "L", "1.5", "2", "3000"),
        ]:
            with self.subTest(destino=destino, origem=origem):
                self.produto.tratar_apenas_como_unidades = False
                self.produto.contem_variacoes = True
                self.produto.unidade_medida = UnidadeMedida(destino)
                nota = self.nota([self.produto], ["10"], variacao=Dados(
                    quantidade=Decimal(tamanho), unidade_medida=UnidadeMedida(origem)))
                nota.itens[0].quantidade_confirmada = Decimal(confirmado)
                item = self.servico._itens([nota])[0]
                self.assertEqual(item.quantidade_comprada, Decimal(esperado))
                self.assertEqual(item.unidade_quantidade, destino)

    def test_grandezas_separadas_tags_e_soma_antes_da_paginacao(self):
        self.produto.tratar_apenas_como_unidades = False
        self.produto.unidade_medida = UnidadeMedida.GRAMA
        self.outro.tratar_apenas_como_unidades = False
        self.outro.unidade_medida = UnidadeMedida.QUILOGRAMA
        tag = Dados(id=uuid4(), nome="Compartilhada")
        notas = [self.nota([self.produto, self.outro], ["0", "10"]) for _ in range(52)]
        for nota in notas:
            nota.itens[0].quantidade_confirmada = Decimal("0.12345")
            for item in nota.itens:
                item.tags = [tag]
        with patch.object(self.servico, "_notas_mes", side_effect=lambda _, mes: notas if mes.month == 10 else []):
            relatorio = RelatorioMensalResponse.from_entity(self.servico.mensal("2026-10"))
            esperado = [{"quantidade": "52", "unidade": "KG"}, {"quantidade": "6.41940", "unidade": "G"}]
            self.assertEqual([q.model_dump() for q in relatorio.quantidades_compradas], esperado)
            self.assertEqual(relatorio.categorias[0].quantidades_compradas, relatorio.quantidades_compradas)
            self.assertEqual(relatorio.tags[0].quantidades_compradas, relatorio.quantidades_compradas)
            pagina = self.servico.itens_mes("2026-10", produto_id=self.produto.id, deslocamento=50)
            self.assertEqual(len(pagina.itens), 2)
            grupo = next(g for g in self.servico.produtos_mes("2026-10", self.categoria.id) if g.id == self.produto.id)
            self.assertEqual(grupo.quantidade_comprada, Decimal("6.41940"))
            self.assertEqual(grupo.total_pago, Decimal(0))

    def test_ausencia_de_quantidade_nao_inventa_unidade_comprada(self):
        nota = self.nota([self.produto], ["10"])
        nota.itens[0].quantidade_confirmada = None
        item = self.servico._itens([nota])[0]
        self.assertIsNone(item.quantidade_comprada)
        self.assertEqual(self.servico._quantidades([item]), [])

    def test_soma_tamanhos_diferentes_na_unidade_do_produto(self):
        self.produto.tratar_apenas_como_unidades = False
        self.produto.contem_variacoes = True
        self.produto.unidade_medida = UnidadeMedida.GRAMA
        notas = [self.nota([self.produto], ["10"], variacao=Dados(
            quantidade=Decimal("0.5"), unidade_medida=UnidadeMedida.QUILOGRAMA)),
            self.nota([self.produto], ["15"], variacao=Dados(
                quantidade=Decimal("250"), unidade_medida=UnidadeMedida.GRAMA))]
        notas[0].itens[0].quantidade_confirmada = Decimal(2)
        with patch.object(self.servico, "_notas_mes", return_value=notas):
            self.assertEqual(self.servico.produtos_mes("2026-10", self.categoria.id)[0].quantidade_comprada,
                             Decimal(1250))
        notas[0].itens[0].variacao.unidade_medida = UnidadeMedida.LITRO
        self.assertIsNone(self.servico._itens(notas)[0].quantidade_comprada)
