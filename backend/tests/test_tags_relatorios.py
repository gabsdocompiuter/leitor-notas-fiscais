import tempfile
import unittest
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import select

from src.api.app import criar_app
from src.entities.nota_entity import NotaEntity
from src.services.calculos_relatorio import ratear_desconto
from src.services.leitura_service import LeituraService
from tests.test_leitura import HTML, URL_TESTE

CHAVE = "43260907718633007868650080002005971056148317"


class TagsRelatoriosTests(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        self.caminho = Path(self.temporario.name) / "notas.sqlite3"
        self.app = criar_app(self.caminho, lambda _: HTML.encode("utf-8"))
        self.cliente = TestClient(self.app)
        self.addCleanup(self.cliente.close)
        self.nota = self.cliente.post("/leituras", json={"url": URL_TESTE}).json()["nota"]

    def tag(self, nome):
        resposta = self.cliente.post("/tags", json={"nome": nome})
        self.assertEqual(resposta.status_code, 201, resposta.text)
        return resposta.json()

    def marcar(self, item, ids):
        return self.cliente.put(
            f"/notas/{CHAVE}/itens/{item['id']}/tags", json={"tag_ids": ids}
        )

    def importar(self):
        categorias = []
        for indice, item in enumerate(self.nota["itens"]):
            categoria = self.cliente.post(
                "/categorias", json={"nome": f"Categoria {indice}"}
            ).json()
            categorias.append(categoria)
            produto = self.cliente.post("/produtos", json={
                "nome": f"Produto {indice}", "categoria_id": categoria["id"],
                "nao_solicitar_marca": True, "tratar_apenas_como_unidades": False,
                "contem_variacoes": False, "unidade_medida": "KG",
            }).json()
            resposta = self.cliente.patch(f"/notas/{CHAVE}/itens/{item['id']}", json={
                "produto_id": produto["id"], "quantidade_confirmada": "1",
            })
            self.assertEqual(resposta.status_code, 200, resposta.text)
        resposta = self.cliente.post(f"/notas/{CHAVE}/importacao")
        self.assertEqual(resposta.status_code, 200, resposta.text)
        return resposta.json(), categorias

    def relatorio(self, mes):
        resposta = self.cliente.get("/relatorios/mensal", params={"mes": mes})
        self.assertEqual(resposta.status_code, 200, resposta.text)
        return resposta.json()

    def test_catalogo_normaliza_nomes_unicode_e_continua_apos_remocao(self):
        tag = self.tag("  CRIANÇAS   da casa  ")
        repetida = self.tag("crianças da CASA")
        self.assertEqual(tag["id"], repetida["id"])
        self.assertEqual(tag["nome"], "CRIANÇAS da casa")
        self.assertEqual(self.marcar(self.nota["itens"][0], [tag["id"], tag["id"]]).status_code, 200)
        self.assertEqual(self.marcar(self.nota["itens"][0], []).json()["itens"][0]["tags"], [])
        self.assertEqual(self.cliente.get("/tags", params={"busca": "crianças"}).json(), [tag])
        self.assertEqual(self.cliente.post("/tags", json={"nome": "   "}).status_code, 422)
        self.assertEqual(self.cliente.post("/tags", json={"nome": "x" * 101}).status_code, 422)

    def test_sugestoes_limitam_cinco_por_uso_filtram_e_desempatam_por_nome(self):
        tags = {nome: self.tag(nome) for nome in [
            "Alfa", "Beta", "Grupo A", "Grupo B", "Grupo C", "Grupo D", "Grupo E", "Grupo F"
        ]}
        primeira, segunda = self.nota["itens"]
        self.marcar(primeira, [tags["Grupo F"]["id"], tags["Grupo E"]["id"], tags["Grupo E"]["id"]])
        self.marcar(segunda, [tags["Grupo F"]["id"]])

        def nomes(busca=None):
            resposta = self.cliente.get("/tags", params={"busca": busca} if busca else {})
            self.assertEqual(resposta.status_code, 200, resposta.text)
            return [tag["nome"] for tag in resposta.json()]

        populares = ["Grupo F", "Grupo E", "Alfa", "Beta", "Grupo A"]
        self.assertEqual(nomes(), populares)
        self.assertEqual(nomes("gr"), populares)
        self.assertEqual(nomes(" GRU "), ["Grupo F", "Grupo E", "Grupo A", "Grupo B", "Grupo C"])
        self.assertEqual(nomes("grupo d"), ["Grupo D"])
        self.assertEqual(nomes("inexistente"), [])
        self.marcar(primeira, [tags["Grupo E"]["id"]])
        self.assertEqual(nomes()[:2], ["Grupo E", "Grupo F"])

    def test_filtro_de_tags_trata_curingas_como_texto(self):
        literal = self.tag("Oferta %_ especial")
        self.tag("Oferta normal especial")
        self.assertEqual(self.cliente.get("/tags", params={"busca": "%_ "}).json(),
                         self.cliente.get("/tags").json())
        self.assertEqual(self.cliente.get("/tags", params={"busca": "%_ e"}).json(), [literal])

    def test_lote_preserva_tags_individuais_e_nao_altera_revisao(self):
        individual = self.tag("Individual")
        comum = self.tag("Comum")
        self.marcar(self.nota["itens"][0], [individual["id"]])
        for _ in range(2):
            resposta = self.cliente.post(
                f"/notas/{CHAVE}/itens/tags", json={"tag_ids": [comum["id"], comum["id"]]}
            )
            self.assertEqual(resposta.status_code, 200, resposta.text)
        nota = resposta.json()
        self.assertEqual(nota["situacao"], "lida")
        self.assertFalse(any(item["revisado"] for item in nota["itens"]))
        self.assertEqual({tag["id"] for tag in nota["itens"][0]["tags"]}, {individual["id"], comum["id"]})
        self.assertEqual(nota["itens"][1]["tags"], [comum])
        removida = self.marcar(nota["itens"][0], [individual["id"]]).json()
        self.assertEqual(removida["itens"][1]["tags"], [comum])

    def test_ids_invalidos_nao_deixam_alteracoes_parciais(self):
        tag = self.tag("Festa")
        self.marcar(self.nota["itens"][0], [tag["id"]])
        resposta = self.cliente.post(f"/notas/{CHAVE}/itens/tags", json={
            "tag_ids": [tag["id"], str(uuid4())],
        })
        self.assertEqual(resposta.status_code, 404)
        nota = self.cliente.get(f"/notas/{CHAVE}").json()
        self.assertEqual(nota["itens"][0]["tags"], [tag])
        self.assertEqual(nota["itens"][1]["tags"], [])
        self.assertEqual(self.marcar({"id": str(uuid4())}, [tag["id"]]).status_code, 404)

    def test_classificacao_automatica_nao_copia_tags_para_proxima_nota(self):
        tag = self.tag("Festa")
        self.cliente.post(f"/notas/{CHAVE}/itens/tags", json={"tag_ids": [tag["id"]]})
        self.importar()
        url = URL_TESTE.replace("432609", "432608")
        nova = LeituraService.extrair_nota(
            HTML.replace("4326 0907", "4326 0807"), url
        )
        self.app.state.nota_service.salvar(nova)
        revisada = self.app.state.revisao_nota_service.aplicar_classificacoes_automaticas(nova.chave)
        self.assertTrue(all(item.revisado for item in revisada.itens))
        self.assertTrue(all(not item.tags for item in revisada.itens))
        self.assertFalse(revisada.considerar_proximo_mes)

    def test_mes_exclui_pendentes_rateia_e_evitar_duplicacao_por_tag(self):
        tag = self.tag("Festa")
        extra = self.tag("Crianças")
        self.cliente.post(f"/notas/{CHAVE}/itens/tags", json={"tag_ids": [tag["id"]]})
        self.marcar(self.nota["itens"][0], [tag["id"], extra["id"]])
        self.assertEqual(self.relatorio("2026-09")["total_pago"], "0.00")
        importada, categorias = self.importar()
        relatorio = self.relatorio("2026-09")
        self.assertEqual(relatorio["total_pago"], "35.68")
        self.assertEqual(relatorio["total_desconto"], "2.60")
        self.assertEqual(relatorio["quantidade_notas"], 1)
        self.assertEqual(relatorio["quantidade_itens"], 2)
        self.assertEqual(sum(Decimal(grupo["total_pago"]) for grupo in relatorio["categorias"]), Decimal("35.68"))
        festa = next(grupo for grupo in relatorio["tags"] if grupo["id"] == tag["id"])
        self.assertEqual(festa["total_pago"], "35.68")
        self.assertEqual(festa["quantidade_itens"], 2)
        pagina = self.cliente.get("/relatorios/mensal/itens", params={
            "mes": "2026-09", "categoria_id": categorias[0]["id"], "limite": 1,
        }).json()
        self.assertEqual(pagina["total"], 1)
        self.assertEqual(pagina["itens"][0]["id"], importada["itens"][0]["id"])
        todos = self.cliente.get("/relatorios/mensal/itens", params={"mes": "2026-09"}).json()["itens"]
        self.assertEqual(sum(Decimal(item["desconto_rateado"]) for item in todos), Decimal("2.60"))
        for item in todos:
            self.assertEqual(Decimal(item["valor_bruto"]) - Decimal(item["desconto_rateado"]), Decimal(item["valor_pago"]))

    def test_flag_move_nota_inteira_e_pode_ser_revertida_apos_importacao(self):
        importada, _ = self.importar()
        resposta = self.cliente.patch(f"/notas/{CHAVE}", json={"considerar_proximo_mes": True})
        self.assertEqual(resposta.status_code, 200, resposta.text)
        self.assertEqual(resposta.json()["importada_em"], importada["importada_em"])
        self.assertEqual(resposta.json()["emissao"], importada["emissao"])
        self.assertEqual(self.relatorio("2026-09")["quantidade_notas"], 0)
        outubro = self.relatorio("2026-10")
        self.assertEqual(outubro["total_pago"], "35.68")
        self.assertEqual(outubro["quantidade_itens"], 2)
        self.assertEqual(outubro["total_mes_anterior"], "0.00")
        tag = self.tag("Depois")
        ajustada = self.marcar(importada["itens"][0], [tag["id"]]).json()
        self.assertEqual(ajustada["situacao"], "importada")
        self.assertEqual(ajustada["importada_em"], importada["importada_em"])
        self.assertEqual(len(self.relatorio("2026-10")["tags"]), 1)
        self.cliente.patch(f"/notas/{CHAVE}", json={"considerar_proximo_mes": False})
        self.assertEqual(self.relatorio("2026-09")["total_pago"], "35.68")
        self.assertEqual(self.relatorio("2026-10")["total_mes_anterior"], "35.68")

    def test_limites_de_mes_e_virada_do_ano(self):
        self.importar()
        with self.app.state.banco.session_factory.begin() as session:
            nota = session.scalar(select(NotaEntity).where(NotaEntity.chave == CHAVE))
            nota.emissao = datetime(2026, 12, 31, 23, 59, 59)
        self.cliente.patch(f"/notas/{CHAVE}", json={"considerar_proximo_mes": True})
        self.assertEqual(self.relatorio("2026-12")["total_pago"], "0.00")
        self.assertEqual(self.relatorio("2027-01")["total_pago"], "35.68")
        with self.app.state.banco.session_factory.begin() as session:
            nota = session.scalar(select(NotaEntity).where(NotaEntity.chave == CHAVE))
            nota.emissao = datetime(2027, 1, 1)
        self.cliente.patch(f"/notas/{CHAVE}", json={"considerar_proximo_mes": False})
        self.assertEqual(self.relatorio("2027-01")["total_pago"], "35.68")
        for mes in ["2026-13", "2026-00", "0000-01", "0001-01", "9999-12", "abc"]:
            self.assertEqual(self.cliente.get("/relatorios/mensal", params={"mes": mes}).status_code, 422)

    def test_relatorio_nao_depende_do_limite_da_listagem_de_notas(self):
        self.importar()
        # Copia 51 compras importadas com IDs próprios, mantendo o catálogo.
        original = self.app.state.nota_service.obter_por_chave(CHAVE)
        from copy import deepcopy
        for indice in range(51):
            nova = deepcopy(original)
            nova.id = uuid4()
            nova.chave = str(indice).zfill(44)
            for item in nova.itens:
                item.id = uuid4()
            self.app.state.nota_service.salvar(nova)
        self.assertEqual(self.relatorio("2026-09")["quantidade_notas"], 52)
        self.assertEqual(self.relatorio("2026-09")["total_pago"], "1855.36")
        primeira = self.cliente.get("/relatorios/mensal/itens", params={
            "mes": "2026-09", "limite": 50,
        }).json()
        segunda = self.cliente.get("/relatorios/mensal/itens", params={
            "mes": "2026-09", "limite": 50, "deslocamento": 50,
        }).json()
        self.assertEqual(primeira["total"], 104)
        self.assertEqual(len(primeira["itens"]), 50)
        self.assertFalse({item["id"] for item in primeira["itens"]} &
                         {item["id"] for item in segunda["itens"]})

    def test_migration_preserva_nota_existente_e_flag_desmarcada(self):
        self.importar()
        config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
        config.set_main_option("script_location", str(
            Path(__file__).resolve().parents[1] / "src/core/persistence/migrations"
        ))
        config.set_main_option("sqlalchemy.url", f"sqlite:///{self.caminho.as_posix()}")
        command.downgrade(config, "0002")
        command.upgrade(config, "head")
        nota = self.cliente.get(f"/notas/{CHAVE}").json()
        self.assertFalse(nota["considerar_proximo_mes"])
        self.assertEqual(nota["valor_a_pagar"], "35.68")
        self.assertEqual(nota["situacao"], "importada")
        self.assertEqual(len(nota["itens"]), 2)
        self.assertTrue(all(not item["tags"] for item in nota["itens"]))


class RateioTests(unittest.TestCase):
    def test_resto_de_centavos_e_empates_sao_deterministicos(self):
        self.assertEqual(ratear_desconto([Decimal("1.00")] * 3, Decimal("0.01")),
                         [Decimal("0.01"), Decimal("0.00"), Decimal("0.00")])
        self.assertEqual(ratear_desconto([Decimal("1.00")] * 3, Decimal("0.02")),
                         [Decimal("0.01"), Decimal("0.01"), Decimal("0.00")])

    def test_desconto_integral_zero_e_itens_sem_valor(self):
        valores = [Decimal("0.00"), Decimal("0.01"), Decimal("1.00")]
        self.assertEqual(ratear_desconto(valores, Decimal("1.01")), valores)
        self.assertEqual(ratear_desconto(valores, Decimal("0.00")), [Decimal("0.00")] * 3)
        self.assertEqual(ratear_desconto([Decimal("0.00")], Decimal("0.00")), [Decimal("0.00")])
