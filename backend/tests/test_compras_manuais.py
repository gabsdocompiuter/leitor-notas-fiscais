import sqlite3
import tempfile
import unittest
from pathlib import Path
from contextlib import closing
from uuid import uuid4

from fastapi.testclient import TestClient

from src.api.app import criar_app
from src.core.persistence.banco_sqlite import BancoSQLite
from tests.test_leitura import HTML, URL_TESTE


class ComprasManuaisTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.caminho = Path(self.temp.name) / 'notas.sqlite3'
        self.consultas = 0

        def consultar(_):
            self.consultas += 1
            return HTML.encode('utf-8')

        self.cliente = TestClient(criar_app(self.caminho, consultar, permitir_importacao_banco=True))
        self.addCleanup(self.cliente.app.state.banco.fechar)
        self.addCleanup(self.cliente.close)
        self.categoria = self.cliente.post('/categorias', json={'nome': 'Alimentação'}).json()
        self.produto = self.criar_produto()
        self.loja = self.cliente.post('/estabelecimentos', json={'apelido': 'Feira'}).json()

    def criar_produto(self, **opcoes):
        dados = dict(nome='Banana', categoria_id=self.categoria['id'],
                     nao_solicitar_marca=True, tratar_apenas_como_unidades=False,
                     contem_variacoes=False, unidade_medida='KG')
        dados.update(opcoes)
        resposta = self.cliente.post('/produtos', json=dados)
        self.assertEqual(resposta.status_code, 201, resposta.text)
        return resposta.json()

    def entrada(self, **opcoes):
        dados = dict(estabelecimento_id=self.loja['id'], data='2026-10-01',
                     itens=[dict(produto_id=self.produto['id'], quantidade_confirmada='1.5', valor_total='12.34')])
        dados.update(opcoes)
        return dados

    def criar(self, **opcoes):
        resposta = self.cliente.post('/notas/manuais', json=self.entrada(**opcoes))
        self.assertEqual(resposta.status_code, 201, resposta.text)
        return resposta.json()

    def test_adicionar_item_concluido_atualiza_totais_e_relatorios(self):
        nota = self.criar()
        caminho = '/notas/' + nota['id']
        entrada = dict(produto_id=self.produto['id'], quantidade_confirmada='2.5', valor_unitario='3.33')
        resposta = self.cliente.post(caminho + '/itens', json=entrada)
        self.assertEqual(resposta.status_code, 201, resposta.text)
        salva = resposta.json()
        self.assertEqual(salva['quantidade_itens'], 2)
        self.assertEqual(salva['valor_total'], '20.67')
        self.assertEqual(salva['valor_a_pagar'], '20.67')
        self.assertEqual(salva['situacao'], 'importada')
        self.assertEqual(salva['importada_em'], nota['importada_em'])
        self.assertEqual(salva['itens'][0], nota['itens'][0])
        novo = salva['itens'][1]
        self.assertEqual(novo['numero'], 2)
        self.assertTrue(novo['revisado'])
        self.assertFalse(novo['ignorado'])
        self.assertEqual(novo['descricao_original'], self.produto['nome'])
        self.assertEqual(novo['valor_total'], '8.33')
        self.assertEqual(self.cliente.get(caminho).json()['valor_total'], '20.67')
        mensal = self.cliente.get('/relatorios/mensal', params={'mes': '2026-10'}).json()
        self.assertEqual(mensal['total_pago'], '20.67')
        self.assertEqual(mensal['quantidade_notas'], 1)
        segunda = self.cliente.post(caminho + '/itens', json=entrada)
        self.assertEqual(segunda.status_code, 201, segunda.text)
        self.assertEqual(segunda.json()['itens'][-1]['numero'], 3)
        self.assertEqual(segunda.json()['quantidade_itens'], 3)

    def test_adicionar_item_invalido_preserva_compra(self):
        nota = self.criar()
        caminho = '/notas/' + nota['id']
        entrada = dict(produto_id=self.produto['id'], quantidade_confirmada='1', valor_total='2.00')
        invalidados = [
            {**entrada, 'quantidade_confirmada': '0'},
            {**entrada, 'valor_total': '1.234'},
            {**entrada, 'valor_unitario': '2'},
            {**entrada, 'produto_id': str(uuid4())},
            {**entrada, 'quantidade_pacotes': '1', 'unidades_por_pacote': '2'},
        ]
        marca_obrigatoria = self.criar_produto(nome='Café', nao_solicitar_marca=False)
        invalidados.append({**entrada, 'produto_id': marca_obrigatoria['id']})
        variacao_obrigatoria = self.criar_produto(nome='Ovos', contem_variacoes=True, tratar_apenas_como_unidades=False, unidade_medida='KG')
        invalidados.append({**entrada, 'produto_id': variacao_obrigatoria['id']})
        for dados in invalidados:
            with self.subTest(dados=dados):
                resposta = self.cliente.post(caminho + '/itens', json=dados)
                self.assertIn(resposta.status_code, (404, 422), resposta.text)
                self.assertEqual(self.cliente.get(caminho).json(), nota)

    def test_adicionar_item_com_pacotes_e_total_informado(self):
        nota = self.criar()
        produto = self.criar_produto(nome='Filtros', tratar_apenas_como_unidades=True, unidade_medida=None)
        resposta = self.cliente.post('/notas/' + nota['id'] + '/itens', json={
            'produto_id': produto['id'], 'quantidade_confirmada': '20',
            'quantidade_pacotes': '2', 'unidades_por_pacote': '10', 'valor_total': '7.00',
        })
        self.assertEqual(resposta.status_code, 201, resposta.text)
        salva = resposta.json()
        self.assertEqual(salva['valor_total'], '19.34')
        self.assertEqual(salva['itens'][-1]['quantidade_pacotes'], '2')
        self.assertEqual(salva['itens'][-1]['quantidade_confirmada'], '20')

    def test_adicionar_item_rejeita_fiscal_ignorada_e_inexistente(self):
        entrada = dict(produto_id=self.produto['id'], quantidade_confirmada='1', valor_total='2.00')
        fiscal = self.cliente.post('/leituras', json={'url': URL_TESTE}).json()['nota']
        self.assertEqual(self.cliente.post('/notas/' + fiscal['chave'] + '/itens', json=entrada).status_code, 409)
        nota = self.criar()
        caminho = '/notas/' + nota['id']
        self.cliente.patch(caminho + '/ignorada', json={'ignorada': True})
        ignorada = self.cliente.get(caminho).json()
        self.assertEqual(self.cliente.post(caminho + '/itens', json=entrada).status_code, 409)
        self.assertEqual(self.cliente.get(caminho).json(), ignorada)
        self.assertEqual(self.cliente.post('/notas/' + str(uuid4()) + '/itens', json=entrada).status_code, 404)

    def test_estabelecimento_somente_apelido_busca_e_obrigatoriedade(self):
        self.assertIsNone(self.loja['cnpj'])
        self.assertIsNone(self.loja['razao_social'])
        outra = self.cliente.post('/estabelecimentos', json={'apelido': '  Padaria  '})
        self.assertEqual(outra.status_code, 201)
        self.assertEqual(outra.json()['nome_exibicao'], 'Padaria')
        encontrados = self.cliente.get('/estabelecimentos', params={'busca': 'Feira'}).json()
        self.assertEqual([loja['id'] for loja in encontrados], [self.loja['id']])
        for apelido in ('', '  ', 'a' * 101):
            with self.subTest(apelido=apelido):
                self.assertEqual(self.cliente.post('/estabelecimentos', json={'apelido': apelido}).status_code, 422)
        self.assertEqual(self.cliente.patch('/estabelecimentos/' + self.loja['id'],
                                           json={'apelido': None}).status_code, 422)

    def test_compra_concluida_totais_data_e_relatorios(self):
        itens = self.entrada()['itens'] + [dict(produto_id=self.produto['id'],
                                               quantidade_confirmada='0.5', valor_total='0.10')]
        nota = self.criar(itens=itens)
        self.assertEqual(nota['origem'], 'manual')
        self.assertEqual(nota['situacao'], 'importada')
        self.assertEqual(nota['emissao'][:10], '2026-10-01')
        self.assertEqual(nota['valor_a_pagar'], '12.44')
        self.assertEqual(nota['quantidade_itens'], 2)
        self.assertEqual(nota['desconto'], '0')
        for campo in ('chave', 'numero', 'serie', 'url_origem'):
            self.assertIsNone(nota[campo])
        self.assertFalse(nota['ignorada'])
        self.assertTrue(all(i['revisado'] and not i['ignorado'] for i in nota['itens']))
        self.assertEqual(nota['itens'][0]['descricao_original'], self.produto['nome'])
        self.assertEqual(self.consultas, 0)
        mensal = self.cliente.get('/relatorios/mensal', params={'mes': '2026-10'}).json()
        self.assertEqual(mensal['total_pago'], '12.44')
        pagina = self.cliente.get('/relatorios/mensal/itens', params={'mes': '2026-10'}).json()
        self.assertEqual(pagina['itens'][0]['nota_id'], nota['id'])
        self.assertIsNone(pagina['itens'][0]['chave_nota'])
        self.criar()
        self.assertEqual(self.cliente.get('/relatorios/mensal', params={'mes': '2026-10'}).json()['quantidade_notas'], 2)

    def test_estabelecimento_fiscal_existente_preserva_cnpj(self):
        fiscal = self.cliente.post('/leituras', json={'url': URL_TESTE}).json()['nota']
        manual = self.criar(estabelecimento_id=fiscal['estabelecimento']['id'])
        self.assertEqual(manual['estabelecimento'], fiscal['estabelecimento'])
        self.assertEqual(self.consultas, 1)
        repetida = self.cliente.post('/leituras', json={'url': URL_TESTE}).json()['nota']
        self.assertEqual(repetida['id'], fiscal['id'])
        self.assertEqual(repetida['origem'], 'sefaz')

    def test_validacao_dos_campos_sem_salvar_parcialmente(self):
        item = self.entrada()['itens'][0]
        casos = [
            self.entrada(itens=[]), self.entrada(data='2026-99-99'),
            self.entrada(estabelecimento_id=str(uuid4())),
        ]
        for campos in ({'produto_id': str(uuid4())}, {'produto_id': None},
                       {'quantidade_confirmada': '0'}, {'quantidade_confirmada': '1.0001'},
                       {'valor_total': '-1'}, {'valor_total': '1.001'}, {'valor_total': 'NaN'}):
            casos.append(self.entrada(itens=[dict(item, **campos)]))
        # O primeiro item cria uma apresentação antes de o segundo falhar.
        casos.append(self.entrada(itens=[item, dict(item, produto_id=str(uuid4()))]))
        for entrada in casos:
            with self.subTest(entrada=entrada):
                resposta = self.cliente.post('/notas/manuais', json=entrada)
                self.assertIn(resposta.status_code, (404, 422), resposta.text)
                self.assertEqual(self.cliente.get('/notas').json(), [])
        with closing(sqlite3.connect(self.caminho)) as conexao:
            self.assertEqual(conexao.execute('SELECT COUNT(*) FROM apresentacoes_produto').fetchone()[0], 0)

    def test_marca_variacao_e_pacotes_reutilizam_validacoes(self):
        produto = self.criar_produto(nome='Ovos', nao_solicitar_marca=False,
                                     tratar_apenas_como_unidades=True, unidade_medida=None)
        item = dict(produto_id=produto['id'], quantidade_confirmada='12', valor_total='18.00',
                    quantidade_pacotes='2', unidades_por_pacote='6')
        self.assertEqual(self.cliente.post('/notas/manuais', json=self.entrada(itens=[item])).status_code, 422)
        marca = self.cliente.post('/marcas', json={'nome': 'Granja'}).json()
        item['marca_id'] = marca['id']
        nota = self.criar(itens=[item])
        self.assertEqual(nota['itens'][0]['quantidade_confirmada'], '12')
        self.assertEqual(nota['itens'][0]['quantidade_pacotes'], '2')
        for campos in ({'quantidade_confirmada': '1.5'}, {'unidades_por_pacote': '5'},
                       {'quantidade_pacotes': None}, {'marca_id': str(uuid4())}):
            self.assertIn(self.cliente.post('/notas/manuais',
                json=self.entrada(itens=[dict(item, **campos)])).status_code, (404, 422))
        variado = self.criar_produto(nome='Iogurte', contem_variacoes=True, unidade_medida='G')
        variacao = self.cliente.post('/produtos/' + variado['id'] + '/variacoes',
                                    json={'quantidade': '180', 'unidade_medida': 'G'}).json()
        variado_item = dict(produto_id=variado['id'], quantidade_confirmada='2', valor_total='8.00')
        self.assertEqual(self.cliente.post('/notas/manuais', json=self.entrada(itens=[variado_item])).status_code, 422)
        self.criar(itens=[dict(variado_item, variacao_id=variacao['id'])])
        self.assertEqual(self.cliente.post('/notas/manuais',
            json=self.entrada(itens=[dict(variado_item, variacao_id=variacao['id'], produto_id=self.produto['id'])])).status_code, 422)

    def test_uuid_ajustes_tags_competencia_ignorar_sem_aprender_descricao(self):
        nota = self.criar()
        caminho = '/notas/' + nota['id']
        self.assertEqual(self.cliente.get(caminho).json()['id'], nota['id'])
        self.assertEqual(self.cliente.post(caminho + '/classificacoes-automaticas').json(), nota)
        item = nota['itens'][0]
        resposta = self.cliente.patch(caminho + '/itens/' + item['id'],
            json=dict(produto_id=self.produto['id'], quantidade_confirmada='2'))
        self.assertEqual(resposta.status_code, 200, resposta.text)
        self.assertEqual(resposta.json()['situacao'], 'importada')
        self.assertEqual(resposta.json()['importada_em'], nota['importada_em'])
        tag = self.cliente.post('/tags', json={'nome': 'Casa'}).json()
        self.assertEqual(self.cliente.put(caminho + '/itens/' + item['id'] + '/tags',
                                         json={'tag_ids': [tag['id']]}).status_code, 200)
        self.assertEqual(self.cliente.patch(caminho, json={'considerar_proximo_mes': True}).status_code, 200)
        self.assertEqual(self.cliente.get('/relatorios/mensal', params={'mes': '2026-11'}).json()['total_pago'], '12.34')
        ignorado = self.cliente.patch(caminho + '/itens/' + item['id'] + '/ignorado', json={'ignorado': True})
        self.assertEqual(ignorado.status_code, 200)
        self.assertEqual(self.cliente.get('/relatorios/mensal', params={'mes': '2026-11'}).json()['total_pago'], '0.00')
        self.assertEqual(self.cliente.patch(caminho + '/ignorada', json={'ignorada': True}).status_code, 200)
        with closing(sqlite3.connect(self.caminho)) as conexao:
            self.assertEqual(conexao.execute('SELECT COUNT(*) FROM associacoes_produto').fetchone()[0], 0)

    def test_edicao_manual_atualiza_cabecalho_totais_e_relatorios(self):
        nota = self.criar(itens=[
            dict(produto_id=self.produto['id'], quantidade_confirmada='1', valor_total='60.00'),
            dict(produto_id=self.produto['id'], quantidade_confirmada='1', valor_total='10.00'),
        ])
        produto = self.criar_produto(nome='Ração', unidade_medida='KG')
        item = nota['itens'][0]
        caminho = '/notas/' + nota['id']
        entrada = dict(produto_id=produto['id'], quantidade_confirmada='5', valor_total='75.00')
        resposta = self.cliente.patch(caminho + '/itens/' + item['id'], json=entrada)
        self.assertEqual(resposta.status_code, 200, resposta.text)
        atual = resposta.json()
        salvo = atual['itens'][0]
        self.assertEqual(salvo['descricao_original'], 'Ração')
        self.assertEqual(salvo['quantidade'], '5')
        self.assertEqual(salvo['unidade_original'], 'KG')
        self.assertEqual(salvo['valor_unitario'], '15.000000')
        self.assertEqual(salvo['valor_total'], '75.00')
        self.assertEqual(atual['valor_total'], '85.00')
        self.assertEqual(atual['valor_a_pagar'], '85.00')
        self.assertEqual(atual['importada_em'], nota['importada_em'])
        self.assertEqual(atual['situacao'], 'importada')
        self.assertEqual(self.cliente.get(caminho).json(), atual)
        mensal = self.cliente.get('/relatorios/mensal', params={'mes': '2026-10'}).json()
        self.assertEqual(mensal['total_pago'], '85.00')
        itens = self.cliente.get('/relatorios/mensal/itens', params={'mes': '2026-10'}).json()['itens']
        racao = next(i for i in itens if i['produto'] == 'Ração')
        self.assertEqual(racao['quantidade_comprada'], '5')
        self.assertEqual(racao['valor_pago'], '75.00')
        # Atualizar só a quantidade preserva o total e recalcula o preço unitário.
        entrada.pop('valor_total')
        entrada['quantidade_confirmada'] = '3'
        resposta = self.cliente.patch(caminho + '/itens/' + item['id'], json=entrada).json()
        self.assertEqual(resposta['itens'][0]['valor_unitario'], '25.000000')
        self.assertEqual(resposta['valor_a_pagar'], '85.00')
        entrada['valor_total'] = '0.00'
        resposta = self.cliente.patch(caminho + '/itens/' + item['id'], json=entrada).json()
        self.assertEqual(resposta['itens'][0]['valor_total'], '0.00')
        self.assertEqual(resposta['valor_a_pagar'], '10.00')

    def test_edicao_valor_invalido_preserva_item_e_totais(self):
        nota = self.criar()
        caminho = '/notas/' + nota['id']
        for valor in ('-1', '1.001', 'NaN', '10000000000000.00'):
            with self.subTest(valor=valor):
                resposta = self.cliente.patch(caminho + '/itens/' + nota['itens'][0]['id'],
                    json=dict(produto_id=self.produto['id'], quantidade_confirmada='2', valor_total=valor))
                self.assertEqual(resposta.status_code, 422, resposta.text)
                self.assertEqual(self.cliente.get(caminho).json(), nota)

    def test_valor_de_nota_fiscal_nao_pode_ser_alterado(self):
        nota = self.cliente.post('/leituras', json={'url': URL_TESTE}).json()['nota']
        caminho = '/notas/' + nota['chave']
        resposta = self.cliente.patch(caminho + '/itens/' + nota['itens'][0]['id'],
            json=dict(produto_id=self.produto['id'], quantidade_confirmada='2', valor_total='1.00'))
        self.assertEqual(resposta.status_code, 422, resposta.text)
        self.assertEqual(self.cliente.get(caminho).json(), nota)

    def test_criar_com_valor_unitario_calcula_total_e_preserva_preco(self):
        for quantidade, preco, total in [('5', '15.00', '75.00'), ('0.5', '0.29', '0.15'),
                                          ('3', '0.10', '0.30'), ('1', '0.00', '0.00')]:
            with self.subTest(quantidade=quantidade, preco=preco):
                nota = self.criar(itens=[dict(produto_id=self.produto['id'],
                    quantidade_confirmada=quantidade, valor_unitario=preco)])
                self.assertEqual(nota['valor_a_pagar'], total)
                self.assertEqual(nota['itens'][0]['valor_unitario'], preco)
                self.assertEqual(self.cliente.get('/notas/' + nota['id']).json(), nota)

    def test_editar_com_valor_unitario_recalcula_compra_e_relatorio(self):
        nota = self.criar()
        caminho = '/notas/' + nota['id']
        resposta = self.cliente.patch(caminho + '/itens/' + nota['itens'][0]['id'],
            json=dict(produto_id=self.produto['id'], quantidade_confirmada='0.5', valor_unitario='0.29'))
        self.assertEqual(resposta.status_code, 200, resposta.text)
        self.assertEqual(resposta.json()['itens'][0]['valor_unitario'], '0.29')
        self.assertEqual(resposta.json()['valor_a_pagar'], '0.15')
        mensal = self.cliente.get('/relatorios/mensal', params={'mes': '2026-10'}).json()
        self.assertEqual(mensal['total_pago'], '0.15')
        self.assertEqual(self.cliente.get(caminho).json(), resposta.json())

    def test_valor_unitario_invalido_ou_ambiguo_nao_grava(self):
        for campos in [dict(valor_unitario='-1'), dict(valor_unitario='NaN'), dict(valor_unitario='1.001'),
                       dict(valor_unitario='9999999999999.99', quantidade_confirmada='2'),
                       dict(valor_unitario='2.00', valor_total='3.00'), {}]:
            with self.subTest(campos=campos):
                item = dict(produto_id=self.produto['id'], quantidade_confirmada='1')
                item.update(campos)
                resposta = self.cliente.post('/notas/manuais', json=self.entrada(itens=[item]))
                self.assertEqual(resposta.status_code, 422, resposta.text)
                self.assertEqual(self.cliente.get('/notas').json(), [])
        nota = self.criar()
        for campos in [dict(valor_unitario='-1'), dict(valor_unitario='1.001'),
                       dict(valor_unitario='2', valor_total='3'),
                       dict(valor_unitario='9999999999999.99')]:
            with self.subTest(edicao=campos):
                resposta = self.cliente.patch('/notas/' + nota['id'] + '/itens/' + nota['itens'][0]['id'],
                    json=dict(produto_id=self.produto['id'], quantidade_confirmada='2', **campos))
                self.assertEqual(resposta.status_code, 422, resposta.text)
                self.assertEqual(self.cliente.get('/notas/' + nota['id']).json(), nota)

    def test_nota_fiscal_nao_aceita_edicao_de_valor_unitario(self):
        nota = self.cliente.post('/leituras', json={'url': URL_TESTE}).json()['nota']
        resposta = self.cliente.patch('/notas/' + nota['chave'] + '/itens/' + nota['itens'][0]['id'],
            json=dict(produto_id=self.produto['id'], quantidade_confirmada='2', valor_unitario='1.00'))
        self.assertEqual(resposta.status_code, 422, resposta.text)
        self.assertEqual(self.cliente.get('/notas/' + nota['chave']).json(), nota)

    def test_backup_preserva_compras_sem_dados_fiscais(self):
        nota = self.criar()
        backup = self.cliente.get("/banco/exportacao")
        self.assertEqual(backup.status_code, 200)
        self.criar()
        resposta = self.cliente.post("/banco/importacao",
            files={"arquivo": ("copia.sqlite3", backup.content, "application/vnd.sqlite3")})
        self.assertEqual(resposta.status_code, 200, resposta.text)
        self.assertEqual(len(self.cliente.get("/notas").json()), 1)
        self.assertEqual(self.cliente.get("/notas/" + nota["id"]).json(), nota)

    def test_migracao_preserva_registros_e_restricoes_unicas(self):
        caminho = Path(self.temp.name) / 'legado.sqlite3'
        BancoSQLite.migrar(caminho, '0005')
        with closing(sqlite3.connect(caminho)) as conexao:
            loja_id, nota_id = uuid4().hex, uuid4().hex
            conexao.execute('INSERT INTO estabelecimentos (id, cnpj, razao_social) VALUES (?, ?, ?)',
                            (loja_id, '12345678000100', 'Mercado'))
            conexao.execute('''INSERT INTO notas
                (id, chave, numero, serie, estabelecimento_id, emissao, quantidade_itens,
                 valor_total, desconto, valor_a_pagar, url_origem, situacao)
                VALUES (?, ?, '1', '1', ?, '2026-10-01 12:00:00', 0, '0', '0', '0', 'https://exemplo.com', 'lida')''',
                (nota_id, '1' * 44, loja_id))
            conexao.commit()
        BancoSQLite.migrar(caminho)
        with closing(sqlite3.connect(caminho)) as conexao:
            self.assertEqual(conexao.execute('SELECT origem, chave FROM notas').fetchone(), ('sefaz', '1' * 44))
            self.assertEqual(conexao.execute('PRAGMA foreign_key_check').fetchall(), [])
            with self.assertRaises(sqlite3.IntegrityError):
                conexao.execute('INSERT INTO estabelecimentos (id, cnpj, razao_social) VALUES (?, ?, ?)',
                                (uuid4().hex, '12345678000100', 'Duplicado'))
            with self.assertRaises(sqlite3.IntegrityError):
                colunas = 'chave numero serie estabelecimento_id emissao quantidade_itens valor_total desconto valor_a_pagar url_origem situacao considerar_proximo_mes importada_em ignorada origem'.split()
                lista = ','.join(colunas)
                conexao.execute(f'INSERT INTO notas (id,{lista}) SELECT ?,{lista} FROM notas',
                                (uuid4().hex,))


class NormalizacaoSchemaTests(unittest.TestCase):
    def test_ordem_das_restricoes_nao_altera_estrutura(self):
        from src.services.banco_service import BancoService
        inicio = "CREATE TABLE notas (id TEXT NOT NULL, loja TEXT, chave TEXT,"
        fim = "CHECK(chave IN ('a,b', 'c')), CHECK(id <> ''))"
        a = inicio + "PRIMARY KEY(id), UNIQUE(chave), FOREIGN KEY(loja) REFERENCES lojas(id)," + fim
        b = inicio + "FOREIGN KEY(loja) REFERENCES lojas(id), PRIMARY KEY(id), UNIQUE(chave)," + fim
        self.assertEqual(BancoService.normalizar_definicao(a), BancoService.normalizar_definicao(b))
        self.assertNotEqual(BancoService.normalizar_definicao(a),
                            BancoService.normalizar_definicao(b.replace("CHECK(id <> '')", "CHECK(id = '')")))
