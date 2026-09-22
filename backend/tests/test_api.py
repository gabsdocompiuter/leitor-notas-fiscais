import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from src.api.app import criar_app
from src.core.exceptions import ErroConsulta
from tests.test_leitura import HTML, URL_TESTE


CHAVE = "43260907718633007868650080002005971056148317"


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.consultas = 0

        def consultar(_: str) -> bytes:
            self.consultas += 1
            return HTML.encode("utf-8")

        app = criar_app(Path(self.temporario.name) / "notas.sqlite3", consultar)
        self.cliente = TestClient(app)

    def tearDown(self):
        self.cliente.close()
        self.temporario.cleanup()

    def test_health_e_swagger(self):
        self.assertEqual(self.cliente.get("/health").json(), {"status": "ok"})
        especificacao = self.cliente.get("/openapi.json").json()
        self.assertIn("/leituras", especificacao["paths"])
        self.assertIn("/notas/{chave}", especificacao["paths"])
        self.assertIn("/notas/{chave}/itens/{item_id}", especificacao["paths"])
        self.assertIn("/notas/{chave}/importacao", especificacao["paths"])
        self.assertIn("/categorias", especificacao["paths"])
        self.assertIn("/marcas", especificacao["paths"])
        self.assertIn("/produtos", especificacao["paths"])
        self.assertNotIn("/api/v1/leituras", especificacao["paths"])
        swagger = self.cliente.get("/docs")
        self.assertEqual(swagger.status_code, 200)
        self.assertIn("Swagger UI", swagger.text)

    def test_leitura_salva_e_reutiliza_nota_sem_nova_consulta(self):
        primeira = self.cliente.post("/leituras", json={"url": URL_TESTE})
        self.assertEqual(primeira.status_code, 200)
        dados = primeira.json()
        self.assertEqual(dados["nota"]["chave"], CHAVE)
        self.assertEqual(dados["nota"]["valor_a_pagar"], "35.68")
        self.assertEqual(len(dados["nota"]["itens"]), 2)

        segunda = self.cliente.post("/leituras", json={"url": URL_TESTE})
        self.assertEqual(segunda.status_code, 200)
        self.assertEqual(segunda.json()["id"], dados["id"])
        self.assertEqual(segunda.json()["nota"]["id"], dados["nota"]["id"])
        self.assertEqual(self.consultas, 1)

        self.assertEqual(
            self.cliente.get(f"/leituras/{CHAVE}").json()["id"], dados["id"]
        )
        self.assertEqual(
            self.cliente.get(f"/notas/{CHAVE}").json()["id"],
            dados["nota"]["id"],
        )
        lista = self.cliente.get("/notas", params={"situacao": "lida"})
        self.assertEqual(lista.status_code, 200)
        self.assertEqual([nota["chave"] for nota in lista.json()], [CHAVE])
        self.assertEqual(
            self.cliente.get("/notas", params={"situacao": "importada"}).json(),
            [],
        )

    def test_qrcode_invalido_retorna_erro_documentado(self):
        resposta = self.cliente.post(
            "/leituras", json={"url": "https://exemplo.com/nota"}
        )
        self.assertEqual(resposta.status_code, 422)
        self.assertEqual(resposta.json()["codigo"], "qrcode_invalido")
        self.assertEqual(self.consultas, 0)

    def test_recursos_ausentes_retorna_erro_documentado(self):
        for rota in ("leituras", "notas"):
            with self.subTest(rota=rota):
                resposta = self.cliente.get(f"/{rota}/{'0' * 44}")
                self.assertEqual(resposta.status_code, 404)
                self.assertEqual(
                    resposta.json(),
                    {"codigo": "nao_encontrado", "mensagem": resposta.json()["mensagem"]},
                )

    def test_falha_da_sefaz_e_registrada_na_leitura(self):
        def falhar(_: str) -> bytes:
            raise ErroConsulta("SEFAZ indisponível")

        caminho = Path(self.temporario.name) / "falha.sqlite3"
        with TestClient(criar_app(caminho, falhar)) as cliente:
            resposta = cliente.post("/leituras", json={"url": URL_TESTE})
            self.assertEqual(resposta.status_code, 502)
            self.assertEqual(resposta.json()["codigo"], "falha_consulta_sefaz")
            leitura = cliente.get(f"/leituras/{CHAVE}").json()
            self.assertIsNone(leitura["nota"])
            self.assertEqual(leitura["erro_consulta"], "SEFAZ indisponível")


if __name__ == "__main__":
    unittest.main()
