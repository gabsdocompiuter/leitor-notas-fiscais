import tempfile
import unittest
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path

from src.core.exceptions import ErroPersistencia
from src.core.persistence.banco_sqlite import BancoSQLite
from src.dtos.apresentacao_produto_dto import ApresentacaoProdutoDTO
from src.dtos.categoria_dto import CategoriaDTO
from src.dtos.marca_dto import MarcaDTO
from src.dtos.produto_dto import ProdutoDTO
from src.enums.situacao_nota import SituacaoNota
from src.enums.unidade_medida import UnidadeMedida
from src.services.leitura_nota_service import LeituraNotaService
from src.services.leitura_service import LeituraService
from src.services.nota_service import NotaService
from src.services.qrcode_service import QRCodeService
from test_leitura import HTML, URL_TESTE

ApresentacaoProduto = ApresentacaoProdutoDTO
Categoria = CategoriaDTO
Marca = MarcaDTO
Produto = ProdutoDTO
extrair_nota = LeituraService.extrair_nota
extrair_chave = QRCodeService.extrair_chave


class PersistenciaTests(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        self.caminho = Path(self.temporario.name) / "dados" / "notas.sqlite3"
        self.banco = BancoSQLite(self.caminho)
        self.repo = NotaService(self.banco.session_factory)
        self.leituras = LeituraNotaService(self.banco.session_factory)

    def nova_nota(self):
        return extrair_nota(HTML, URL_TESTE)

    def test_persiste_e_reabre_sem_perder_ids_decimais_ou_situacao(self):
        nota = self.nova_nota()
        leitura = self.leituras.registrar_leitura(URL_TESTE, nota.chave)
        salva = self.repo.salvar(nota, leitura.id)
        outro_banco = BancoSQLite(self.caminho)
        outro_repo = NotaService(outro_banco.session_factory)
        recuperada = outro_repo.obter_por_chave(nota.chave)
        self.assertEqual(asdict(nota), asdict(salva))
        self.assertEqual(asdict(salva), asdict(recuperada))
        self.assertEqual(recuperada.situacao, SituacaoNota.LIDA)
        captura = outro_repo.obter_leitura_por_chave(nota.chave)
        self.assertEqual(captura.id, leitura.id)
        self.assertEqual(captura.nota.id, nota.id)
        self.assertEqual(captura.criada_em, leitura.criada_em)
        with self.banco.conectar() as conexao:
            quantidade = conexao.execute("SELECT quantidade, typeof(quantidade) FROM itens ORDER BY numero").fetchone()
            self.assertEqual(tuple(quantidade), ("0.15", "text"))

    def test_reconsulta_nao_duplica_nem_apaga_apelido_ou_revisao(self):
        nota = self.nova_nota()
        nota.estabelecimento.apelido = "Mercado da esquina"
        nota.itens[0].quantidade_confirmada = Decimal("0.15")
        nota.itens[0].revisado = True
        nota.situacao = SituacaoNota.EM_REVISAO
        primeira = self.repo.salvar(nota)
        segunda = self.repo.salvar(self.nova_nota())
        self.assertEqual(asdict(primeira), asdict(segunda))
        with self.banco.conectar() as conexao:
            self.assertEqual(conexao.execute("SELECT count(*) FROM notas").fetchone()[0], 1)
            self.assertEqual(conexao.execute("SELECT count(*) FROM estabelecimentos").fetchone()[0], 1)
            self.assertEqual(conexao.execute("SELECT count(*) FROM itens").fetchone()[0], 2)

    def test_notas_diferentes_reutilizam_estabelecimento_pelo_cnpj(self):
        a = self.nova_nota()
        a.estabelecimento.apelido = "Meu mercado"
        a = self.repo.salvar(a)
        b = extrair_nota(HTML.replace("4326 0907", "4326 0807"), URL_TESTE.replace("432609", "432608"))
        b = self.repo.salvar(b)
        self.assertNotEqual(a.id, b.id)
        self.assertEqual(a.estabelecimento.id, b.estabelecimento.id)
        self.assertEqual(b.estabelecimento.apelido, "Meu mercado")
        with self.banco.conectar() as conexao:
            self.assertEqual(conexao.execute("SELECT count(*) FROM estabelecimentos").fetchone()[0], 1)

    def test_falha_em_um_item_desfaz_nota_estabelecimento_e_itens(self):
        nota = self.nova_nota()
        nota.itens[1].id = nota.itens[0].id
        with self.assertRaises(ErroPersistencia):
            self.repo.salvar(nota)
        with self.banco.conectar() as conexao:
            for tabela in ("notas", "estabelecimentos", "itens"):
                self.assertEqual(conexao.execute(f"SELECT count(*) FROM {tabela}").fetchone()[0], 0)

    def test_leitura_errada_desfaz_a_transacao(self):
        nota = self.nova_nota()
        url_errada = URL_TESTE.replace("432609", "432608")
        leitura = self.leituras.registrar_leitura(url_errada, extrair_chave(url_errada))
        with self.assertRaisesRegex(ErroPersistencia, "não corresponde"):
            self.repo.salvar(nota, leitura.id)
        self.assertIsNone(self.repo.obter_por_chave(nota.chave))

    def test_persiste_grafo_da_classificacao_quando_presente(self):
        nota = self.nova_nota()
        produto = Produto("Queijo muçarela", Categoria("Alimentação"), unidade_medida=UnidadeMedida.QUILOGRAMA)
        nota.itens[1].apresentacao = ApresentacaoProduto(produto, Marca("Rodeio"))
        nota.itens[1].quantidade_confirmada = Decimal("0.600")
        self.assertEqual(asdict(nota), asdict(self.repo.salvar(nota)))

    def test_registro_de_erro_e_retentativa_preservam_captura(self):
        chave = extrair_chave(URL_TESTE)
        leitura = self.leituras.registrar_leitura(URL_TESTE, chave)
        self.repo.registrar_erro(leitura.id, "Indisponível")
        tentativa = self.leituras.registrar_leitura(URL_TESTE.replace("|", "%7C"), chave)
        self.assertEqual(tentativa.id, leitura.id)
        self.assertEqual(tentativa.erro_consulta, "Indisponível")
        self.repo.salvar(self.nova_nota(), tentativa.id)
        final = self.repo.obter_leitura_por_chave(chave)
        self.assertIsNone(final.erro_consulta)
        self.assertIsNotNone(final.nota)

    def test_banco_ativa_chaves_estrangeiras(self):
        with self.banco.conectar() as conexao:
            self.assertEqual(conexao.execute("PRAGMA foreign_keys").fetchone()[0], 1)
            self.assertEqual(conexao.execute("PRAGMA foreign_key_check").fetchall(), [])
