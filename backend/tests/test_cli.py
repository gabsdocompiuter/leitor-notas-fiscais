import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from src.core.config import URL_NOTA
from src.core.version import __version__
from src.presentation.cli import main


class CliTests(unittest.TestCase):
    def test_cli_encaminha_url_padrao_ou_informada_para_consulta_e_extracao(self):
        outra_url = URL_NOTA.replace("432609", "432608")
        for args, url in (([], URL_NOTA), (["--url", outra_url], outra_url)):
            with self.subTest(args=args), patch("sys.argv", ["main.py", *args]), \
                    patch("src.presentation.cli.consultar_nota", return_value=b"html") as consultar, \
                    patch("src.presentation.cli.extrair_nota") as extrair, \
                    patch("src.presentation.cli.BancoSQLite"), \
                    patch("src.presentation.cli.RepositorioNotas"), \
                    patch("src.presentation.cli.mostrar"), redirect_stdout(io.StringIO()):
                self.assertEqual(main(), 0)
                consultar.assert_called_once_with(url)
                extrair.assert_called_once_with(b"html", url)

    def test_versao_nao_inicia_consulta(self):
        saida = io.StringIO()
        with patch("sys.argv", ["main.py", "--version"]), \
                patch("src.presentation.cli.consultar_nota") as consultar, \
                patch("src.presentation.cli.BancoSQLite") as banco, \
                redirect_stdout(saida), self.assertRaises(SystemExit) as erro:
            main()
        self.assertEqual(erro.exception.code, 0)
        self.assertEqual(saida.getvalue().strip(), __version__)
        consultar.assert_not_called()
        banco.assert_not_called()
