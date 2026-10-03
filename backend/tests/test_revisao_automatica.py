import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from src.core.exceptions import DadosInvalidos
from src.core.persistence.banco_sqlite import BancoSQLite
from src.entities import CategoriaEntity, ProdutoEntity, NotaEntity, TagEntity
from src.enums.situacao_nota import SituacaoNota
from src.enums.unidade_medida import UnidadeMedida
from src.services.leitura_service import LeituraService
from src.services.nota_service import NotaService
from src.services.revisao_nota_service import RevisaoNotaService
from tests.test_leitura import HTML, URL_TESTE


class RevisaoAutomaticaTests(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        self.banco = BancoSQLite(Path(self.temporario.name) / 'notas.sqlite3')
        self.addCleanup(self.banco.engine.dispose)
        self.notas = NotaService(self.banco.session_factory)
        self.revisao = RevisaoNotaService(self.banco.session_factory)
        with self.banco.session_factory.begin() as session:
            categoria = CategoriaEntity(nome='Alimentos')
            produto = ProdutoEntity(nome='Pão', categoria=categoria, nao_solicitar_marca=True,
                                    tratar_apenas_como_unidades=False, contem_variacoes=False,
                                    unidade_medida=UnidadeMedida.QUILOGRAMA)
            session.add(produto)
            session.flush()
            self.produto_id = produto.id

    def criar_nota(self, numero, descricoes=None, cnpj=None, unidade='UN', quantidade='0.15'):
        nota = LeituraService.extrair_nota(HTML, URL_TESTE)
        nota.chave = str(numero).zfill(44)
        if cnpj:
            nota.estabelecimento.cnpj = cnpj
        if descricoes:
            for item, descricao in zip(nota.itens, descricoes):
                item.descricao_original = descricao
        nota.itens[0].unidade_original = unidade
        nota.itens[0].quantidade = Decimal(quantidade)
        return self.notas.salvar(nota)

    def confirmar(self, nota, quantidade='0.15'):
        return self.revisao.revisar_item(nota.chave, nota.itens[0].id, self.produto_id,
                                        None, None, Decimal(quantidade))

    def consultar(self, nota):
        return self.notas.obter_por_chave(nota.chave)

    def test_revisa_mesma_nota_e_outras_aguardando_sem_importar(self):
        origem = self.criar_nota(1, ['PAO kg', '  pao   KG  '])
        outra = self.criar_nota(2, quantidade='0.45')
        com_codigo = self.criar_nota(3, ['Descrição antiga', 'QUEIJO 300g'])
        resposta = self.confirmar(origem, '0.3')
        self.assertTrue(all(item.revisado for item in resposta.itens))
        self.assertEqual(resposta.itens[1].quantidade_confirmada, Decimal('4'))
        for nota, esperado in [(outra, '0.9'), (com_codigo, '0.3')]:
            atual = self.consultar(nota)
            self.assertTrue(atual.itens[0].revisado)
            self.assertFalse(atual.itens[1].revisado)
            self.assertEqual(atual.itens[0].quantidade_confirmada, Decimal(esperado))
            self.assertEqual(atual.situacao, SituacaoNota.EM_REVISAO)
            self.assertIsNone(atual.importada_em)

    def test_descricao_em_outro_estabelecimento_e_unidade_compativel(self):
        origem = self.criar_nota(1, unidade='KG', quantidade='1')
        outra = self.criar_nota(2, ['  pao KG ', 'QUEIJO 300g'], cnpj='22222222222222',
                                unidade='G', quantidade='250')
        self.confirmar(origem, '2')
        item = self.consultar(outra).itens[0]
        self.assertTrue(item.revisado)
        self.assertEqual(item.quantidade_confirmada, Decimal('0.5'))
        self.assertEqual(item.apresentacao.produto.id, self.produto_id)

    def test_nao_revisa_unidade_incompativel_ou_item_diferente_em_outra_loja(self):
        origem = self.criar_nota(1)
        incompativel = self.criar_nota(2, unidade='ML')
        diferente = self.criar_nota(3, ['Outro produto', 'QUEIJO 300g'], cnpj='22222222222222')
        self.confirmar(origem)
        for nota in [incompativel, diferente]:
            self.assertFalse(self.consultar(nota).itens[0].revisado)
            self.assertEqual(self.consultar(nota).situacao, SituacaoNota.LIDA)

    def test_preserva_itens_revisados_notas_importadas_e_tags(self):
        origem = self.criar_nota(1)
        revisada = self.criar_nota(2)
        importada = self.criar_nota(3)
        pendente = self.criar_nota(4)
        with self.banco.session_factory.begin() as session:
            entidade = session.get(NotaEntity, revisada.id)
            entidade.itens[0].revisado = True
            entidade.itens[0].quantidade_confirmada = Decimal('7')
            session.get(NotaEntity, importada.id).situacao = SituacaoNota.IMPORTADA
            entidade_pendente = session.get(NotaEntity, pendente.id)
            entidade_pendente.itens[0].tags.append(TagEntity(nome='Festa', nome_normalizado='festa'))
        self.confirmar(origem)
        self.assertEqual(self.consultar(revisada).itens[0].quantidade_confirmada, Decimal('7'))
        self.assertFalse(self.consultar(importada).itens[0].revisado)
        atual = self.consultar(pendente)
        self.assertTrue(atual.itens[0].revisado)
        self.assertEqual([tag.nome for tag in atual.itens[0].tags], ['Festa'])
        self.assertEqual(atual.itens[0].descricao_original, pendente.itens[0].descricao_original)
        self.assertEqual(atual.itens[0].valor_total, pendente.itens[0].valor_total)

    def test_quantidade_inteira_e_variacao_sao_preservadas(self):
        from src.entities import VariacaoProdutoEntity
        with self.banco.session_factory.begin() as session:
            produto = session.get(ProdutoEntity, self.produto_id)
            produto.contem_variacoes = True
            variacao = VariacaoProdutoEntity(produto=produto, quantidade=Decimal('250'),
                                            unidade_medida=UnidadeMedida.GRAMA)
            session.add(variacao)
            session.flush()
            variacao_id = variacao.id
        origem = self.criar_nota(1, quantidade='3')
        inteira = self.criar_nota(2, quantidade='6')
        fracionaria = self.criar_nota(3, quantidade='4')
        self.revisao.revisar_item(origem.chave, origem.itens[0].id, self.produto_id,
                                 None, variacao_id, Decimal('1'))
        atual = self.consultar(inteira).itens[0]
        self.assertTrue(atual.revisado)
        self.assertEqual(atual.quantidade_confirmada, Decimal('2'))
        self.assertEqual(atual.variacao.id, variacao_id)
        self.assertFalse(self.consultar(fracionaria).itens[0].revisado)

    def test_erro_na_classificacao_nao_atualiza_pendentes(self):
        origem = self.criar_nota(1)
        outra = self.criar_nota(2)
        with self.assertRaises(DadosInvalidos):
            self.confirmar(origem, '0.0001')
        self.assertFalse(self.consultar(origem).itens[0].revisado)
        self.assertFalse(self.consultar(outra).itens[0].revisado)

    def test_revisao_de_nota_importada_nao_propaga(self):
        origem = self.criar_nota(1)
        outra = self.criar_nota(2)
        with self.banco.session_factory.begin() as session:
            session.get(NotaEntity, origem.id).situacao = SituacaoNota.IMPORTADA
        self.confirmar(origem)
        self.assertFalse(self.consultar(outra).itens[0].revisado)
