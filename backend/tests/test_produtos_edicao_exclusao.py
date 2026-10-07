import sqlite3
import unittest
from contextlib import closing
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.entities import (
    ApresentacaoProdutoEntity, AssociacaoProdutoEntity, ItemEntity,
    ProdutoEntity, VariacaoProdutoEntity,
)
from src.services.leitura_service import LeituraService
from tests import test_catalogo_revisao as catalogo
from tests.test_leitura import HTML, URL_TESTE


CHAVE = catalogo.CHAVE


class ProdutosEdicaoExclusaoTests(unittest.TestCase):
    setUp = catalogo.CatalogoRevisaoApiTests.setUp
    produto = catalogo.CatalogoRevisaoApiTests.produto
    ler = catalogo.CatalogoRevisaoApiTests.ler
    revisar = catalogo.CatalogoRevisaoApiTests.revisar

    def atualizar(self, produto, **mudancas):
        dados = {campo: produto[campo] for campo in (
            'nome', 'nao_solicitar_marca', 'tratar_apenas_como_unidades',
            'contem_variacoes', 'unidade_medida',
        )}
        dados['categoria_id'] = produto['categoria']['id']
        dados.update(mudancas)
        return self.cliente.patch(f"/produtos/{produto['id']}", json=dados)

    def restricoes(self, produto):
        resposta = self.cliente.get(f"/produtos/{produto['id']}/restricoes")
        self.assertEqual(resposta.status_code, 200, resposta.text)
        return resposta.json()

    def excluir(self, produto):
        return self.cliente.delete(f"/produtos/{produto['id']}")

    def criar_dependencias(self, produto):
        with self.app.state.banco.session_factory.begin() as session:
            entidade = session.get(ProdutoEntity, UUID(produto['id']))
            apresentacao = ApresentacaoProdutoEntity(produto=entidade)
            variacao = VariacaoProdutoEntity(
                produto=entidade, quantidade=Decimal('100'),
                unidade_medida=entidade.unidade_medida,
            )
            session.add_all([apresentacao, variacao])
            session.flush()
            return apresentacao.id, variacao.id

    def test_edita_importado_preservando_historico_e_reagrupando_relatorios(self):
        nota = self.ler()
        produto = self.produto(nao_solicitar_marca=True)
        for indice, item in enumerate(nota['itens']):
            self.assertEqual(self.revisar(item, produto, '0.6', marca=indice == 1).status_code, 200)
        anterior = self.cliente.post(f'/notas/{CHAVE}/importacao').json()
        mes = anterior['emissao'][:7]
        resumo_anterior = self.cliente.get('/relatorios/mensal', params={'mes': mes}).json()
        categoria = self.cliente.post('/categorias', json={'nome': 'Corrigida'}).json()
        resposta = self.atualizar(produto, nome='Nome corrigido',
                                  categoria_id=categoria['id'], nao_solicitar_marca=False)
        self.assertEqual(resposta.status_code, 200, resposta.text)
        depois = self.cliente.get(f'/notas/{CHAVE}').json()
        self.assertEqual(depois['situacao'], anterior['situacao'])
        self.assertEqual(depois['importada_em'], anterior['importada_em'])
        for antigo, atual in zip(anterior['itens'], depois['itens']):
            for campo in ('quantidade', 'quantidade_confirmada', 'valor_unitario',
                          'valor_total', 'quantidade_pacotes', 'unidades_por_pacote', 'revisado'):
                self.assertEqual(atual[campo], antigo[campo])
            self.assertEqual(atual['apresentacao']['marca'], antigo['apresentacao']['marca'])
            self.assertEqual(atual['apresentacao']['produto']['nome'], 'Nome corrigido')
            self.assertEqual(atual['apresentacao']['produto']['categoria'], categoria)
        resumo = self.cliente.get('/relatorios/mensal', params={'mes': mes}).json()
        self.assertEqual(resumo['total_pago'], resumo_anterior['total_pago'])
        self.assertEqual([grupo['id'] for grupo in resumo['categorias']], [categoria['id']])
        detalhes = self.cliente.get('/relatorios/mensal/itens', params={'mes': mes}).json()
        self.assertTrue(all(item['produto'] == 'Nome corrigido' for item in detalhes['itens']))
        self.assertEqual(self.revisar(depois['itens'][0], produto, 1, marca=False).status_code, 422)
        self.assertEqual(self.revisar(depois['itens'][0], produto, 1).status_code, 200)

    def test_exigir_marca_invalida_so_pendentes_sem_marca_e_impede_automaticas(self):
        nota = self.ler()
        produto = self.produto(nao_solicitar_marca=True)
        self.revisar(nota['itens'][0], produto, 1, marca=False)
        antes = self.revisar(nota['itens'][1], produto, 1).json()
        self.assertEqual(self.atualizar(produto, nao_solicitar_marca=False).status_code, 200)
        depois = self.cliente.get(f'/notas/{CHAVE}').json()
        self.assertFalse(depois['itens'][0]['revisado'])
        self.assertTrue(depois['itens'][1]['revisado'])
        for campo in ('apresentacao', 'quantidade_confirmada'):
            if campo == 'apresentacao':
                self.assertEqual(depois['itens'][0][campo]['id'], antes['itens'][0][campo]['id'])
            else:
                self.assertEqual(depois['itens'][0][campo], antes['itens'][0][campo])
        self.assertEqual(self.cliente.post(f'/notas/{CHAVE}/importacao').status_code, 409)
        nova = LeituraService.extrair_nota(HTML, URL_TESTE)
        nova.chave = '1'.zfill(44)
        self.app.state.nota_service.salvar(nova)
        aplicada = self.app.state.revisao_nota_service.aplicar_classificacoes_automaticas(nova.chave)
        self.assertFalse(aplicada.itens[0].revisado)
        self.assertTrue(aplicada.itens[1].revisado)

    def test_bloqueia_estrutura_e_exclusao_em_revisao_e_importada(self):
        nota = self.ler()
        produto = self.produto(nao_solicitar_marca=True)
        for item in nota['itens']:
            self.revisar(item, produto, 1, marca=False)
        for importada in (False, True):
            if importada:
                self.cliente.post(f'/notas/{CHAVE}/importacao')
            with self.subTest(importada=importada):
                restricoes = self.restricoes(produto)
                self.assertFalse(restricoes['pode_alterar_estrutura'])
                self.assertFalse(restricoes['pode_excluir'])
                for mudancas in (
                    {'unidade_medida': 'G'}, {'contem_variacoes': True},
                    {'tratar_apenas_como_unidades': True, 'unidade_medida': None},
                ):
                    self.assertEqual(self.atualizar(produto, **mudancas).status_code, 409)
                self.assertEqual(self.atualizar(produto, nome='Correção segura').status_code, 200)
                self.assertEqual(self.excluir(produto).status_code, 409)

    def test_duplicidade_e_categoria_inexistente_nao_invalidam_itens(self):
        nota = self.ler()
        produto = self.produto('Primeiro', nao_solicitar_marca=True)
        self.produto('Duplicado')
        self.revisar(nota['itens'][0], produto, 1, marca=False)
        self.assertEqual(self.atualizar(produto, nome='duplicado', nao_solicitar_marca=False).status_code, 409)
        self.assertEqual(self.atualizar(produto, categoria_id=str(uuid4()), nao_solicitar_marca=False).status_code, 404)
        atual = self.cliente.get(f'/notas/{CHAVE}').json()['itens'][0]
        self.assertTrue(atual['revisado'])
        self.assertTrue(atual['apresentacao']['produto']['nao_solicitar_marca'])

    def test_edita_estrutura_sem_uso_mas_nao_desativa_variacoes_existentes(self):
        produto = self.produto()
        self.assertTrue(self.restricoes(produto)['pode_alterar_estrutura'])
        self.assertEqual(self.atualizar(produto, unidade_medida='G').status_code, 200)
        variado = self.produto('Variado', contem_variacoes=True)
        self.criar_dependencias(variado)
        self.assertEqual(self.atualizar(variado, contem_variacoes=False).status_code, 409)
        self.assertEqual(self.atualizar(variado, nome='Variado corrigido').status_code, 200)

    def test_exclui_vazio_e_retorna_404_apos_exclusao(self):
        produto = self.produto()
        self.assertTrue(self.restricoes(produto)['pode_excluir'])
        self.assertEqual(self.excluir(produto).status_code, 204)
        self.assertEqual(self.excluir(produto).status_code, 404)
        self.assertEqual(self.cliente.get(f"/produtos/{produto['id']}/restricoes").status_code, 404)

    def test_limpa_dependencias_sem_uso_e_vinculos_cruzados(self):
        nota = self.ler()
        produto = self.produto('Sem uso', contem_variacoes=True)
        outro = self.produto('Outro', contem_variacoes=True)
        apresentacao_id, variacao_id = self.criar_dependencias(produto)
        outra_apresentacao, outra_variacao = self.criar_dependencias(outro)
        with self.app.state.banco.session_factory.begin() as session:
            for codigo, apresentacao, variacao in (
                ('a', apresentacao_id, variacao_id),
                ('b', outra_apresentacao, variacao_id),
                ('c', apresentacao_id, outra_variacao),
            ):
                session.add(AssociacaoProdutoEntity(
                    estabelecimento_id=UUID(nota['estabelecimento']['id']), codigo_item=codigo,
                    descricao_original=codigo, descricao_normalizada=codigo,
                    apresentacao_id=apresentacao, variacao_id=variacao,
                    fator_conversao=Decimal(1),
                ))
        self.assertFalse(self.restricoes(produto)['pode_alterar_estrutura'])
        self.assertTrue(self.restricoes(produto)['pode_excluir'])
        self.assertEqual(self.atualizar(produto, unidade_medida='G').status_code, 409)
        self.assertEqual(self.excluir(produto).status_code, 204)
        with self.app.state.banco.session_factory() as session:
            self.assertEqual(list(session.scalars(select(AssociacaoProdutoEntity))), [])
            self.assertIsNone(session.get(ApresentacaoProdutoEntity, apresentacao_id))
            self.assertIsNone(session.get(VariacaoProdutoEntity, variacao_id))
            self.assertIsNotNone(session.get(VariacaoProdutoEntity, outra_variacao))
        self.assertEqual(self.cliente.get(f"/produtos/{outro['id']}").status_code, 200)
        self.assertEqual(self.cliente.get(f"/categorias/{self.categoria['id']}").status_code, 200)
        self.assertEqual(self.cliente.get(f"/marcas/{self.marca['id']}").status_code, 200)
        self.assertEqual(self.cliente.get(f"/estabelecimentos/{nota['estabelecimento']['id']}").status_code, 200)

    def test_item_vinculado_apenas_por_variacao_bloqueia_exclusao_e_estrutura(self):
        nota = self.ler()
        produto = self.produto(contem_variacoes=True)
        _, variacao_id = self.criar_dependencias(produto)
        with self.app.state.banco.session_factory.begin() as session:
            item = session.get(ItemEntity, UUID(nota['itens'][0]['id']))
            item.variacao_id = variacao_id
        self.assertFalse(self.restricoes(produto)['pode_excluir'])
        self.assertFalse(self.restricoes(produto)['pode_alterar_estrutura'])
        self.assertEqual(self.excluir(produto).status_code, 409)

    def test_falha_na_exclusao_desfaz_limpeza_integralmente(self):
        nota = self.ler()
        produto = self.produto(contem_variacoes=True)
        apresentacao_id, variacao_id = self.criar_dependencias(produto)
        with self.app.state.banco.session_factory.begin() as session:
            associacao = AssociacaoProdutoEntity(
                estabelecimento_id=UUID(nota['estabelecimento']['id']), codigo_item='rollback',
                descricao_original='rollback', descricao_normalizada='rollback',
                apresentacao_id=apresentacao_id, variacao_id=variacao_id,
                fator_conversao=Decimal(1),
            )
            session.add(associacao)
            session.flush()
            associacao_id = associacao.id
        with closing(sqlite3.connect(self.caminho)) as conexao:
            conexao.execute("""CREATE TRIGGER impedir_exclusao BEFORE DELETE ON produtos
                BEGIN SELECT RAISE(ABORT, 'falha simulada'); END""")
            conexao.commit()
        with self.assertRaises(IntegrityError):
            self.app.state.produto_service.excluir(UUID(produto['id']))
        with self.app.state.banco.session_factory() as session:
            self.assertIsNotNone(session.get(ProdutoEntity, UUID(produto['id'])))
            self.assertIsNotNone(session.get(ApresentacaoProdutoEntity, apresentacao_id))
            self.assertIsNotNone(session.get(VariacaoProdutoEntity, variacao_id))
            self.assertIsNotNone(session.get(AssociacaoProdutoEntity, associacao_id))


if __name__ == '__main__':
    unittest.main()
