import importlib
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

migration = importlib.import_module("src.core.persistence.migrations.versions.0012_produtos_sabores")


class MigracaoProdutosSaboresTests(unittest.TestCase):
    inserir = staticmethod(chocolate.MigracaoBarrasChocolateTests.inserir)
    conectar = chocolate.MigracaoBarrasChocolateTests.conectar
    snapshot = chocolate.MigracaoBarrasChocolateTests.snapshot

    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        self.caminho = Path(self.temporario.name) / "sabores.sqlite3"
        BancoSQLite.migrar(self.caminho, "0011")

    def popular(self):
        with self.conectar() as c:
            alimentacao = self.inserir(c, "categorias", nome="Alimentação")
            doces = self.inserir(c, "categorias", nome="Doces")
            marca = self.inserir(c, "marcas", nome="Marca preservada")
            self.loja = self.inserir(c, "estabelecimentos", cnpj="12345678000100", razao_social="Loja")
            self.nota = self.inserir(c, "notas", chave="1" * 44, numero="1", serie="1", estabelecimento_id=self.loja,
                emissao="2026-10-01 12:00:00", quantidade_itens=6, valor_total="65.64", desconto="1.00", valor_a_pagar="64.64",
                situacao="importada", importada_em="2026-10-02 12:00:00", considerar_proximo_mes=0, ignorada=0)
            self.casos = []
            for numero, caso in enumerate(migration.CASOS, 1):
                origem, destino, sabor, descricao, quantidade, unidade, base, converter = caso
                produto = self.inserir(c, "produtos", nome=origem, categoria_id=doces if origem == "Bis" else alimentacao,
                    nao_solicitar_marca=origem not in ("Óleo Girassol", "Batata congelada (air fryer)"), nao_solicitar_sabor=1,
                    tratar_apenas_como_unidades=converter, contem_variacoes=not converter, unidade_medida=None if converter else base)
                ap = self.inserir(c, "apresentacoes_produto", produto_id=produto, marca_id=marca if numero in (1, 6) else None)
                tamanho = None if converter else self.inserir(c, "variacoes_produto", produto_id=produto,
                    quantidade=quantidade, unidade_medida=unidade)
                valor = ["16.90", "6.87", "7.99", "15.49", "7.49", "10.90"][numero - 1]
                item = self.inserir(c, "itens", nota_id=self.nota, numero=numero, codigo=str(numero), descricao_original=descricao,
                    quantidade="1", quantidade_confirmada="1", unidade_original="UN", valor_unitario=valor, valor_total=valor,
                    alertas="[]", apresentacao_id=ap, variacao_id=tamanho, sabor_id=None, revisado=1, ignorado=0)
                assoc = self.inserir(c, "associacoes_produto", estabelecimento_id=self.loja, codigo_item=str(numero),
                    descricao_original=descricao, descricao_normalizada=descricao.casefold(), apresentacao_id=ap,
                    variacao_id=tamanho, sabor_id=None, fator_conversao="1.000", unidades_por_pacote=None)
                self.casos.append(dict(caso=caso, produto=produto, ap=ap, tamanho=tamanho, item=item, assoc=assoc))
            # Um registro relacionado pelo tipo de produto, mas fora dos seis mapeamentos.
            self.fora = self.inserir(c, "produtos", nome="Massa Lasanha", categoria_id=alimentacao,
                nao_solicitar_marca=0, nao_solicitar_sabor=1, tratar_apenas_como_unidades=1, contem_variacoes=0, unidade_medida=None)
            tag = self.inserir(c, "tags", nome="Histórico", nome_normalizado="HISTÓRICO")
            c.execute("INSERT INTO itens_tags(item_id,tag_id) VALUES (?,?)", (self.casos[0]["item"], tag))
            c.commit()

    def test_mapeamentos_preservam_historico_e_quantidades(self):
        self.popular()
        antes = self.snapshot()
        BancoSQLite.migrar(self.caminho)
        depois = self.snapshot()
        for tabela in ("notas", "categorias", "marcas", "apresentacoes_produto", "tags", "itens_tags", "estabelecimentos"):
            self.assertEqual(antes[tabela], depois[tabela], tabela)
        self.assertEqual(len(depois["produtos"]), len(antes["produtos"]))
        self.assertEqual(len(depois["sabores_produto"]), 6)
        self.assertEqual(len(depois["variacoes_produto"]), 6)
        produtos_antes = {r["id"]: r for r in antes["produtos"]}
        with self.conectar() as c:
            for x in self.casos:
                origem, destino, sabor, descricao, quantidade, unidade, base, converter = x["caso"]
                produto = dict(c.execute("SELECT * FROM produtos WHERE id=?", (x["produto"],)).fetchone())
                esperado = dict(produtos_antes[x["produto"]], nome=destino, nao_solicitar_sabor=0)
                if converter:
                    esperado.update(tratar_apenas_como_unidades=0, contem_variacoes=1, unidade_medida=base)
                self.assertEqual(produto, esperado)
                for tabela, chave in (("itens", "item"), ("associacoes_produto", "assoc")):
                    linha = dict(c.execute(f"SELECT * FROM {tabela} WHERE id=?", (x[chave],)).fetchone())
                    original = next(r for r in antes[tabela] if r["id"] == x[chave])
                    campos = ("sabor_id", "variacao_id") if converter else ("sabor_id",)
                    self.assertEqual({k:v for k,v in linha.items() if k not in campos},
                                     {k:v for k,v in original.items() if k not in campos})
                    self.assertEqual(c.execute("SELECT nome,produto_id FROM sabores_produto WHERE id=?", (linha["sabor_id"],)).fetchone()[:],
                                     (sabor, x["produto"]))
                    tamanho = c.execute("SELECT quantidade,unidade_medida,produto_id FROM variacoes_produto WHERE id=?",
                                        (linha["variacao_id"],)).fetchone()
                    self.assertEqual((Decimal(tamanho[0]), tamanho[1], tamanho[2]), (Decimal(quantidade), unidade, x["produto"]))
            self.assertEqual(dict(c.execute("SELECT * FROM produtos WHERE id=?", (self.fora,)).fetchone()), produtos_antes[self.fora])
            self.assertEqual(sum(Decimal(r[0]) for r in c.execute("SELECT valor_total FROM itens")), Decimal("65.64"))
            self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])
        BancoSQLite.migrar(self.caminho)
        self.assertEqual(depois, self.snapshot())

    def test_novas_importacoes_reconhecem_os_seis_sabores_e_embalagens(self):
        self.popular()
        BancoSQLite.migrar(self.caminho)
        banco = BancoSQLite(self.caminho)
        self.addCleanup(banco.fechar)
        with banco.session_factory.begin() as session:
            nota = NotaEntity(chave="2" * 44, numero="2", serie="1", estabelecimento_id=UUID(self.loja), emissao=datetime(2026,10,18),
                quantidade_itens=6, valor_total=Decimal(12), desconto=Decimal(0), valor_a_pagar=Decimal(12), situacao=SituacaoNota.LIDA)
            for numero, x in enumerate(self.casos, 1):
                nota.itens.append(ItemEntity(numero=numero, codigo=str(numero), descricao_original=x["caso"][3],
                    quantidade=Decimal(2), unidade_original="UN", valor_unitario=Decimal(1), valor_total=Decimal(2), alertas=[]))
            session.add(nota)
        itens = RevisaoNotaService(banco.session_factory).aplicar_classificacoes_automaticas("2" * 44).itens
        for item in itens:
            x = self.casos[item.numero - 1]
            self.assertTrue(item.revisado)
            self.assertEqual(item.sabor.nome, x["caso"][2])
            self.assertEqual(item.quantidade_confirmada, Decimal(2))
            self.assertEqual(item.variacao.quantidade, Decimal(x["caso"][4]))
            if item.sabor.nome == "Girassol":
                self.assertEqual(item.quantidade_confirmada * item.variacao.quantidade / 1000, Decimal("1.8"))
            if item.sabor.nome == "Maracujá":
                self.assertEqual(item.quantidade_confirmada * item.variacao.quantidade, Decimal(400))

    def test_reutiliza_sabores_e_embalagens_numericamente_equivalentes(self):
        self.popular()
        with self.conectar() as c:
            existentes = []
            for x in self.casos:
                sabor = self.inserir(c, "sabores_produto", produto_id=x["produto"], nome=x["caso"][2])
                tamanho = x["tamanho"] or self.inserir(c, "variacoes_produto", produto_id=x["produto"],
                    quantidade=x["caso"][4]+".000", unidade_medida=x["caso"][5])
                existentes.append((x, sabor, tamanho))
            c.commit()
        BancoSQLite.migrar(self.caminho)
        with self.conectar() as c:
            for x, sabor, tamanho in existentes:
                for tabela, chave in (("itens", "item"), ("associacoes_produto", "assoc")):
                    self.assertEqual(c.execute(f"SELECT sabor_id,variacao_id FROM {tabela} WHERE id=?", (x[chave],)).fetchone()[:], (sabor,tamanho))
            self.assertEqual(c.execute("SELECT count(*) FROM sabores_produto").fetchone()[0], 6)
            self.assertEqual(c.execute("SELECT count(*) FROM variacoes_produto").fetchone()[0], 6)

    def test_conflitos_interrompem_sem_alteracoes_inclusive_revisao(self):
        alteracoes = [
            "UPDATE itens SET descricao_original='DESCONHECIDO' WHERE numero=6",
            "UPDATE associacoes_produto SET descricao_original='DESCONHECIDO' WHERE codigo_item='6'",
            "UPDATE itens SET quantidade_confirmada='0.5' WHERE numero=6",
            "UPDATE associacoes_produto SET fator_conversao='0.5' WHERE codigo_item='6'",
            "UPDATE itens SET quantidade_pacotes='1' WHERE numero=2",
            "UPDATE produtos SET nome='Macarrão' WHERE nome='Massa Lasanha'",
            "UPDATE itens SET variacao_id=(SELECT variacao_id FROM itens WHERE numero=1) WHERE numero=6",
            "UPDATE itens SET sabor_id=(SELECT id FROM sabores_produto LIMIT 1) WHERE numero=6",
            "UPDATE variacoes_produto SET quantidade='1008' WHERE quantidade='100.8'",
        ]
        for sql in alteracoes:
            with self.subTest(sql=sql):
                self.caminho = Path(self.temporario.name) / (str(alteracoes.index(sql))+".sqlite3")
                BancoSQLite.migrar(self.caminho, "0011")
                self.popular()
                with self.conectar() as c:
                    self.inserir(c, "sabores_produto", produto_id=self.casos[0]["produto"], nome="Conflito")
                    c.execute(sql)
                    c.commit()
                antes = self.snapshot()
                with self.assertRaises(ErroPersistencia):
                    BancoSQLite.migrar(self.caminho)
                self.assertEqual(antes, self.snapshot())

    def test_erro_durante_escrita_reverte_todas_as_alteracoes(self):
        self.popular()
        with self.conectar() as c:
            c.execute("CREATE TRIGGER impedir_ultimo BEFORE UPDATE ON produtos WHEN NEW.nome='Óleo de Cozinha' "
                      "BEGIN SELECT RAISE(ABORT,'falha simulada'); END")
            c.commit()
        antes = self.snapshot()
        with self.assertRaises(ErroPersistencia):
            BancoSQLite.migrar(self.caminho)
        self.assertEqual(antes, self.snapshot())

    def test_banco_vazio_nao_cria_catalogo(self):
        BancoSQLite.migrar(self.caminho)
        with self.conectar() as c:
            for tabela in ("produtos", "sabores_produto", "variacoes_produto"):
                self.assertEqual(c.execute(f"SELECT count(*) FROM {tabela}").fetchone()[0], 0)

    def test_downgrade_bloqueado(self):
        self.popular()
        BancoSQLite.migrar(self.caminho)
        antes = self.snapshot()
        with self.assertRaisesRegex(RuntimeError, "backup"):
            command.downgrade(BancoSQLite.configuracao_migrations(self.caminho), "0011")
        self.assertEqual(antes, self.snapshot())
