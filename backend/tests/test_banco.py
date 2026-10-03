import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from threading import Event
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api.app import criar_app
from src.core.persistence.banco_sqlite import BancoSQLite
from tests.test_leitura import HTML, URL_TESTE


class BancoTests(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        self.pasta = Path(self.temporario.name)
        self.caminho = self.pasta / "atual.sqlite3"
        self.app = criar_app(self.caminho, lambda _: HTML.encode("utf-8"), permitir_importacao_banco=True)
        self.addCleanup(self.app.state.banco.fechar)
        self.cliente = TestClient(self.app)
        self.addCleanup(self.cliente.close)
        self.cliente.post("/categorias", json={"nome": "Anterior"})

    def novo_banco(self, revisao="head"):
        caminho = self.pasta / "recebido.sqlite3"
        BancoSQLite.migrar(caminho, revisao)
        with closing(sqlite3.connect(caminho)) as conexao:
            conexao.execute("INSERT INTO categorias(id, nome) VALUES (?, ?)", ("0" * 32, "Recebida"))
            conexao.commit()
        return caminho

    def importar(self, conteudo):
        return self.cliente.post("/banco/importacao", files={"arquivo": ("copia.sqlite3", conteudo, "application/vnd.sqlite3")})

    def categorias(self):
        return [c["nome"] for c in self.cliente.get("/categorias").json()]

    def assert_sem_temporarios(self):
        self.assertEqual(list(self.pasta.glob("transferencia-*")), [])

    def test_configuracao_e_bloqueio_antes_de_ler_upload(self):
        self.assertEqual(self.cliente.get("/banco/configuracao").json(), {"permitir_importacao": True})
        app = criar_app(self.pasta / "producao.sqlite3", permitir_importacao_banco=False)
        self.addCleanup(app.state.banco.fechar)
        with TestClient(app) as cliente:
            self.assertEqual(cliente.get("/banco/configuracao").json(), {"permitir_importacao": False})
            resposta = cliente.post("/banco/importacao", content=b"nem multipart")
            self.assertEqual(resposta.status_code, 403)
            self.assertEqual(resposta.json()["codigo"], "importacao_desabilitada")
            self.assertEqual(cliente.get("/banco/exportacao").status_code, 200)

    def test_exportacao_reimportacao_preserva_notas_tags_e_associacoes(self):
        leitura = self.cliente.post("/leituras", json={"url": URL_TESTE}).json()
        nota = leitura["nota"]
        tag = self.cliente.post("/tags", json={"nome": "Teste"}).json()
        self.cliente.put(f"/notas/{nota['chave']}/itens/{nota['itens'][0]['id']}/tags", json={"tag_ids": [tag["id"]]})
        categoria = self.cliente.get("/categorias").json()[0]
        marca = self.cliente.post("/marcas", json={"nome": "Marca teste"}).json()
        produto = self.cliente.post("/produtos", json={
            "nome": "Produto teste", "categoria_id": categoria["id"],
            "tratar_apenas_como_unidades": True,
        }).json()
        for item in nota["itens"]:
            revisao = self.cliente.patch(f"/notas/{nota['chave']}/itens/{item['id']}", json={
                "produto_id": produto["id"], "marca_id": marca["id"], "quantidade_confirmada": 1,
            })
            self.assertEqual(revisao.status_code, 200, revisao.text)
        self.assertEqual(self.cliente.post(f"/notas/{nota['chave']}/importacao").status_code, 200)
        antes = self.cliente.get(f"/notas/{nota['chave']}").json()
        with closing(sqlite3.connect(self.caminho)) as conexao:
            associacoes = conexao.execute("SELECT * FROM associacoes_produto ORDER BY id").fetchall()
        resposta = self.cliente.get("/banco/exportacao")
        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.content.startswith(b"SQLite format 3\x00"))
        self.assertIn(".sqlite3", resposta.headers["content-disposition"])
        self.assertEqual(resposta.headers["cache-control"], "no-store")
        self.assert_sem_temporarios()
        self.cliente.post("/categorias", json={"nome": "Depois"})
        importada = self.importar(resposta.content)
        self.assertEqual(importada.status_code, 200, importada.text)
        self.assertEqual(self.categorias(), ["Anterior"])
        self.assertEqual(self.cliente.get(f"/notas/{nota['chave']}").json(), antes)
        with closing(sqlite3.connect(self.caminho)) as conexao:
            self.assertEqual(conexao.execute("SELECT * FROM associacoes_produto ORDER BY id").fetchall(), associacoes)
        self.assertEqual(self.cliente.get("/marcas").json()[0]["id"], marca["id"])
        self.assertEqual(self.cliente.get("/produtos").json()[0]["id"], produto["id"])
        # Serviços e sessionmaker já existentes também gravam no novo arquivo.
        self.assertEqual(self.cliente.post("/categorias", json={"nome": "Nova"}).status_code, 201)
        self.assert_sem_temporarios()

    def test_substituicao_backup_e_ultima_copia(self):
        novo = self.novo_banco()
        resposta = self.importar(novo.read_bytes())
        self.assertEqual(resposta.status_code, 200, resposta.text)
        self.assertEqual(self.categorias(), ["Recebida"])
        backup = self.caminho.with_name(self.caminho.name + ".pre-importacao.bak")
        with closing(sqlite3.connect(backup)) as conexao:
            self.assertEqual(conexao.execute("SELECT nome FROM categorias").fetchall(), [("Anterior",)])
        self.assertEqual(self.importar(novo.read_bytes()).status_code, 200)
        with closing(sqlite3.connect(backup)) as conexao:
            self.assertEqual(conexao.execute("SELECT nome FROM categorias").fetchall(), [("Recebida",)])
        self.assert_sem_temporarios()

    def test_migra_revisoes_anteriores(self):
        for revisao in ("0001", "0002"):
            with self.subTest(revisao=revisao):
                caminho = self.pasta / "recebido.sqlite3"
                caminho.unlink(missing_ok=True)
                novo = self.novo_banco(revisao)
                resposta = self.importar(novo.read_bytes())
                self.assertEqual(resposta.status_code, 200, resposta.text)
                with closing(sqlite3.connect(self.caminho)) as conexao:
                    self.assertEqual(conexao.execute("SELECT version_num FROM alembic_version").fetchone(), ("0003",))
                    self.assertIn("considerar_proximo_mes", [r[1] for r in conexao.execute("PRAGMA table_info(notas)")])
                # O arquivo original fornecido não é migrado.
                with closing(sqlite3.connect(novo)) as conexao:
                    self.assertEqual(conexao.execute("SELECT version_num FROM alembic_version").fetchone(), (revisao,))

    def test_arquivo_vazio_invalido_corrompido(self):
        for conteudo in (b"", b"nao sqlite", b"SQLite format 3\x00" + b"x" * 100):
            with self.subTest(conteudo=conteudo[:16]):
                self.assertEqual(self.importar(conteudo).status_code, 422)
                self.assertEqual(self.categorias(), ["Anterior"])
                self.assert_sem_temporarios()

    def test_rejeita_schema_alterado_revisao_futura_e_sem_revisao(self):
        caminho = self.novo_banco()
        original = caminho.read_bytes()
        for sql in ("PRAGMA writable_schema=ON; UPDATE sqlite_master SET sql=replace(sql, 'NOCASE', 'BINARY') WHERE name='categorias'", "DROP TABLE tags", "UPDATE alembic_version SET version_num='9999'", "DROP TABLE alembic_version"):
            with self.subTest(sql=sql):
                caminho.write_bytes(original)
                with closing(sqlite3.connect(caminho)) as conexao:
                    conexao.executescript(sql)
                    conexao.commit()
                self.assertEqual(self.importar(caminho.read_bytes()).status_code, 422)
                self.assertEqual(self.categorias(), ["Anterior"])
                self.assert_sem_temporarios()

    def test_rejeita_chave_estrangeira_invalida(self):
        novo = self.novo_banco()
        with closing(sqlite3.connect(novo)) as conexao:
            conexao.execute("INSERT INTO itens_tags(item_id, tag_id) VALUES (?, ?)", ("0" * 32, "1" * 32))
            conexao.commit()
        self.assertEqual(self.importar(novo.read_bytes()).status_code, 422)
        self.assertEqual(self.categorias(), ["Anterior"])

    def test_limite_tamanho_sem_criar_arquivo_permanente(self):
        with patch("src.api.routers.banco.LIMITE_IMPORTACAO_BANCO", 10):
            resposta = self.importar(b"x" * 11)
        self.assertEqual(resposta.status_code, 413)
        self.assertEqual(resposta.json()["codigo"], "arquivo_muito_grande")
        with patch("src.services.banco_service.LIMITE_IMPORTACAO_BANCO", 10):
            self.assertEqual(self.importar(b"x" * 11).status_code, 413)
        self.assert_sem_temporarios()

    def test_limite_corpo_durante_recebimento(self):
        with patch("src.api.middleware_banco.LIMITE_IMPORTACAO_BANCO", 0):
            resposta = self.importar(b"x" * (1024 * 1024 + 1))
        self.assertEqual(resposta.status_code, 413, resposta.text)
        self.assertEqual(resposta.json()["codigo"], "arquivo_muito_grande")
        self.assert_sem_temporarios()

    def test_rollback_apos_falha_na_reabertura(self):
        novo = self.novo_banco()
        servico = self.app.state.banco_service
        original = servico.verificar_abertura
        chamadas = 0

        def falhar_uma_vez():
            nonlocal chamadas
            chamadas += 1
            if chamadas == 1:
                raise RuntimeError("Falha simulada")
            original()

        with patch.object(servico, "verificar_abertura", side_effect=falhar_uma_vez):
            resposta = self.importar(novo.read_bytes())
        self.assertEqual(resposta.status_code, 500, resposta.text)
        self.assertEqual(self.categorias(), ["Anterior"])
        self.assert_sem_temporarios()

    def test_falha_backup_nao_substitui(self):
        novo = self.novo_banco()
        with patch.object(self.app.state.banco_service, "copiar_banco", side_effect=OSError("disco cheio")):
            self.assertEqual(self.importar(novo.read_bytes()).status_code, 500)
        self.assertEqual(self.categorias(), ["Anterior"])
        self.assert_sem_temporarios()

    def test_exportacao_com_wal(self):
        with closing(sqlite3.connect(self.caminho)) as conexao:
            conexao.execute("PRAGMA journal_mode=WAL")
            conexao.execute("INSERT INTO categorias(id,nome) VALUES (?,?)", ("2" * 32, "WAL"))
            conexao.commit()
            resposta = self.cliente.get("/banco/exportacao")
        exportado = self.pasta / "exportado.sqlite3"
        exportado.write_bytes(resposta.content)
        with closing(sqlite3.connect(exportado)) as conexao:
            self.assertEqual(conexao.execute("SELECT nome FROM categorias ORDER BY nome").fetchall(), [("Anterior",), ("WAL",)])
        self.assert_sem_temporarios()

    def test_aguarda_leitura_sefaz_e_bloqueia_novas_operacoes(self):
        novo = self.novo_banco()
        consultando = Event()
        liberar = Event()
        coordenacao = self.app.state.coordenacao_banco

        def consulta(_):
            consultando.set()
            if not liberar.wait(10):
                raise RuntimeError("Tempo de teste esgotado")
            return HTML.encode("utf-8")

        self.app.state.leitura_nota_service.consultar = consulta
        with ThreadPoolExecutor(max_workers=2) as pool:
            leitura = pool.submit(self.cliente.post, "/leituras", json={"url": URL_TESTE})
            try:
                self.assertTrue(consultando.wait(5))
                importacao = pool.submit(self.importar, novo.read_bytes())
                with coordenacao._condicao:
                    self.assertTrue(coordenacao._condicao.wait_for(lambda: coordenacao._substituindo, timeout=5))
                self.assertFalse(importacao.done())
                self.assertEqual(self.cliente.get("/categorias").status_code, 503)
                self.assertEqual(self.cliente.get("/banco/exportacao").status_code, 503)
                self.assertEqual(self.importar(b"outro banco").status_code, 409)
                self.assertEqual(self.cliente.get("/health").status_code, 200)
            finally:
                liberar.set()
            self.assertEqual(leitura.result(timeout=10).status_code, 200)
            resposta = importacao.result(timeout=10)
            self.assertEqual(resposta.status_code, 200, resposta.text)
        self.assertEqual(self.categorias(), ["Recebida"])
        backup = self.caminho.with_name(self.caminho.name + ".pre-importacao.bak")
        with closing(sqlite3.connect(backup)) as conexao:
            self.assertEqual(conexao.execute("SELECT COUNT(*) FROM notas").fetchone(), (1,))
        self.assert_sem_temporarios()

    def test_falha_na_restauracao_bloqueia_acesso_e_preserva_backup(self):
        novo = self.novo_banco()
        with patch.object(self.app.state.banco_service, "verificar_abertura", side_effect=RuntimeError("falha persistente")):
            resposta = self.importar(novo.read_bytes())
        self.assertEqual(resposta.status_code, 500)
        self.assertIn("acesso ao banco foi bloqueado", resposta.json()["mensagem"])
        self.assertEqual(self.cliente.get("/categorias").status_code, 503)
        self.assertEqual(self.cliente.get("/health").status_code, 503)
        self.assertEqual(self.importar(novo.read_bytes()).status_code, 503)
        backup = self.caminho.with_name(self.caminho.name + ".pre-importacao.bak")
        with closing(sqlite3.connect(backup)) as conexao:
            self.assertEqual(conexao.execute("SELECT nome FROM categorias").fetchall(), [("Anterior",)])
        self.assert_sem_temporarios()

    def test_timeout_libera_banco_sem_substituir(self):
        novo = self.novo_banco()
        with patch.object(self.app.state.coordenacao_banco._condicao, "wait_for", return_value=False):
            resposta = self.importar(novo.read_bytes())
        self.assertEqual(resposta.status_code, 503)
        self.assertEqual(self.categorias(), ["Anterior"])
        self.assertEqual(self.importar(novo.read_bytes()).status_code, 200)
        self.assert_sem_temporarios()

    def test_falha_migration_preserva_banco_atual(self):
        novo = self.novo_banco("0001")
        original = BancoSQLite.migrar
        chamadas = 0

        def migrar(caminho, revisao="head"):
            nonlocal chamadas
            chamadas += 1
            if chamadas == 2:
                raise RuntimeError("Falha na migration do banco recebido")
            original(caminho, revisao)

        with patch.object(BancoSQLite, "migrar", side_effect=migrar):
            resposta = self.importar(novo.read_bytes())
        self.assertEqual(chamadas, 2)
        self.assertEqual(resposta.status_code, 422)
        self.assertEqual(self.categorias(), ["Anterior"])
        self.assert_sem_temporarios()
