import unittest
from decimal import Decimal

from alembic import command

from src.core.exceptions import DadosInvalidos
from src.entities import ProdutoEntity, NotaEntity
from src.enums.situacao_nota import SituacaoNota
from tests import test_revisao_automatica as helpers


class PacotesTests(unittest.TestCase):
    criar_nota = helpers.RevisaoAutomaticaTests.criar_nota
    consultar = helpers.RevisaoAutomaticaTests.consultar

    def setUp(self):
        helpers.RevisaoAutomaticaTests.setUp(self)
        with self.banco.session_factory.begin() as session:
            produto = session.get(ProdutoEntity, self.produto_id)
            produto.tratar_apenas_como_unidades = True
            produto.unidade_medida = None

    def confirmar(self, nota, pacotes='1', unidades='30'):
        pacotes, unidades = Decimal(pacotes), Decimal(unidades)
        return self.revisao.revisar_item(
            nota.chave, nota.itens[0].id, self.produto_id, None, None,
            pacotes * unidades, pacotes, unidades,
        )

    def test_salva_reabre_e_edita_nota_importada(self):
        nota = self.criar_nota(1, quantidade='1')
        self.confirmar(nota)
        with self.banco.session_factory.begin() as session:
            session.get(NotaEntity, nota.id).situacao = SituacaoNota.IMPORTADA
        self.confirmar(nota, '2')
        atual = self.consultar(nota)
        item = atual.itens[0]
        self.assertEqual(atual.situacao, SituacaoNota.IMPORTADA)
        self.assertEqual(item.quantidade_confirmada, Decimal(60))
        self.assertEqual(item.quantidade_pacotes, Decimal(2))
        self.assertEqual(item.unidades_por_pacote, Decimal(30))
        self.assertEqual(item.quantidade, nota.itens[0].quantidade)
        self.assertEqual(item.valor_total, nota.itens[0].valor_total)

    def test_propaga_pacotes_e_reutiliza_associacao_por_codigo_e_descricao(self):
        origem = self.criar_nota(1, ['FILTRO C/30', 'FILTRO C/30'], quantidade='1')
        pendente = self.criar_nota(2, quantidade='2')
        resposta = self.confirmar(origem)
        self.assertEqual(resposta.itens[1].quantidade_pacotes, Decimal(2))
        self.assertEqual(self.consultar(pendente).itens[0].quantidade_pacotes, Decimal(2))
        codigo = self.criar_nota(3, quantidade='3')
        descricao = self.criar_nota(4, ['FILTRO C/30', 'OUTRO'],
                                    cnpj='22222222222222', quantidade='2')
        for nota, pacotes in [(codigo, 3), (descricao, 2)]:
            atual = self.revisao.aplicar_classificacoes_automaticas(nota.chave).itens[0]
            self.assertTrue(atual.revisado)
            self.assertEqual(atual.quantidade_confirmada, Decimal(pacotes * 30))
            self.assertEqual(atual.quantidade_pacotes, Decimal(pacotes))
            self.assertEqual(atual.unidades_por_pacote, Decimal(30))

    def test_pacotes_fracionarios_ficam_pendentes(self):
        origem = self.criar_nota(1, quantidade='2')
        pendente = self.criar_nota(2, quantidade='1')
        self.confirmar(origem)
        self.assertFalse(self.consultar(pendente).itens[0].revisado)
        outra = self.criar_nota(3, quantidade='1')
        atual = self.revisao.aplicar_classificacoes_automaticas(outra.chave).itens[0]
        self.assertFalse(atual.revisado)
        self.assertIsNone(atual.quantidade_pacotes)

    def test_rejeita_pacotes_invalidos_sem_salvar(self):
        nota = self.criar_nota(1, quantidade='1')
        for pacotes, unidades, total in [
            (None, '30', '30'), ('1', None, '30'), ('0', '30', '30'),
            ('-1', '30', '30'), ('1.5', '20', '30'), ('1', '0', '30'),
            ('1', '-30', '30'), ('1', '30.5', '30'), ('2', '30', '30'),
        ]:
            with self.subTest(pacotes=pacotes, unidades=unidades):
                with self.assertRaises(DadosInvalidos):
                    self.revisao.revisar_item(
                        nota.chave, nota.itens[0].id, self.produto_id, None, None,
                        Decimal(total), Decimal(pacotes) if pacotes is not None else None,
                        Decimal(unidades) if unidades is not None else None,
                    )
                self.assertFalse(self.consultar(nota).itens[0].revisado)

    def test_rejeita_pacotes_para_produto_por_peso(self):
        nota = self.criar_nota(1, quantidade='1')
        from src.enums.unidade_medida import UnidadeMedida
        with self.banco.session_factory.begin() as session:
            produto = session.get(ProdutoEntity, self.produto_id)
            produto.tratar_apenas_como_unidades = False
            produto.unidade_medida = UnidadeMedida.QUILOGRAMA
        with self.assertRaises(DadosInvalidos):
            self.confirmar(nota)

    def test_voltar_a_unidades_limpa_item_e_associacao(self):
        nota = self.criar_nota(1, quantidade='1')
        self.confirmar(nota)
        self.revisao.revisar_item(nota.chave, nota.itens[0].id, self.produto_id,
                                 None, None, Decimal(2))
        outra = self.criar_nota(2, quantidade='2')
        item = self.revisao.aplicar_classificacoes_automaticas(outra.chave).itens[0]
        self.assertEqual(item.quantidade_confirmada, Decimal(4))
        self.assertIsNone(item.quantidade_pacotes)
        self.assertIsNone(item.unidades_por_pacote)
        self.assertIsNone(self.consultar(nota).itens[0].quantidade_pacotes)

    def test_migracao_preserva_registros_antigos_sem_inferir_pacotes(self):
        nota = self.criar_nota(1, quantidade='1')
        self.revisao.revisar_item(nota.chave, nota.itens[0].id, self.produto_id,
                                 None, None, Decimal(30))
        configuracao = self.banco.configuracao_migrations(self.banco.caminho)
        command.downgrade(configuracao, '0003')
        self.banco.inicializar()
        self.banco.inicializar()
        item = self.consultar(nota).itens[0]
        self.assertEqual(item.quantidade_confirmada, Decimal(30))
        self.assertIsNone(item.quantidade_pacotes)
        self.assertIsNone(item.unidades_por_pacote)
        outra = self.criar_nota(2, quantidade='2')
        atual = self.revisao.aplicar_classificacoes_automaticas(outra.chave).itens[0]
        self.assertEqual(atual.quantidade_confirmada, Decimal(60))
        self.assertIsNone(atual.quantidade_pacotes)
