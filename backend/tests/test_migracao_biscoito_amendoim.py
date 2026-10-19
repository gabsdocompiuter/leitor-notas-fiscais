import tempfile
import unittest
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from alembic import command

from src.core.exceptions import ErroPersistencia
from src.core.persistence.banco_sqlite import BancoSQLite
from src.entities import ItemEntity, NotaEntity
from src.enums.situacao_nota import SituacaoNota
from src.services.revisao_nota_service import RevisaoNotaService
from tests import test_migracao_barras_chocolate as chocolate


class MigracaoBiscoitoAmendoimTests(unittest.TestCase):
    inserir = staticmethod(chocolate.MigracaoBarrasChocolateTests.inserir)
    conectar = chocolate.MigracaoBarrasChocolateTests.conectar
    snapshot = chocolate.MigracaoBarrasChocolateTests.snapshot

    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        self.caminho = Path(self.temporario.name) / "biscoitos.sqlite3"
        BancoSQLite.migrar(self.caminho, "0010")

    def popular(self, origem=True):
        with self.conectar() as c:
            self.alimentacao = self.inserir(c, "categorias", nome="Alimentação")
            self.doces = self.inserir(c, "categorias", nome="Doces")
            self.loja = self.inserir(c, "estabelecimentos", cnpj="12345678000100", razao_social="Loja")
            self.nota = self.inserir(c, "notas", chave="1" * 44, numero="1", serie="1", estabelecimento_id=self.loja,
                emissao="2026-10-09 13:53:09", quantidade_itens=6, valor_total="37.98", desconto="1.00", valor_a_pagar="36.98",
                situacao="importada", importada_em="2026-10-10 12:00:00", considerar_proximo_mes=0, ignorada=0)
            self.destino = self.inserir(c, "produtos", nome="Biscoito", categoria_id=self.alimentacao,
                nao_solicitar_marca=0, nao_solicitar_sabor=0, tratar_apenas_como_unidades=0, contem_variacoes=1, unidade_medida="G")
            self.sabor = self.inserir(c, "sabores_produto", produto_id=self.destino, nome="Amendoim")
            coco = self.inserir(c, "sabores_produto", produto_id=self.destino, nome="Coco")
            cebola = self.inserir(c, "sabores_produto", produto_id=self.destino, nome="Cebola e Salsa")
            ana = self.inserir(c, "marcas", nome="Ana Julia")
            zeze = self.inserir(c, "marcas", nome="Zezé")
            ap_ana = self.inserir(c, "apresentacoes_produto", produto_id=self.destino, marca_id=ana)
            ap_zeze = self.inserir(c, "apresentacoes_produto", produto_id=self.destino, marca_id=zeze)
            tamanho200 = self.inserir(c, "variacoes_produto", produto_id=self.destino, quantidade="200", unidade_medida="G")
            tamanho80 = self.inserir(c, "variacoes_produto", produto_id=self.destino, quantidade="80", unidade_medida="G")
            casos = [
                ("coco", "BISCOITO ANA JULIA 200g COCO", ap_ana, tamanho200, coco, "5.47"),
                ("amendoim", "BISCOITO ANA JULIA 200g AMENDOIM", ap_ana, tamanho200, self.sabor, "5.47"),
                ("cebola", "BISCOITO ZEZE 80G PETISK CEBOLA E SALSA", ap_zeze, tamanho80, cebola, "3.69"),
            ]
            if origem:
                self.origem = self.inserir(c, "produtos", nome="Biscoito de Amendoim", categoria_id=self.alimentacao,
                    nao_solicitar_marca=1, nao_solicitar_sabor=1, tratar_apenas_como_unidades=1, contem_variacoes=0, unidade_medida=None)
                self.ap_origem = self.inserir(c, "apresentacoes_produto", produto_id=self.origem, marca_id=None)
                casos.append(("pasetto", "BISCOITO PASETTO 250g AMENDOIM", self.ap_origem, None, None, "11.99"))
            sequilhos = self.inserir(c, "produtos", nome="Biscoito Sequilhos", categoria_id=self.alimentacao,
                nao_solicitar_marca=1, nao_solicitar_sabor=1, tratar_apenas_como_unidades=1, contem_variacoes=0, unidade_medida=None)
            ap_sequilhos = self.inserir(c, "apresentacoes_produto", produto_id=sequilhos, marca_id=None)
            casos.append(("sequilhos", "BISCOITO SEQ.FERNANDES 200g MARAC. SGL", ap_sequilhos, None, None, "6.87"))
            recheada = self.inserir(c, "produtos", nome="Bolacha Recheada", categoria_id=self.doces,
                nao_solicitar_marca=0, nao_solicitar_sabor=0, tratar_apenas_como_unidades=0, contem_variacoes=1, unidade_medida="G")
            orquidea = self.inserir(c, "marcas", nome="Orquídea")
            ap_recheada = self.inserir(c, "apresentacoes_produto", produto_id=recheada, marca_id=orquidea)
            tamanho130 = self.inserir(c, "variacoes_produto", produto_id=recheada, quantidade="130", unidade_medida="G")
            sabor_chocolate = self.inserir(c, "sabores_produto", produto_id=recheada, nome="Chocolate")
            casos.append(("recheada", "BISCOITO ORQUIDEA 130G TORTISSIMAS RECHEADO CHOCOLATE", ap_recheada, tamanho130, sabor_chocolate, "4.49"))
            self.itens = {}
            for numero, (codigo, descricao, ap, tamanho, sabor, valor) in enumerate(casos, 1):
                self.itens[codigo] = self.inserir(c, "itens", nota_id=self.nota, numero=numero, codigo=codigo,
                    descricao_original=descricao, quantidade="1", quantidade_confirmada="1", unidade_original="UN", valor_unitario=valor,
                    valor_total=valor, alertas="[]", apresentacao_id=ap, variacao_id=tamanho, sabor_id=sabor, revisado=1, ignorado=0)
                self.inserir(c, "associacoes_produto", estabelecimento_id=self.loja, codigo_item=codigo, descricao_original=descricao,
                    descricao_normalizada=descricao.upper(), apresentacao_id=ap, variacao_id=tamanho, sabor_id=sabor,
                    fator_conversao="1.000", unidades_por_pacote=None)
            tag = self.inserir(c, "tags", nome="Biscoitos", nome_normalizado="BISCOITOS")
            c.execute("INSERT INTO itens_tags(item_id,tag_id) VALUES (?,?)", (self.itens["amendoim"], tag))
            c.commit()

    def test_consolida_preservando_sabor_existente_e_historico(self):
        self.popular()
        antes = self.snapshot()
        BancoSQLite.migrar(self.caminho, "0011")
        depois = self.snapshot()
        self.assertEqual(len(depois["produtos"]), len(antes["produtos"]) - 1)
        self.assertEqual(depois["sabores_produto"], antes["sabores_produto"])
        for tabela in ("notas", "categorias", "tags", "itens_tags", "estabelecimentos"):
            self.assertEqual(depois[tabela], antes[tabela])
        for tabela in ("itens", "associacoes_produto"):
            originais = {r["id"]: r for r in antes[tabela]}
            for linha in depois[tabela]:
                original = originais[linha["id"]]
                codigo = linha["codigo"] if tabela == "itens" else linha["codigo_item"]
                if codigo != "pasetto":
                    self.assertEqual(linha, original)
                else:
                    campos = ("apresentacao_id", "sabor_id", "variacao_id")
                    self.assertEqual({k: v for k, v in linha.items() if k not in campos}, {k: v for k, v in original.items() if k not in campos})
                    self.assertEqual(linha["sabor_id"], self.sabor)
        with self.conectar() as c:
            self.assertIsNone(c.execute("SELECT id FROM produtos WHERE id=?", (self.origem,)).fetchone())
            destino = dict(c.execute("SELECT * FROM produtos WHERE id=?", (self.destino,)).fetchone())
            self.assertEqual(destino, next(p for p in antes["produtos"] if p["id"] == self.destino))
            migrado = c.execute("SELECT p.id,m.nome,s.id,v.quantidade,v.unidade_medida,i.quantidade_confirmada FROM itens i "
                "JOIN apresentacoes_produto ap ON ap.id=i.apresentacao_id JOIN produtos p ON p.id=ap.produto_id "
                "JOIN marcas m ON m.id=ap.marca_id JOIN sabores_produto s ON s.id=i.sabor_id JOIN variacoes_produto v ON v.id=i.variacao_id "
                "WHERE i.codigo='pasetto'").fetchone()
            self.assertEqual(tuple(migrado), (self.destino, "Pasetto", self.sabor, "250", "G", "1"))
            totais = c.execute("SELECT i.valor_total,i.quantidade_confirmada,v.quantidade FROM itens i JOIN apresentacoes_produto ap "
                "ON ap.id=i.apresentacao_id JOIN variacoes_produto v ON v.id=i.variacao_id WHERE ap.produto_id=?", (self.destino,)).fetchall()
            self.assertEqual(len(totais), 4)
            self.assertEqual(sum(Decimal(r[0]) for r in totais), Decimal("26.62"))
            self.assertEqual(sum(Decimal(r[1]) * Decimal(r[2]) for r in totais), Decimal(730))
            self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])
        BancoSQLite.migrar(self.caminho, "0011")
        self.assertEqual(self.snapshot(), depois)

    def test_reconhecimento_automatico_mantem_contagem_e_calcula_peso(self):
        self.popular()
        BancoSQLite.migrar(self.caminho, "0011")
        banco = BancoSQLite(self.caminho)
        self.addCleanup(banco.fechar)
        with banco.session_factory.begin() as session:
            nota = NotaEntity(chave="2" * 44, numero="2", serie="1", estabelecimento_id=UUID(self.loja), emissao=datetime(2026, 10, 18),
                quantidade_itens=1, valor_total=Decimal("23.98"), desconto=Decimal(0), valor_a_pagar=Decimal("23.98"), situacao=SituacaoNota.LIDA)
            nota.itens.append(ItemEntity(numero=1, codigo="pasetto", descricao_original="BISCOITO PASETTO 250g AMENDOIM", quantidade=Decimal(2),
                unidade_original="UN", valor_unitario=Decimal("11.99"), valor_total=Decimal("23.98"), alertas=[]))
            session.add(nota)
        item = RevisaoNotaService(banco.session_factory).aplicar_classificacoes_automaticas("2" * 44).itens[0]
        self.assertTrue(item.revisado)
        self.assertEqual(item.sabor.nome, "Amendoim")
        self.assertEqual(item.apresentacao.marca.nome, "Pasetto")
        self.assertEqual(item.quantidade_confirmada, Decimal(2))
        self.assertEqual(item.quantidade_confirmada * item.variacao.quantidade, Decimal(500))

    def test_reutiliza_marca_apresentacao_e_embalagem(self):
        self.popular()
        with self.conectar() as c:
            marca = self.inserir(c, "marcas", nome="Pasetto")
            ap = self.inserir(c, "apresentacoes_produto", produto_id=self.destino, marca_id=marca)
            tamanho = self.inserir(c, "variacoes_produto", produto_id=self.destino, quantidade="250.000", unidade_medida="G")
            c.commit()
        BancoSQLite.migrar(self.caminho, "0011")
        with self.conectar() as c:
            for tabela, campo in (("itens", "codigo"), ("associacoes_produto", "codigo_item")):
                r = c.execute(f"SELECT apresentacao_id,variacao_id,sabor_id FROM {tabela} WHERE {campo}='pasetto'").fetchone()
                self.assertEqual(tuple(r), (ap, tamanho, self.sabor))
            self.assertEqual(c.execute("SELECT count(*) FROM marcas WHERE nome='Pasetto'").fetchone()[0], 1)
            self.assertEqual(c.execute("SELECT count(*) FROM variacoes_produto WHERE produto_id=?", (self.destino,)).fetchone()[0], 3)

    def test_cria_sabor_somente_quando_ausente(self):
        self.popular()
        with self.conectar() as c:
            for tabela in ("itens", "associacoes_produto"):
                c.execute(f"UPDATE {tabela} SET sabor_id=NULL WHERE sabor_id=?", (self.sabor,))
            c.execute("DELETE FROM sabores_produto WHERE id=?", (self.sabor,))
            c.commit()
        BancoSQLite.migrar(self.caminho, "0011")
        with self.conectar() as c:
            self.assertEqual(c.execute("SELECT count(*) FROM sabores_produto WHERE produto_id=? AND nome='Amendoim'", (self.destino,)).fetchone()[0], 1)
            self.assertIsNotNone(c.execute("SELECT sabor_id FROM itens WHERE codigo='pasetto'").fetchone()[0])

    def test_sem_origem_nao_cria_cadastros_e_downgrade_exige_backup(self):
        BancoSQLite.migrar(self.caminho, "0011")
        vazio = self.snapshot()
        for tabela in ("categorias", "produtos", "sabores_produto", "marcas"):
            self.assertEqual(vazio[tabela], [])
        with self.assertRaisesRegex(RuntimeError, "backup"):
            command.downgrade(BancoSQLite.configuracao_migrations(self.caminho), "0010")
        self.assertEqual(self.snapshot(), vazio)
        self.caminho = Path(self.temporario.name) / "sem-origem.sqlite3"
        BancoSQLite.migrar(self.caminho, "0010")
        self.popular(origem=False)
        antes = self.snapshot()
        BancoSQLite.migrar(self.caminho, "0011")
        depois = self.snapshot()
        antes.pop("alembic_version")
        depois.pop("alembic_version")
        self.assertEqual(depois, antes)

    def test_conflitos_revertem_sem_alterar_nenhum_registro(self):
        cenarios = (
            ("descricao", "UPDATE itens SET descricao_original='OUTRO BISCOITO' WHERE codigo='pasetto'"),
            ("marca", "UPDATE apresentacoes_produto SET marca_id=(SELECT id FROM marcas WHERE nome='Ana Julia') WHERE produto_id=(SELECT id FROM produtos WHERE nome='Biscoito de Amendoim')"),
            ("sabor", "UPDATE itens SET sabor_id=(SELECT id FROM sabores_produto WHERE nome='Coco') WHERE codigo='pasetto'"),
            ("embalagem", "UPDATE itens SET variacao_id=(SELECT id FROM variacoes_produto WHERE quantidade='200') WHERE codigo='pasetto'"),
            ("fracao", "UPDATE itens SET quantidade_confirmada='0.5' WHERE codigo='pasetto'"),
            ("pacotes", "UPDATE itens SET quantidade_pacotes='1',unidades_por_pacote='1' WHERE codigo='pasetto'"),
            ("pacotes_associacao", "UPDATE associacoes_produto SET unidades_por_pacote='2' WHERE codigo_item='pasetto'"),
            ("sem_destino", "UPDATE produtos SET nome='Outro biscoito' WHERE nome='Biscoito'"),
            ("estrutura", "UPDATE produtos SET unidade_medida='KG' WHERE nome='Biscoito'"),
            ("categoria", "UPDATE produtos SET categoria_id=(SELECT id FROM categorias WHERE nome='Doces') WHERE nome='Biscoito de Amendoim'"),
        )
        for nome, sql in cenarios:
            with self.subTest(cenario=nome):
                self.caminho = Path(self.temporario.name) / f"{nome}.sqlite3"
                BancoSQLite.migrar(self.caminho, "0010")
                self.popular()
                with self.conectar() as c:
                    c.execute(sql)
                    c.commit()
                antes = self.snapshot()
                with self.assertRaises(ErroPersistencia):
                    BancoSQLite.migrar(self.caminho, "0011")
                self.assertEqual(self.snapshot(), antes)

    def test_falha_apos_transferencia_reverte_itens_e_novos_cadastros(self):
        self.popular()
        with self.conectar() as c:
            c.execute("CREATE TRIGGER falha BEFORE DELETE ON produtos WHEN OLD.nome='Biscoito de Amendoim' BEGIN SELECT RAISE(ABORT,'falha simulada'); END")
            c.commit()
        antes = self.snapshot()
        with self.assertRaisesRegex(ErroPersistencia, "falha simulada"):
            BancoSQLite.migrar(self.caminho, "0011")
        self.assertEqual(self.snapshot(), antes)
