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


def url_da_chave(chave: str) -> str:
    return f"https://dfe-portal.svrs.rs.gov.br/Dfe/QrCodeNFce?p={chave}|3|1"


def html_com_chave(chave: str) -> str:
    chave_formatada = " ".join(chave[indice : indice + 4] for indice in range(0, 44, 4))
    original = " ".join(CHAVE[indice : indice + 4] for indice in range(0, 44, 4))
    return HTML.replace(original, chave_formatada)


class CatalogoRevisaoApiTests(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        caminho = Path(self.temporario.name) / "notas.sqlite3"
        self.app = criar_app(caminho, lambda _: HTML.encode("utf-8"))
        self.cliente = TestClient(self.app)
        self.addCleanup(self.cliente.close)

    def criar_catalogo(self):
        categoria = self.cliente.post(
            "/categorias", json={"nome": "  Alimentação  "}
        )
        self.assertEqual(categoria.status_code, 201)
        marca = self.cliente.post("/marcas", json={"nome": "Rodeio"})
        self.assertEqual(marca.status_code, 201)
        pao = self.cliente.post(
            "/produtos",
            json={
                "nome": "Pão",
                "categoria_id": categoria.json()["id"],
                "unidade_base": "KG",
                "nao_solicitar_marca": True,
            },
        )
        queijo = self.cliente.post(
            "/produtos",
            json={
                "nome": "Queijo muçarela",
                "categoria_id": categoria.json()["id"],
                "unidade_base": "KG",
                "nao_solicitar_marca": False,
            },
        )
        self.assertEqual(pao.status_code, 201)
        self.assertEqual(queijo.status_code, 201)
        return categoria.json(), marca.json(), pao.json(), queijo.json()

    def ler_nota(self):
        resposta = self.cliente.post("/leituras", json={"url": URL_TESTE})
        self.assertEqual(resposta.status_code, 200)
        return resposta.json()["nota"]

    def revisar(
        self,
        item_id: str,
        produto_id: str,
        quantidade_normalizada: str,
        marca_id: str | None = None,
        unidade_corrigida: str = "UN",
    ):
        return self.cliente.patch(
            f"/notas/{CHAVE}/itens/{item_id}",
            json={
                "produto_id": produto_id,
                "marca_id": marca_id,
                "unidade_corrigida": unidade_corrigida,
                "quantidade_normalizada": quantidade_normalizada,
            },
        )

    def test_crud_dos_catalogos_e_busca(self):
        categoria, marca, pao, _ = self.criar_catalogo()
        self.assertEqual(categoria["nome"], "Alimentação")
        self.assertEqual(
            [item["id"] for item in self.cliente.get("/categorias?busca=menta").json()],
            [categoria["id"]],
        )
        self.assertEqual(
            [item["id"] for item in self.cliente.get("/produtos?busca=pão").json()],
            [pao["id"]],
        )
        self.assertTrue(pao["nao_solicitar_marca"])
        alterada = self.cliente.patch(
            f"/marcas/{marca['id']}", json={"nome": "Rodeio Alimentos"}
        )
        self.assertEqual(alterada.status_code, 200)
        self.assertEqual(
            self.cliente.get(f"/marcas/{marca['id']}").json()["nome"],
            "Rodeio Alimentos",
        )
        produto = self.cliente.patch(
            f"/produtos/{pao['id']}",
            json={
                "nome": "Pão francês",
                "categoria_id": categoria["id"],
                "unidade_base": "KG",
                "nao_solicitar_marca": True,
            },
        )
        self.assertEqual(produto.status_code, 200)
        temporaria = self.cliente.post("/marcas", json={"nome": "Temporária"}).json()
        self.assertEqual(self.cliente.delete(f"/marcas/{temporaria['id']}").status_code, 204)
        self.assertEqual(self.cliente.get(f"/marcas/{temporaria['id']}").status_code, 404)
        self.assertEqual(self.cliente.delete(f"/categorias/{categoria['id']}").status_code, 409)

    def test_importacao_exige_todos_os_itens_e_depois_e_imutavel(self):
        nota = self.ler_nota()
        categoria, marca, pao, queijo = self.criar_catalogo()

        primeira = self.revisar(
            nota["itens"][0]["id"], pao["id"], "0.15", unidade_corrigida="KG"
        )
        self.assertEqual(primeira.status_code, 200)
        self.assertEqual(primeira.json()["situacao"], "em_revisao")
        bloqueada = self.cliente.post(f"/notas/{CHAVE}/importacao")
        self.assertEqual(bloqueada.status_code, 409)
        self.assertIn("1 item", bloqueada.json()["mensagem"])

        segunda = self.revisar(
            nota["itens"][1]["id"],
            queijo["id"],
            "0.600",
            marca["id"],
        )
        self.assertEqual(segunda.status_code, 200)
        importada = self.cliente.post(f"/notas/{CHAVE}/importacao")
        self.assertEqual(importada.status_code, 200)
        self.assertEqual(importada.json()["situacao"], "importada")
        self.assertIsNotNone(importada.json()["importada_em"])

        repetida = self.cliente.post(f"/notas/{CHAVE}/importacao")
        self.assertEqual(repetida.json()["importada_em"], importada.json()["importada_em"])
        self.assertEqual(
            self.revisar(
                nota["itens"][0]["id"], pao["id"], "0.15", unidade_corrigida="KG"
            ).status_code,
            409,
        )
        self.assertEqual(
            self.cliente.patch(
                f"/categorias/{categoria['id']}", json={"nome": "Comida"}
            ).status_code,
            409,
        )

    def test_marca_e_obrigatoria_conforme_configuracao_do_produto(self):
        nota = self.ler_nota()
        _, marca, pao, queijo = self.criar_catalogo()

        sem_marca_permitida = self.revisar(
            nota["itens"][0]["id"], pao["id"], "0.15", unidade_corrigida="KG"
        )
        self.assertEqual(sem_marca_permitida.status_code, 200)
        apresentacao = sem_marca_permitida.json()["itens"][0]["apresentacao"]
        self.assertIsNone(apresentacao["marca"])
        self.assertNotIn("marca_confirmada", apresentacao)
        self.assertNotIn("conteudo_embalagem", apresentacao)
        self.assertNotIn("unidade_embalagem", apresentacao)

        marca_obrigatoria = self.revisar(
            nota["itens"][1]["id"], queijo["id"], "0.600"
        )
        self.assertEqual(marca_obrigatoria.status_code, 422)
        self.assertIn("marca é obrigatória", marca_obrigatoria.json()["mensagem"])

        com_marca = self.revisar(
            nota["itens"][1]["id"], queijo["id"], "0.600", marca["id"]
        )
        self.assertEqual(com_marca.status_code, 200)

    def test_classificacao_automatica_por_codigo_e_por_descricao(self):
        nota = self.ler_nota()
        _, _, pao, _ = self.criar_catalogo()
        resposta = self.revisar(
            nota["itens"][0]["id"], pao["id"], "0.15", unidade_corrigida="KG"
        )
        self.assertEqual(resposta.status_code, 200)

        chave_mesma_loja = "43260807718633007868650080002005971056148317"
        html_codigo = (
            html_com_chave(chave_mesma_loja)
            .replace("PAO kg", "OUTRO NOME")
            .replace("<strong>Qtde.:</strong>0,15", "<strong>Qtde.:</strong>0,30")
            .replace('<span class="valor">10,48', '<span class="valor">20,97')
            .replace("<span>38,28</span>", "<span>48,77</span>")
            .replace("<span>35,68</span>", "<span>46,17</span>")
        )
        self.app.state.servico_leitura_notas.consultar = lambda _: html_codigo.encode("utf-8")
        classificada_codigo = self.cliente.post(
            "/leituras", json={"url": url_da_chave(chave_mesma_loja)}
        ).json()["nota"]
        self.assertTrue(classificada_codigo["itens"][0]["revisado"])
        self.assertEqual(
            classificada_codigo["itens"][0]["apresentacao"]["produto"]["id"], pao["id"]
        )
        self.assertEqual(classificada_codigo["itens"][0]["quantidade_normalizada"], "0.3")
        self.assertFalse(classificada_codigo["itens"][1]["revisado"])

        chave_outro_local = "43260707718633007868650080002005971056148317"
        html_nome = (
            html_com_chave(chave_outro_local)
            .replace("00.000.000/0001-00", "11.111.111/0001-11")
            .replace("(Código: 10)", "(Código: 99)")
            .replace("PAO kg", "  pao   KG ")
        )
        self.app.state.servico_leitura_notas.consultar = lambda _: html_nome.encode("utf-8")
        classificada_nome = self.cliente.post(
            "/leituras", json={"url": url_da_chave(chave_outro_local)}
        ).json()["nota"]
        self.assertTrue(classificada_nome["itens"][0]["revisado"])
        self.assertEqual(
            classificada_nome["itens"][0]["apresentacao"]["produto"]["id"], pao["id"]
        )


class MigracaoTests(unittest.TestCase):
    def test_migracao_preserva_dados_da_estrutura_1(self):
        with tempfile.TemporaryDirectory() as temporario:
            caminho = Path(temporario) / "v1.sqlite3"
            with closing(sqlite3.connect(caminho)) as conexao:
                conexao.executescript(
                    """
                    CREATE TABLE estabelecimentos (id TEXT PRIMARY KEY);
                    CREATE TABLE categorias (id TEXT PRIMARY KEY, nome TEXT NOT NULL);
                    CREATE TABLE marcas (id TEXT PRIMARY KEY, nome TEXT NOT NULL);
                    CREATE TABLE produtos (
                        id TEXT PRIMARY KEY, nome TEXT NOT NULL,
                        categoria_id TEXT NOT NULL, unidade_base TEXT NOT NULL
                    );
                    CREATE TABLE apresentacoes_produto (
                        id TEXT PRIMARY KEY, produto_id TEXT NOT NULL, marca_id TEXT,
                        conteudo_embalagem TEXT, unidade_embalagem TEXT,
                        marca_confirmada INTEGER NOT NULL
                    );
                    CREATE TABLE notas (
                        id TEXT PRIMARY KEY, chave TEXT NOT NULL, situacao TEXT NOT NULL
                    );
                    INSERT INTO notas VALUES ('nota-1', 'chave-existente', 'lida');
                    INSERT INTO categorias VALUES ('categoria-1', 'Alimentação');
                    INSERT INTO produtos VALUES ('produto-1', 'Pão', 'categoria-1', 'KG');
                    INSERT INTO apresentacoes_produto
                    VALUES ('apresentacao-1', 'produto-1', NULL, NULL, NULL, 1);
                    PRAGMA user_version = 1;
                    """
                )
                conexao.commit()
            BancoSQLite(caminho).inicializar()
            with closing(sqlite3.connect(caminho)) as conexao:
                self.assertEqual(conexao.execute("PRAGMA user_version").fetchone()[0], 3)
                self.assertEqual(
                    conexao.execute("SELECT chave FROM notas").fetchone()[0],
                    "chave-existente",
                )
                colunas = [linha[1] for linha in conexao.execute("PRAGMA table_info(notas)")]
                self.assertIn("importada_em", colunas)
                self.assertIsNotNone(
                    conexao.execute(
                        "SELECT name FROM sqlite_master WHERE name = 'associacoes_produto'"
                    ).fetchone()
                )
                produto = conexao.execute(
                    "SELECT nao_solicitar_marca FROM produtos WHERE id = 'produto-1'"
                ).fetchone()
                self.assertEqual(produto[0], 1)
                colunas_apresentacao = [
                    linha[1]
                    for linha in conexao.execute("PRAGMA table_info(apresentacoes_produto)")
                ]
                self.assertEqual(colunas_apresentacao, ["id", "produto_id", "marca_id"])


if __name__ == "__main__":
    unittest.main()
