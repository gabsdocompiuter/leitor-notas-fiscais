import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from src.api.app import criar_app
from src.core.persistence.banco_sqlite import BancoSQLite
from src.services.leitura_service import LeituraService
from tests.test_leitura import HTML, URL_TESTE

CHAVE = "43260907718633007868650080002005971056148317"


class IgnorarNotasItensTests(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        self.caminho = Path(self.temporario.name) / "notas.sqlite3"
        self.app = criar_app(self.caminho, lambda _: HTML.encode("utf-8"))
        self.addCleanup(self.app.state.banco.engine.dispose)
        self.cliente = TestClient(self.app)
        self.addCleanup(self.cliente.close)
        self.nota = self.cliente.post("/leituras", json={"url": URL_TESTE}).json()["nota"]
        self.categoria = self.cliente.post("/categorias", json={"nome": "Compras"}).json()
        self.produto = self.cliente.post("/produtos", json={
            "nome": "Produto", "categoria_id": self.categoria["id"],
            "nao_solicitar_marca": True, "tratar_apenas_como_unidades": False,
            "contem_variacoes": False, "unidade_medida": "KG",
        }).json()

    def ignorar_item(self, indice, ignorado=True):
        return self.cliente.patch(
            f"/notas/{CHAVE}/itens/{self.nota['itens'][indice]['id']}/ignorado",
            json={"ignorado": ignorado},
        )

    def ignorar_nota(self, ignorada=True):
        return self.cliente.patch(f"/notas/{CHAVE}/ignorada", json={"ignorada": ignorada})

    def revisar(self, indice):
        resposta = self.cliente.patch(f"/notas/{CHAVE}/itens/{self.nota['itens'][indice]['id']}", json={
            "produto_id": self.produto["id"], "quantidade_confirmada": "1",
        })
        self.assertEqual(resposta.status_code, 200, resposta.text)

    def importar(self):
        resposta = self.cliente.post(f"/notas/{CHAVE}/importacao")
        self.assertEqual(resposta.status_code, 200, resposta.text)
        return resposta.json()

    def relatorio(self, mes="2026-09"):
        resposta = self.cliente.get("/relatorios/mensal", params={"mes": mes})
        self.assertEqual(resposta.status_code, 200, resposta.text)
        return resposta.json()

    def detalhes(self, recurso="itens", **params):
        resposta = self.cliente.get(f"/relatorios/mensal/{recurso}", params={"mes": "2026-09", **params})
        self.assertEqual(resposta.status_code, 200, resposta.text)
        return resposta.json()

    def test_importacao_dispensa_ignorado_e_restauracao_exige_revisao(self):
        self.assertFalse(self.nota["ignorada"])
        self.assertTrue(all(not item["ignorado"] for item in self.nota["itens"]))
        self.assertEqual(self.ignorar_item(1).status_code, 200)
        self.revisar(0)
        importada = self.importar()
        self.assertFalse(importada["itens"][1]["revisado"])
        self.assertEqual(self.relatorio()["quantidade_itens"], 1)
        self.assertEqual(self.ignorar_item(1, False).status_code, 409)
        self.assertEqual(self.relatorio()["quantidade_itens"], 1)
        self.revisar(1)
        self.assertTrue(self.cliente.get(f"/notas/{CHAVE}").json()["itens"][1]["ignorado"])
        restaurada = self.ignorar_item(1, False)
        self.assertEqual(restaurada.status_code, 200, restaurada.text)
        self.assertEqual(restaurada.json()["importada_em"], importada["importada_em"])
        self.assertEqual(self.relatorio()["quantidade_itens"], 2)

    def test_todos_ignorados_bloqueiam_importacao_mesmo_revisados(self):
        for indice in range(2):
            self.revisar(indice)
            self.assertEqual(self.ignorar_item(indice).status_code, 200)
        resposta = self.cliente.post(f"/notas/{CHAVE}/importacao")
        self.assertEqual(resposta.status_code, 409)
        self.assertIn("pelo menos um item", resposta.json()["mensagem"])
        self.assertIsNone(self.cliente.get(f"/notas/{CHAVE}").json()["importada_em"])
        self.ignorar_item(0, False)
        self.importar()

    def test_relatorios_excluem_item_sem_transferir_desconto(self):
        tag = self.cliente.post("/tags", json={"nome": "Casa"}).json()
        self.cliente.post(f"/notas/{CHAVE}/itens/tags", json={"tag_ids": [tag["id"]]})
        for indice in range(2):
            self.revisar(indice)
        self.importar()
        original = self.detalhes()["itens"]
        mantido = original[1]
        self.ignorar_item(0)
        resumo = self.relatorio()
        self.assertEqual(resumo["total_pago"], mantido["valor_pago"])
        self.assertEqual(resumo["total_desconto"], mantido["desconto_rateado"])
        self.assertEqual(resumo["quantidade_notas"], 1)
        self.assertEqual(resumo["quantidade_itens"], 1)
        self.assertEqual(resumo["quantidades_compradas"], [{"quantidade": "1", "unidade": "KG"}])
        self.assertEqual(resumo["categorias"][0]["total_pago"], mantido["valor_pago"])
        self.assertEqual(resumo["tags"][0]["total_pago"], mantido["valor_pago"])
        self.assertEqual(self.detalhes(limite=1)["itens"], [mantido])
        produtos = self.detalhes("produtos", categoria_id=self.categoria["id"])
        self.assertEqual(produtos[0]["total_pago"], mantido["valor_pago"])
        for agrupador in ("marca", "variacao", "estabelecimento"):
            grupos = self.detalhes("agrupamentos", categoria_id=self.categoria["id"],
                                   produto_id=self.produto["id"], agrupador=agrupador)
            self.assertEqual(grupos[0]["quantidade_registros"], 1)
            self.assertEqual(grupos[0]["total_pago"], mantido["valor_pago"])
        self.assertEqual(self.relatorio("2026-10")["total_mes_anterior"], mantido["valor_pago"])
        self.cliente.patch(f"/notas/{CHAVE}", json={"considerar_proximo_mes": True})
        self.assertEqual(self.relatorio()["total_pago"], "0.00")
        self.assertEqual(self.relatorio("2026-10")["total_pago"], mantido["valor_pago"])

    def test_ignorar_nota_preserva_itens_e_todos_ignorados_zeram_relatorios(self):
        for indice in range(2):
            self.revisar(indice)
        importada = self.importar()
        self.ignorar_item(0)
        marcada = self.ignorar_nota().json()
        self.assertEqual(marcada["situacao"], "ignorada")
        self.assertEqual(marcada["importada_em"], importada["importada_em"])
        self.assertEqual(marcada["valor_a_pagar"], "35.68")
        for _ in range(2):
            resumo = self.relatorio()
            self.assertEqual(resumo["total_pago"], "0.00")
            self.assertEqual(resumo["total_desconto"], "0.00")
            self.assertEqual(resumo["quantidade_notas"], 0)
            self.assertEqual(resumo["quantidade_itens"], 0)
            self.assertEqual(resumo["categorias"], [])
            self.assertEqual(resumo["quantidades_compradas"], [])
            self.assertEqual(self.detalhes(), {"itens": [], "total": 0})
            self.assertEqual(self.detalhes("produtos", categoria_id=self.categoria["id"]), [])
            self.assertEqual(self.detalhes("agrupamentos", categoria_id=self.categoria["id"],
                                         produto_id=self.produto["id"], agrupador="marca"), [])
            self.assertEqual(self.relatorio("2026-10")["total_mes_anterior"], "0.00")
            restaurada = self.ignorar_nota(False).json()
            self.assertTrue(restaurada["itens"][0]["ignorado"])
            self.ignorar_item(1)
        self.assertEqual(self.cliente.get(f"/notas/{CHAVE}").json()["situacao"], "importada")

    def test_persiste_reabre_reconsulta_e_migra_banco_existente(self):
        self.ignorar_nota()
        self.ignorar_item(0)
        self.app.state.nota_service.salvar(LeituraService.extrair_nota(HTML, URL_TESTE))
        outro = BancoSQLite(self.caminho)
        self.addCleanup(outro.engine.dispose)
        with outro.conectar() as conexao:
            self.assertEqual(conexao.execute("SELECT ignorada FROM notas").fetchone()[0], 1)
            self.assertEqual(conexao.execute("SELECT ignorado FROM itens ORDER BY numero").fetchone()[0], 1)
        from alembic import command
        config = BancoSQLite.configuracao_migrations(self.caminho)
        command.downgrade(config, "0004")
        command.upgrade(config, "head")
        nota = self.cliente.get(f"/notas/{CHAVE}").json()
        self.assertFalse(nota["ignorada"])
        self.assertTrue(all(not item["ignorado"] for item in nota["itens"]))
        self.assertEqual(nota["valor_a_pagar"], "35.68")

    def test_status_ignorada_filtra_e_restaura_a_situacao_anterior(self):
        for situacao in ("lida", "em_revisao", "importada"):
            with self.subTest(situacao=situacao):
                if situacao == "em_revisao":
                    self.revisar(0)
                elif situacao == "importada":
                    self.revisar(1)
                    self.importar()
                self.assertEqual(self.ignorar_nota().json()["situacao"], "ignorada")
                self.assertEqual(self.cliente.get(f"/notas/{CHAVE}").json()["situacao"], "ignorada")
                todas = self.cliente.get("/notas").json()
                self.assertEqual(len(todas), 1)
                self.assertEqual(todas[0]["situacao"], "ignorada")
                for filtro in ("lida", "em_revisao", "importada", "ignorada"):
                    resposta = self.cliente.get("/notas", params={"situacao": filtro})
                    self.assertEqual(resposta.status_code, 200, resposta.text)
                    self.assertEqual(len(resposta.json()), 1 if filtro == "ignorada" else 0)
                restaurada = self.ignorar_nota(False).json()
                self.assertEqual(restaurada["situacao"], situacao)
                self.assertEqual(len(self.cliente.get("/notas", params={"situacao": situacao}).json()), 1)
                self.assertEqual(self.cliente.get("/notas", params={"situacao": "ignorada"}).json(), [])

    def test_valida_payload_identificadores_e_pertencimento(self):
        for corpo in ({}, {"ignorada": None}, {"ignorada": "false"}):
            self.assertEqual(self.cliente.patch(f"/notas/{CHAVE}/ignorada", json=corpo).status_code, 422)
        self.assertEqual(self.cliente.patch(f"/notas/{'0' * 44}/ignorada", json={"ignorada": True}).status_code, 404)
        self.assertEqual(self.cliente.patch(f"/notas/{CHAVE}/itens/{uuid4()}/ignorado", json={"ignorado": True}).status_code, 404)
        outra = LeituraService.extrair_nota(HTML, URL_TESTE)
        outra.chave = "1" * 44
        outra = self.app.state.nota_service.salvar(outra)
        self.assertEqual(self.cliente.patch(
            f"/notas/{CHAVE}/itens/{outra.itens[0].id}/ignorado", json={"ignorado": True},
        ).status_code, 404)

    def test_rateio_preserva_centavos_mesmo_ao_ignorar_primeiro_item(self):
        nota = self.app.state.nota_service.obter_por_chave(CHAVE)
        nota.id = uuid4()
        nota.chave = "2" * 44
        for item in nota.itens:
            item.id = uuid4()
            item.valor_total = Decimal("1.00")
        nota.valor_total = Decimal("2.00")
        nota.desconto = Decimal("0.01")
        nota.valor_a_pagar = Decimal("1.99")
        nota.itens[0].ignorado = True
        self.app.state.nota_service.salvar(nota)
        revisao = self.app.state.revisao_nota_service
        revisao.revisar_item(nota.chave, nota.itens[1].id, UUID(self.produto["id"]), None, None, Decimal(1))
        revisao.concluir_importacao(nota.chave)
        self.assertEqual(self.relatorio()["total_pago"], "1.00")
        self.assertEqual(self.relatorio()["total_desconto"], "0.00")

