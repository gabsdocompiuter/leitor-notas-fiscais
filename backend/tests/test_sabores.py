from uuid import uuid4
import unittest

from tests import test_catalogo_revisao as catalogo


CHAVE = catalogo.CHAVE


class SaboresTests(unittest.TestCase):
    setUp = catalogo.CatalogoRevisaoApiTests.setUp
    produto = catalogo.CatalogoRevisaoApiTests.produto
    ler = catalogo.CatalogoRevisaoApiTests.ler

    def sabor(self, produto, nome="Morango"):
        resposta = self.cliente.post(f"/produtos/{produto['id']}/sabores", json={"nome": nome})
        self.assertEqual(resposta.status_code, 201, resposta.text)
        return resposta.json()

    def test_preferencia_nao_solicitar_sabor_persiste_em_criacao_edicao_e_consulta(self):
        padrao = self.produto()
        self.assertFalse(padrao["nao_solicitar_sabor"])
        produto = self.produto("Sem sabor", nao_solicitar_sabor=True)
        self.assertTrue(produto["nao_solicitar_sabor"])
        url = f"/produtos/{produto['id']}"
        self.assertTrue(self.cliente.get(url).json()["nao_solicitar_sabor"])
        dados = {"nome": produto["nome"], "categoria_id": self.categoria["id"],
                 "unidade_medida": "KG", "nao_solicitar_sabor": False}
        resposta = self.cliente.patch(url, json=dados)
        self.assertEqual(resposta.status_code, 200, resposta.text)
        self.assertFalse(resposta.json()["nao_solicitar_sabor"])
        self.assertFalse(self.cliente.get(url).json()["nao_solicitar_sabor"])

    def test_catalogo_isolado_normalizacao_edicao_e_exclusao_produto(self):
        produto = self.produto()
        outro = self.produto("Outro")
        sabor = self.sabor(produto, "  Morango  ")
        self.assertEqual(self.sabor(produto, "morango")["id"], sabor["id"])
        self.assertEqual(self.cliente.get(f"/produtos/{outro['id']}/sabores").json(), [])
        self.assertNotEqual(self.sabor(outro)["id"], sabor["id"])
        url = f"/produtos/{produto['id']}/sabores/{sabor['id']}"
        self.assertEqual(self.cliente.patch(url, json={"nome": "Chocolate"}).json()["nome"], "Chocolate")
        self.sabor(produto, "Baunilha")
        self.assertEqual(self.cliente.patch(url, json={"nome": "baunilha"}).status_code, 409)
        self.assertEqual(self.cliente.post(f"/produtos/{produto['id']}/sabores", json={"nome": "  "}).status_code, 422)
        self.assertEqual(self.cliente.get(f"/produtos/{uuid4()}/sabores").status_code, 404)
        self.assertEqual(self.cliente.delete(f"/produtos/{produto['id']}").status_code, 204)

    def test_revisao_valida_produto_e_propaga_sabor_no_historico(self):
        nota = self.ler()
        produto = self.produto(nao_solicitar_marca=True)
        outro = self.produto("Outro", nao_solicitar_marca=True)
        sabor = self.sabor(produto)
        errado = self.sabor(outro)
        url = f"/notas/{CHAVE}/itens/{nota['itens'][0]['id']}"
        dados = {"produto_id": produto["id"], "quantidade_confirmada": 1, "sabor_id": errado["id"]}
        self.assertEqual(self.cliente.patch(url, json=dados).status_code, 422)
        dados['sabor_id'] = sabor['id']
        resposta = self.cliente.patch(url, json=dados)
        self.assertEqual(resposta.status_code, 200, resposta.text)
        self.assertEqual(resposta.json()['itens'][0]['sabor'], sabor)
        with self.app.state.banco.session_factory() as session:
            from sqlalchemy import select
            from src.entities import AssociacaoProdutoEntity
            self.assertEqual(str(session.scalar(select(AssociacaoProdutoEntity)).sabor_id), sabor['id'])

    def test_compra_manual_preserva_sabor_e_protege_historico(self):
        produto = self.produto(nao_solicitar_marca=True)
        sabor = self.sabor(produto)
        estabelecimento = self.cliente.post('/estabelecimentos', json={'apelido': 'Loja'}).json()
        resposta = self.cliente.post('/notas/manuais', json={
            'estabelecimento_id': estabelecimento['id'], 'data': '2026-10-18',
            'itens': [{'produto_id': produto['id'], 'sabor_id': sabor['id'],
                       'quantidade_confirmada': 1, 'valor_total': '10.00'}],
        })
        self.assertEqual(resposta.status_code, 201, resposta.text)
        self.assertEqual(resposta.json()['itens'][0]['sabor'], sabor)
        url = f"/produtos/{produto['id']}/sabores/{sabor['id']}"
        self.assertEqual(self.cliente.patch(url, json={'nome': 'Novo'}).status_code, 409)
        detalhes = self.cliente.get('/relatorios/mensal/itens', params={'mes': '2026-10'}).json()
        self.assertEqual(detalhes['itens'][0]['sabor'], 'Morango')

    def test_migration_estrutural_preserva_produtos_e_tamanhos(self):
        import sqlite3
        from contextlib import closing
        from pathlib import Path
        from src.core.persistence.banco_sqlite import BancoSQLite

        caminho = Path(self.temporario.name) / 'anterior.sqlite3'
        BancoSQLite.migrar(caminho, '0006')
        categoria, produto, tamanho = (uuid4().hex for _ in range(3))
        with closing(sqlite3.connect(caminho)) as conexao:
            conexao.execute('INSERT INTO categorias (id, nome) VALUES (?, ?)', (categoria, 'Alimentos'))
            conexao.execute('INSERT INTO produtos (id, nome, categoria_id, nao_solicitar_marca, '
                            'tratar_apenas_como_unidades, contem_variacoes, unidade_medida) '
                            'VALUES (?, ?, ?, 1, 0, 1, ?)', (produto, 'Iogurte', categoria, 'G'))
            conexao.execute('INSERT INTO variacoes_produto (id, produto_id, quantidade, unidade_medida) '
                            'VALUES (?, ?, ?, ?)', (tamanho, produto, '170', 'G'))
            conexao.commit()
            anterior = conexao.execute('SELECT * FROM produtos').fetchall()
            tamanhos = conexao.execute('SELECT * FROM variacoes_produto').fetchall()
        BancoSQLite.migrar(caminho)
        with closing(sqlite3.connect(caminho)) as conexao:
            self.assertEqual(conexao.execute('SELECT id, nome, categoria_id, nao_solicitar_marca, tratar_apenas_como_unidades, contem_variacoes, unidade_medida FROM produtos').fetchall(), anterior)
            self.assertEqual(conexao.execute('SELECT nao_solicitar_sabor FROM produtos').fetchall(), [(1,)])
            self.assertEqual(conexao.execute('SELECT * FROM variacoes_produto').fetchall(), tamanhos)
            self.assertEqual(conexao.execute('SELECT * FROM sabores_produto').fetchall(), [])
            self.assertEqual(conexao.execute('PRAGMA foreign_key_check').fetchall(), [])
