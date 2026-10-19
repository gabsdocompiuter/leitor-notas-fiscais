import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

from alembic import command

from src.core.exceptions import ErroPersistencia
from src.core.persistence.banco_sqlite import BancoSQLite
from src.entities import ItemEntity, NotaEntity
from src.enums.situacao_nota import SituacaoNota
from src.services.revisao_nota_service import RevisaoNotaService


class MigracaoBarrasChocolateTests(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        self.caminho = Path(self.temporario.name) / "chocolates.sqlite3"
        BancoSQLite.migrar(self.caminho, "0009")

    def conectar(self):
        conexao = sqlite3.connect(self.caminho)
        conexao.execute("PRAGMA foreign_keys=ON")
        conexao.row_factory = sqlite3.Row
        return closing(conexao)

    @staticmethod
    def inserir(conexao, tabela, **valores):
        identificador = valores.setdefault("id", uuid4().hex)
        conexao.execute(f"INSERT INTO {tabela} ({','.join(valores)}) VALUES ({','.join('?' for _ in valores)})", tuple(valores.values()))
        return identificador

    def snapshot(self):
        with self.conectar() as c:
            tabelas = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
            return {t: [dict(r) for r in c.execute(f"SELECT * FROM {t} ORDER BY 1")] for t in tabelas}

    def popular(self, origens=True):
        with self.conectar() as c:
            self.alimentacao = self.inserir(c, "categorias", nome="Alimentação")
            self.doces = self.inserir(c, "categorias", nome="Doces")
            self.lacta = self.inserir(c, "marcas", nome="Lacta")
            self.loja = self.inserir(c, "estabelecimentos", cnpj="12345678000100", razao_social="Loja")
            self.nota = self.inserir(c, "notas", chave="1" * 44, numero="1", serie="1", estabelecimento_id=self.loja,
                emissao="2026-10-14 21:42:26", quantidade_itens=6, valor_total="59.11", desconto="1.00", valor_a_pagar="58.11",
                situacao="importada", importada_em="2026-10-15 10:00:00", considerar_proximo_mes=0, ignorada=0)
            self.destino = self.inserir(c, "produtos", nome="Barra de Chocolate", categoria_id=self.alimentacao,
                nao_solicitar_marca=0, nao_solicitar_sabor=0, tratar_apenas_como_unidades=0, contem_variacoes=1, unidade_medida="G")
            self.ap_destino = self.inserir(c, "apresentacoes_produto", produto_id=self.destino, marca_id=self.lacta)
            self.tamanho = self.inserir(c, "variacoes_produto", produto_id=self.destino, quantidade="145", unidade_medida="G")
            self.amaro = self.inserir(c, "sabores_produto", produto_id=self.destino, nome="Amaro")
            self.shot = self.inserir(c, "sabores_produto", produto_id=self.destino, nome="Shot")
            casos = [
                ("amaro1", "CHOC LACTA AMARO FAMILIA 40% 145g", self.ap_destino, self.tamanho, self.amaro, "10.98"),
                ("shot", "CHOC LACTA SHOT FAMILIA 145g", self.ap_destino, self.tamanho, self.shot, "10.98"),
                ("amaro2", "CHOCOLATE LACTA 145g AMARO", self.ap_destino, self.tamanho, self.amaro, "13.99"),
            ]
            self.fontes = {}
            if origens:
                for nome, codigo, descricao, marca in (
                    ("Barra chocolate ao leite", "leite", "CHOC LACTA 145G LEIT TAM FAMILIA", self.lacta),
                    ("Barra diamante negro", "diamante", "CHOC LACTA 145G DIAM NEGRO TAM FAMILIA", None),
                ):
                    produto = self.inserir(c, "produtos", nome=nome, categoria_id=self.doces,
                        nao_solicitar_marca=marca is None, nao_solicitar_sabor=1, tratar_apenas_como_unidades=0, contem_variacoes=1, unidade_medida="G")
                    self.fontes[codigo] = produto
                    ap = self.inserir(c, "apresentacoes_produto", produto_id=produto, marca_id=marca)
                    tamanho = self.inserir(c, "variacoes_produto", produto_id=produto, quantidade="145.000", unidade_medida="G")
                    casos.append((codigo, descricao, ap, tamanho, None, "9.99"))
            self.cereal = self.inserir(c, "produtos", nome="Barra de Cereal", categoria_id=self.alimentacao,
                nao_solicitar_marca=1, nao_solicitar_sabor=1, tratar_apenas_como_unidades=1, contem_variacoes=0, unidade_medida=None)
            ap_cereal = self.inserir(c, "apresentacoes_produto", produto_id=self.cereal, marca_id=None)
            casos.append(("cereal", "BARRA CEREAL RITTER BROWN COB CHOC 25g", ap_cereal, None, None, "3.18"))
            self.itens = {}
            for numero, (codigo, descricao, ap, tamanho, sabor, valor) in enumerate(casos, 1):
                self.itens[codigo] = self.inserir(c, "itens", nota_id=self.nota, numero=numero, codigo=codigo, descricao_original=descricao,
                    quantidade="1.000", quantidade_confirmada="1.000", unidade_original="UN", valor_unitario=valor, valor_total=valor,
                    alertas="[]", apresentacao_id=ap, variacao_id=tamanho, sabor_id=sabor, revisado=1, ignorado=codigo == "cereal")
                self.inserir(c, "associacoes_produto", estabelecimento_id=self.loja, codigo_item=codigo, descricao_original=descricao,
                    descricao_normalizada=descricao.upper(), apresentacao_id=ap, variacao_id=tamanho, sabor_id=sabor,
                    fator_conversao="1.000", unidades_por_pacote=None)
            tag = self.inserir(c, "tags", nome="Chocolate", nome_normalizado="CHOCOLATE")
            c.execute("INSERT INTO itens_tags(item_id, tag_id) VALUES (?, ?)", (self.itens["amaro1"], tag))
            c.commit()

    def test_consolida_reutiliza_vinculos_e_preserva_historico(self):
        self.popular()
        antes = self.snapshot()
        BancoSQLite.migrar(self.caminho, "0010")
        depois = self.snapshot()
        self.assertEqual(len(depois["produtos"]), 2)
        self.assertEqual(len(depois["sabores_produto"]), 4)
        for tabela in ("notas", "estabelecimentos", "tags", "itens_tags", "marcas", "categorias"):
            self.assertEqual(depois[tabela], antes[tabela])
        for tabela in ("itens", "associacoes_produto"):
            def protegido(linhas):
                return [{k: v for k, v in r.items() if k not in ("apresentacao_id", "variacao_id", "sabor_id")} for r in linhas]
            self.assertEqual(protegido(depois[tabela]), protegido(antes[tabela]))
            antigos = {r["id"]: r for r in antes[tabela]}
            for r in depois[tabela]:
                if r["id"] not in {self.itens["leite"], self.itens["diamante"]} and tabela == "itens":
                    self.assertEqual(r, antigos[r["id"]])
        with self.conectar() as c:
            produto = dict(c.execute("SELECT * FROM produtos WHERE id=?", (self.destino,)).fetchone())
            self.assertEqual((produto["categoria_id"], produto["nao_solicitar_marca"], produto["nao_solicitar_sabor"]), (self.doces, 0, 0))
            for codigo, sabor in (("leite", "Ao leite"), ("diamante", "Diamante Negro")):
                for tabela, coluna in (("itens", "codigo"), ("associacoes_produto", "codigo_item")):
                    r = c.execute(f"SELECT r.apresentacao_id,r.variacao_id,s.nome FROM {tabela} r JOIN sabores_produto s ON s.id=r.sabor_id WHERE r.{coluna}=?", (codigo,)).fetchone()
                    self.assertEqual(tuple(r), (self.ap_destino, self.tamanho, sabor))
            self.assertEqual(c.execute("SELECT count(*) FROM variacoes_produto WHERE produto_id=?", (self.destino,)).fetchone()[0], 1)
            self.assertEqual(c.execute("SELECT count(*) FROM apresentacoes_produto WHERE produto_id=?", (self.destino,)).fetchone()[0], 1)
            self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])
            total = c.execute("SELECT i.valor_total,i.quantidade_confirmada,v.quantidade FROM itens i JOIN apresentacoes_produto ap ON ap.id=i.apresentacao_id JOIN variacoes_produto v ON v.id=i.variacao_id WHERE ap.produto_id=?", (self.destino,)).fetchall()
            self.assertEqual(sum(Decimal(r[0]) for r in total), Decimal("55.93"))
            self.assertEqual(sum(Decimal(r[1]) * Decimal(r[2]) for r in total), Decimal(725))
        BancoSQLite.migrar(self.caminho, "0010")
        self.assertEqual(self.snapshot(), depois)

    def test_classificacao_automatica_reconhece_ambos_os_sabores(self):
        self.popular()
        BancoSQLite.migrar(self.caminho, "0010")
        banco = BancoSQLite(self.caminho)
        self.addCleanup(banco.fechar)
        with banco.session_factory.begin() as session:
            nota = NotaEntity(chave="2" * 44, numero="2", serie="1", estabelecimento_id=UUID(self.loja), emissao=datetime(2026, 10, 18),
                quantidade_itens=2, valor_total=Decimal(20), desconto=Decimal(0), valor_a_pagar=Decimal(20), situacao=SituacaoNota.LIDA)
            for numero, codigo in enumerate(("leite", "diamante"), 1):
                nota.itens.append(ItemEntity(numero=numero, codigo=codigo, descricao_original=codigo, quantidade=Decimal(1),
                    unidade_original="UN", valor_unitario=Decimal(10), valor_total=Decimal(10), alertas=[]))
            session.add(nota)
        resultado = RevisaoNotaService(banco.session_factory).aplicar_classificacoes_automaticas("2" * 44)
        self.assertEqual([i.sabor.nome for i in resultado.itens], ["Ao leite", "Diamante Negro"])
        self.assertTrue(all(i.revisado and i.apresentacao.marca.nome == "Lacta" and i.variacao.quantidade == Decimal(145) for i in resultado.itens))

    def test_vazio_nao_cria_catalogo_e_downgrade_exige_backup(self):
        BancoSQLite.migrar(self.caminho, "0010")
        depois = self.snapshot()
        for tabela in ("produtos", "categorias", "sabores_produto", "marcas"):
            self.assertEqual(depois[tabela], [])
        with self.assertRaisesRegex(RuntimeError, "backup"):
            command.downgrade(BancoSQLite.configuracao_migrations(self.caminho), "0009")
        self.assertEqual(self.snapshot(), depois)

    def test_sem_origens_garante_doces_e_sabores_sem_duplicacao(self):
        self.popular(origens=False)
        with self.conectar() as c:
            c.execute("DELETE FROM categorias WHERE id=?", (self.doces,))
            self.ao_leite = self.inserir(c, "sabores_produto", produto_id=self.destino, nome="Ao leite")
            c.commit()
        BancoSQLite.migrar(self.caminho, "0010")
        with self.conectar() as c:
            categoria = c.execute("SELECT cat.nome FROM produtos p JOIN categorias cat ON cat.id=p.categoria_id WHERE p.id=?", (self.destino,)).fetchone()[0]
            self.assertEqual(categoria, "Doces")
            self.assertEqual(c.execute("SELECT id FROM sabores_produto WHERE produto_id=? AND nome='Ao leite'", (self.destino,)).fetchone()[0], self.ao_leite)
            self.assertEqual(c.execute("SELECT count(*) FROM sabores_produto WHERE produto_id=?", (self.destino,)).fetchone()[0], 4)

    def test_conflitos_abortam_sem_alterar_dados(self):
        cenarios = (
            ("descricao", "UPDATE itens SET descricao_original='OUTRO CHOCOLATE' WHERE codigo='leite'"),
            ("marca", "UPDATE apresentacoes_produto SET marca_id=NULL WHERE produto_id=(SELECT id FROM produtos WHERE nome='Barra chocolate ao leite')"),
            ("tamanho", "UPDATE variacoes_produto SET quantidade='80' WHERE produto_id=(SELECT id FROM produtos WHERE nome='Barra diamante negro')"),
            ("sem_tamanho", "UPDATE itens SET variacao_id=NULL WHERE codigo='diamante'"),
            ("sabor", "UPDATE itens SET sabor_id=(SELECT id FROM sabores_produto WHERE nome='Amaro') WHERE codigo='diamante'"),
            ("sem_destino", "UPDATE produtos SET nome='Outro chocolate' WHERE nome='Barra de Chocolate'"),
            ("destino_ambiguo", "INSERT INTO produtos(id,nome,categoria_id,nao_solicitar_marca,nao_solicitar_sabor,tratar_apenas_como_unidades,contem_variacoes,unidade_medida) SELECT 'duplicado',nome,(SELECT id FROM categorias WHERE nome='Doces'),0,0,0,1,'G' FROM produtos WHERE nome='Barra de Chocolate'"),
        )
        for nome, sql in cenarios:
            with self.subTest(cenario=nome):
                self.caminho = Path(self.temporario.name) / f"{nome}.sqlite3"
                BancoSQLite.migrar(self.caminho, "0009")
                self.popular()
                with self.conectar() as c:
                    c.execute(sql)
                    c.commit()
                antes = self.snapshot()
                with self.assertRaises(ErroPersistencia):
                    BancoSQLite.migrar(self.caminho, "0010")
                self.assertEqual(self.snapshot(), antes)

    def test_falha_de_escrita_reverte_categoria_preferencias_e_sabores(self):
        self.popular()
        with self.conectar() as c:
            c.execute("CREATE TRIGGER falha BEFORE INSERT ON sabores_produto BEGIN SELECT RAISE(ABORT,'falha simulada'); END")
            c.commit()
        antes = self.snapshot()
        with self.assertRaisesRegex(ErroPersistencia, "falha simulada"):
            BancoSQLite.migrar(self.caminho, "0010")
        self.assertEqual(self.snapshot(), antes)
