import unittest
from unittest.mock import MagicMock, patch

from src.core.exceptions import ErroConsulta, ErroLeitura
from src.services.consulta import consultar_nota
from src.services.leitura import extrair_nota
from src.services.qrcode import extrair_chave
from test_leitura import HTML, URL_TESTE


class ConsultaTests(unittest.TestCase):
    def test_consulta_usa_url_recebida_em_vez_da_constante(self):
        outra_url = URL_TESTE.replace("432609", "432608").replace("|", "%7C")
        resposta = MagicMock()
        resposta.__enter__.return_value.read.return_value = b"<html>nota</html>"
        with patch("src.services.consulta.urlopen", return_value=resposta) as abrir:
            self.assertEqual(consultar_nota(outra_url), b"<html>nota</html>")
        requisicao = abrir.call_args.args[0]
        self.assertEqual(requisicao.full_url, outra_url)

    def test_chave_vem_da_url_e_nao_da_constante(self):
        outra_url = URL_TESTE.replace("432609", "432608")
        outro_html = HTML.replace("4326 0907", "4326 0807")
        nota = extrair_nota(outro_html, outra_url)
        self.assertEqual(nota.chave, extrair_chave(outra_url))
        self.assertEqual(nota.url_origem, outra_url)
        with self.assertRaisesRegex(ErroLeitura, "URL consultada"):
            extrair_nota(outro_html, URL_TESTE)

    def test_aceita_qrcode_original_da_sefaz_e_parametros_codificados(self):
        original = URL_TESTE.replace(
            "https://dfe-portal.svrs.rs.gov.br/Dfe/QrCodeNFce",
            "https://www.sefaz.rs.gov.br/NFCE/NFCE-COM.aspx",
        )
        self.assertEqual(extrair_chave(original), extrair_chave(URL_TESTE.replace("|", "%7C")))

    def test_rejeita_urls_invalidas_antes_de_acessar_a_rede(self):
        invalidas = [
            "file:///etc/passwd", "http://127.0.0.1/", "https://example.com/",
            URL_TESTE.replace("https:", "http:"),
            URL_TESTE.replace("432609", "352609"),
            URL_TESTE.replace("432609", "abc"),
            URL_TESTE.split("?")[0],
            URL_TESTE + "&p=duplicado",
            URL_TESTE.replace(".br/", ".br:1234/"),
            URL_TESTE.replace("https://", "https://usuario:senha@"),
        ]
        with patch("src.services.consulta.urlopen") as abrir:
            for url in invalidas:
                with self.subTest(url=url), self.assertRaises(ErroConsulta):
                    consultar_nota(url)
            abrir.assert_not_called()
