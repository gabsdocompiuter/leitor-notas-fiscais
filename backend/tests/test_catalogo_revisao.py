import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from fastapi.testclient import TestClient

from src.api.app import criar_app
from src.persistence.banco_sqlite import BancoSQLite
from tests.test_leitura import HTML, URL_TESTE

CHAVE = "43260907718633007868650080002005971056148317"


class CatalogoRevisaoApiTests(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        self.app = criar_app(
            Path(self.temporario.name) / "notas.sqlite3",
            lambda _: HTML.encode("utf-8"),
        )
        self.cliente = TestClient(self.app)
        self.addCleanup(self.cliente.close)
        self.categoria = self.cliente.post(
            "/categorias", json={"nome": "Alimentação"}
        ).json()
        self.marca = self.cliente.post("/marcas", json={"nome": "Rodeio"}).json()

    def produto(self, nome="Produto", **opcoes):
        dados = {
            "nome": nome,
            "categoria_id": self.categoria["id"],
            "nao_solicitar_marca": False,
            "tratar_apenas_como_unidades": False,
            "contem_variacoes": False,
            "unidade_medida": "KG",
        }
        dados.update(opcoes)
        resposta = self.cliente.post("/produtos", json=dados)
        self.assertEqual(resposta.status_code, 201, resposta.text)
        return resposta.json()

    def ler(self):
        return self.cliente.post("/leituras", json={"url": URL_TESTE}).json()["nota"]

    def revisar(self, item, produto, quantidade, marca=True, variacao_id=None):
        return self.cliente.patch(
            f"/notas/{CHAVE}/itens/{item['id']}",
            json={
                "produto_id": produto["id"],
                "marca_id": self.marca["id"] if marca else None,
                "variacao_id": variacao_id,
                "quantidade_confirmada": quantidade,
            },
        )

    def test_catalogos_possuem_busca_inclusao_edicao_sem_exclusao(self):
        produto = self.produto("Pão", nao_solicitar_marca=True)
        self.assertEqual(
            self.cliente.get("/produtos", params={"busca": "pão"}).json()[0]["id"],
            produto["id"],
        )
        alterada = self.cliente.patch(
            f"/marcas/{self.marca['id']}", json={"nome": "Rodeio Alimentos"}
        )
        self.assertEqual(alterada.status_code, 200)
        self.assertEqual(self.cliente.delete(f"/marcas/{self.marca['id']}").status_code, 405)
        unidades = self.cliente.get("/unidades-medida").json()
        self.assertEqual([item["codigo"] for item in unidades], ["KG", "G", "L", "ML"])

    def test_quantidade_inteira_para_unidades_e_variacoes(self):
        nota = self.ler()
        unidade = self.produto(
            "Ovos", tratar_apenas_como_unidades=True, unidade_medida=None
        )
        self.assertEqual(self.revisar(nota["itens"][0], unidade, "1.5").status_code, 422)
        self.assertEqual(self.revisar(nota["itens"][0], unidade, 2).status_code, 200)

        variado = self.produto("Requeijão", contem_variacoes=True, unidade_medida="G")
        peso = self.cliente.post(
            f"/produtos/{variado['id']}/variacoes",
            json={"quantidade": "180", "unidade_medida": "G", "descricao": None},
        )
        volume = self.cliente.post(
            f"/produtos/{variado['id']}/variacoes",
            json={"quantidade": "200", "unidade_medida": "ML", "descricao": "Copo 200 ml"},
        )
        self.assertEqual(peso.status_code, 201)
        self.assertEqual(volume.status_code, 201)
        sem_variacao = self.revisar(nota["itens"][1], variado, 1)
        self.assertEqual(sem_variacao.status_code, 422)
        revisada = self.revisar(
            nota["itens"][1], variado, 1, variacao_id=peso.json()["id"]
        )
        self.assertEqual(revisada.status_code, 200)
        self.assertEqual(revisada.json()["itens"][1]["variacao"]["nome_exibicao"], "180 G")

    def test_importacao_exige_revisao_de_todos_os_itens(self):
        nota = self.ler()
        produto = self.produto("Alimento", nao_solicitar_marca=True)
        self.assertEqual(
            self.revisar(nota["itens"][0], produto, "0.15", marca=False).status_code,
            200,
        )
        self.assertEqual(self.cliente.post(f"/notas/{CHAVE}/importacao").status_code, 409)
        self.assertEqual(
            self.revisar(nota["itens"][1], produto, "0.6", marca=False).status_code,
            200,
        )
        importada = self.cliente.post(f"/notas/{CHAVE}/importacao")
        self.assertEqual(importada.status_code, 200)
        self.assertEqual(importada.json()["situacao"], "importada")

    def test_estabelecimento_altera_apenas_apelido(self):
        loja = self.ler()["estabelecimento"]
        consultada = self.cliente.get(f"/estabelecimentos/{loja['id']}")
        self.assertEqual(consultada.status_code, 200)
        self.assertEqual(consultada.json()["id"], loja["id"])
        alterada = self.cliente.patch(
            f"/estabelecimentos/{loja['id']}", json={"apelido": "Mercado perto"}
        )
        self.assertEqual(alterada.status_code, 200)
        self.assertEqual(alterada.json()["nome_exibicao"], "Mercado perto")
        self.assertEqual(alterada.json()["razao_social"], loja["razao_social"])

        ausente = self.cliente.get(
            "/estabelecimentos/00000000-0000-0000-0000-000000000000"
        )
        self.assertEqual(ausente.status_code, 404)


class MigracaoTests(unittest.TestCase):
    def test_migracao_preserva_apenas_notas_lidas_e_catalogos(self):
        with tempfile.TemporaryDirectory() as temporario:
            caminho = Path(temporario) / "v3.sqlite3"
            with closing(sqlite3.connect(caminho)) as conexao:
                conexao.executescript(
                    """
                    CREATE TABLE estabelecimentos (id TEXT PRIMARY KEY, cnpj TEXT, razao_social TEXT, apelido TEXT);
                    CREATE TABLE categorias (id TEXT PRIMARY KEY, nome TEXT);
                    CREATE TABLE marcas (id TEXT PRIMARY KEY, nome TEXT);
                    CREATE TABLE produtos (id TEXT PRIMARY KEY, nome TEXT, categoria_id TEXT, unidade_base TEXT, nao_solicitar_marca INTEGER);
                    CREATE TABLE apresentacoes_produto (id TEXT PRIMARY KEY, produto_id TEXT, marca_id TEXT);
                    CREATE TABLE notas (id TEXT PRIMARY KEY, chave TEXT, numero TEXT, serie TEXT, estabelecimento_id TEXT, emissao TEXT, quantidade_itens INTEGER, valor_total TEXT, desconto TEXT, valor_a_pagar TEXT, url_origem TEXT, situacao TEXT, importada_em TEXT);
                    CREATE TABLE itens (id TEXT PRIMARY KEY, nota_id TEXT, numero INTEGER, codigo TEXT, descricao_original TEXT, quantidade TEXT, unidade_original TEXT, valor_unitario TEXT, valor_total TEXT, alertas TEXT, apresentacao_id TEXT, unidade_corrigida TEXT, quantidade_normalizada TEXT, revisado INTEGER);
                    CREATE TABLE leituras (id TEXT PRIMARY KEY, chave TEXT, url TEXT, nota_id TEXT, erro_consulta TEXT, criada_em TEXT);
                    CREATE TABLE associacoes_produto (id TEXT PRIMARY KEY, estabelecimento_id TEXT, codigo_item TEXT, descricao_original TEXT, descricao_normalizada TEXT, apresentacao_id TEXT, unidade_corrigida TEXT, fator_normalizacao TEXT, UNIQUE(estabelecimento_id, codigo_item));
                    INSERT INTO estabelecimentos VALUES ('e', '1', 'Loja', NULL);
                    INSERT INTO categorias VALUES ('c', 'Alimentação');
                    INSERT INTO produtos VALUES ('p-un', 'Ovos', 'c', 'UN', 1);
                    INSERT INTO produtos VALUES ('p-kg', 'Arroz', 'c', 'KG', 0);
                    INSERT INTO notas VALUES ('n1', 'lida', '1', '1', 'e', '2026-01-01', 1, '1', '0', '1', 'url', 'lida', NULL);
                    INSERT INTO notas VALUES ('n2', 'revisao', '2', '1', 'e', '2026-01-01', 1, '1', '0', '1', 'url', 'em_revisao', NULL);
                    INSERT INTO notas VALUES ('n3', 'importada', '3', '1', 'e', '2026-01-01', 1, '1', '0', '1', 'url', 'importada', '2026-01-02');
                    INSERT INTO itens VALUES ('i1', 'n1', 1, '1', 'Item', '1', 'UN', '1', '1', '[]', NULL, NULL, NULL, 0);
                    INSERT INTO itens VALUES ('i2', 'n2', 1, '1', 'Item', '1', 'UN', '1', '1', '[]', NULL, NULL, NULL, 0);
                    INSERT INTO itens VALUES ('i3', 'n3', 1, '1', 'Item', '1', 'UN', '1', '1', '[]', NULL, NULL, NULL, 0);
                    INSERT INTO leituras VALUES ('l1', 'lida', 'url', 'n1', NULL, '2026-01-01');
                    INSERT INTO leituras VALUES ('l2', 'revisao', 'url', 'n2', NULL, '2026-01-01');
                    INSERT INTO leituras VALUES ('l3', 'importada', 'url', 'n3', NULL, '2026-01-01');
                    PRAGMA user_version = 3;
                    """
                )
            BancoSQLite(caminho).inicializar()
            with closing(sqlite3.connect(caminho)) as conexao:
                self.assertEqual(conexao.execute("PRAGMA user_version").fetchone()[0], 4)
                self.assertEqual(conexao.execute("SELECT chave FROM notas").fetchall(), [("lida",)])
                self.assertEqual(conexao.execute("SELECT nota_id FROM leituras").fetchall(), [("n1",)])
                self.assertEqual(conexao.execute("SELECT revisado, quantidade_confirmada FROM itens").fetchone(), (0, None))
                produtos = conexao.execute("SELECT id, tratar_apenas_como_unidades, unidade_medida FROM produtos ORDER BY id").fetchall()
                self.assertEqual(produtos, [("p-kg", 0, "KG"), ("p-un", 1, None)])


if __name__ == "__main__":
    unittest.main()
