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
    def test_migracao_inicial_cria_schema_e_pode_ser_reexecutada(self):
        with tempfile.TemporaryDirectory() as temporario:
            caminho = Path(temporario) / "novo.sqlite3"
            banco = BancoSQLite(caminho)
            banco.inicializar()
            with closing(sqlite3.connect(caminho)) as conexao:
                self.assertEqual(
                    conexao.execute("SELECT version_num FROM alembic_version").fetchone(),
                    ("0001",),
                )
                tabelas = {
                    linha[0]
                    for linha in conexao.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table'"
                    )
                }
                self.assertTrue({"notas", "itens", "categorias"}.issubset(tabelas))


if __name__ == "__main__":
    unittest.main()
