import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

from alembic import command

from src.core.persistence.banco_sqlite import BancoSQLite
from src.core.exceptions import ErroPersistencia
from src.enums.situacao_nota import SituacaoNota
from src.services.revisao_nota_service import RevisaoNotaService


# Casos independentes da implementação, reproduzindo as classificações aprovadas.
# origem, categoria, marca antiga, descrição, tamanho antigo, unidade, destino, sabor, marca final
CASOS = [
    ("Coca-Cola", "Refrigerantes", None, "REFRIGERANTE COCA COLA 600ml ZERO", "600", "ML", "Coca-Cola", "Zero", None),
    ("Coca-Cola", "Refrigerantes", None, "REFRIGERANTE COCA COLA 600ml ZERO", "600", "ML", "Coca-Cola", "Zero", None),
    ("Coca-Cola", "Refrigerantes", None, "REFRIGERANTE COCA COLA ZERO PET 600ML", "600", "ML", "Coca-Cola", "Zero", None),
    ("Coca-Cola", "Refrigerantes", None, "REFRIG COCA COLA 2L S AC", "2", "L", "Coca-Cola", "Zero", None),
    ("Coca-Cola café", "Refrigerantes", None, "REFRI COCA COLA CAFE LT 220ml", None, None, "Coca-Cola", "Café", None),
    ("Coca-Cola café", "Refrigerantes", None, "REFRIGERANTE COCA COLA PLUS CAFE ESPRESS", None, None, "Coca-Cola", "Café", None),
    ("Fanta Laranja", "Refrigerantes", None, "REFRI FANTA LAR ZERO LT 350ml", "350", "ML", "Fanta", "Laranja Zero", None),
    ("Guaraná Antarctica", "Refrigerantes", None, "REFRI ANTAR GUARANA ZERO FIBRAS LT 350ml", "350", "ML", "Guaraná Antarctica", "Zero com Fibras", None),
    ("Pepsi", "Refrigerantes", None, "REFRIGERANTE PEPSI ZERO 350ML", "350", "ML", "Pepsi", "Zero", None),
    ("Pepsi", "Refrigerantes", None, "REFRIGERANTE PEPSI ZERO 350ML", "350", "ML", "Pepsi", "Zero", None),
    ("Pepsi Twist", "Refrigerantes", None, "REFRI PEPSI TWIST LT 350ml", "350", "ML", "Pepsi", "Twist", None),
    ("Refri Fruki Guaraná Bergamota", "Refrigerantes", None, "REFRI FRUKI GUARANA BERGA ZERO LT 350ml", "350", "ML", "Fruki", "Guaraná com Bergamota Zero", None),
    ("Energético", "Energético", "Elev", "ENERG ELEV ZERO", "473", "ML", "Energético", "Zero", "Elev"),
    ("Energético", "Energético", "Elev", "ENERG ELEV 473ML", "473", "ML", "Energético", "Pink Limonade", "Elev"),
    ("Energético", "Energético", "Red Horse", "ENERG RED HORSE UVA VERDE ZERO 473ML", "473", "ML", "Energético", "Uva Verde Zero", "Red Horse"),
    ("Energético Baly Banana", "Energético", None, "ENERGETICO BALY PRO 250ML BANANA 15G PR", None, None, "Energético", "Banana", "Baly"),
    ("Barra de Chocolate", "Alimentação", "Amaro", "CHOC LACTA AMARO FAMILIA 40% 145g", "145", "G", "Barra de Chocolate", "Amaro", "Lacta"),
    ("Barra de Chocolate", "Alimentação", "Amaro", "CHOCOLATE LACTA 145g AMARO", "145", "G", "Barra de Chocolate", "Amaro", "Lacta"),
    ("Barra de Chocolate", "Alimentação", "Lacta Shot", "CHOC LACTA SHOT FAMILIA 145g", "145", "G", "Barra de Chocolate", "Shot", "Lacta"),
    ("Café", "Alimentação", "Melitta", "CAFE PO MELITTA REGIOES BRASIL.250g MOGIANA", "250", "G", "Café", "Mogiana", "Melitta"),
    ("Café", "Alimentação", "Três Corações", "CAFE PO 3 CORACOES GOURMET 250g SUL DE MINAS", "250", "G", "Café", "Sul de Minas", "Três Corações"),
    ("Café", "Alimentação", "Lor", "CAFE SOLUVEL LOR 130g CLASSIQUE VD", "130", "G", "Café", "Classique", "Lor"),
    ("Salgadinho", "Larica", "Lobits", "SALGADINHO MILHO LOBITS CEBOLA 200G", "200", "G", "Salgadinho", "Cebola", "Lobits"),
]


class MigracaoCatalogoTests(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        self.caminho = Path(self.temporario.name) / "catalogo.sqlite3"
        BancoSQLite.migrar(self.caminho, "0008")

    def conectar(self):
        conexao = sqlite3.connect(self.caminho)
        conexao.execute("PRAGMA foreign_keys=ON")
        conexao.row_factory = sqlite3.Row
        return closing(conexao)

    @staticmethod
    def inserir(conexao, tabela, **valores):
        identificador = valores.setdefault("id", uuid4().hex)
        colunas = ",".join(valores)
        parametros = ",".join("?" for _ in valores)
        conexao.execute(f"INSERT INTO {tabela} ({colunas}) VALUES ({parametros})", tuple(valores.values()))
        return identificador

    def popular(self):
        self.produtos = {}
        self.categorias = {}
        self.itens = []
        with self.conectar() as c:
            categorias = self.categorias
            for nome in ("Refrigerantes", "Energético", "Alimentação", "Larica", "Outros"):
                categorias[nome] = self.inserir(c, "categorias", nome=nome)
            loja = self.inserir(c, "estabelecimentos", cnpj="12345678000100", razao_social="Loja")
            self.loja = loja
            self.nota = self.inserir(c, "notas", chave="1" * 44, numero="1", serie="1", estabelecimento_id=loja,
                emissao="2026-09-20 12:00:00", quantidade_itens=23, valor_total="115.00", desconto="1.00",
                valor_a_pagar="114.00", url_origem="https://exemplo.invalid/nota", situacao="importada",
                importada_em="2026-09-21 12:00:00", considerar_proximo_mes=1, ignorada=0)
            marcas = {}
            apresentacoes = {}
            tamanhos = {}
            codigos = {}
            # Lacta já existe, mas ainda não é marca de Barra de Chocolate.
            marcas["Lacta"] = self.inserir(c, "marcas", nome="Lacta")
            for indice, caso in enumerate(CASOS, 1):
                origem, categoria, marca, descricao, tamanho, unidade, *_ = caso
                if origem not in self.produtos:
                    base = "L" if origem in ("Coca-Cola", "Energético") else ("KG" if origem == "Café" else unidade)
                    self.produtos[origem] = self.inserir(c, "produtos", nome=origem, categoria_id=categorias[categoria],
                        nao_solicitar_marca=marca is None, nao_solicitar_sabor=0,
                        tratar_apenas_como_unidades=tamanho is None, contem_variacoes=tamanho is not None, unidade_medida=base)
                if marca and marca not in marcas:
                    marcas[marca] = self.inserir(c, "marcas", nome=marca)
                identidade_ap = origem, marca
                if identidade_ap not in apresentacoes:
                    apresentacoes[identidade_ap] = self.inserir(c, "apresentacoes_produto", produto_id=self.produtos[origem], marca_id=marcas.get(marca))
                identidade_v = origem, tamanho, unidade
                if tamanho and identidade_v not in tamanhos:
                    tamanhos[identidade_v] = self.inserir(c, "variacoes_produto", produto_id=self.produtos[origem], quantidade=tamanho, unidade_medida=unidade)
                if descricao not in codigos:
                    codigos[descricao] = str(indice)
                    self.inserir(c, "associacoes_produto", estabelecimento_id=loja, codigo_item=str(indice),
                        descricao_original=descricao, descricao_normalizada=descricao.upper(),
                        apresentacao_id=apresentacoes[identidade_ap], variacao_id=tamanhos.get(identidade_v),
                        fator_conversao="1", unidades_por_pacote=None)
                self.itens.append(self.inserir(c, "itens", nota_id=self.nota, numero=indice, codigo=codigos[descricao],
                    descricao_original=descricao, quantidade="1", unidade_original="UN", valor_unitario="5.00", valor_total="5.00",
                    alertas="[]", apresentacao_id=apresentacoes[identidade_ap], variacao_id=tamanhos.get(identidade_v),
                    quantidade_confirmada="1.000", revisado=1, ignorado=0, quantidade_pacotes=None, unidades_por_pacote=None))
            for indice in range(118):
                self.inserir(c, "produtos", nome=f"Outro {indice}", categoria_id=categorias["Outros"],
                    nao_solicitar_marca=1, nao_solicitar_sabor=0, tratar_apenas_como_unidades=1, contem_variacoes=0, unidade_medida=None)
            tag = self.inserir(c, "tags", nome="Histórico", nome_normalizado="HISTORICO")
            c.execute("INSERT INTO itens_tags(item_id, tag_id) VALUES (?, ?)", (self.itens[0], tag))
            self.pendente = self.inserir(c, "itens", nota_id=self.nota, numero=24, codigo="pendente", descricao_original="REFRIGERANTE LANCH LATA 350ml",
                quantidade="1", unidade_original="UN", valor_unitario="5.00", valor_total="5.00", alertas="[]", revisado=0, ignorado=1)
            c.commit()

    def snapshot(self):
        with self.conectar() as c:
            tabelas = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
            return {t: [dict(r) for r in c.execute(f"SELECT * FROM {t} ORDER BY 1")] for t in tabelas}

    def test_mapeamentos_totais_historico_reuso_e_classificacao_automatica(self):
        self.popular()
        antes = self.snapshot()
        BancoSQLite.migrar(self.caminho, "0009")
        depois = self.snapshot()
        self.assertEqual(len(depois["produtos"]), 127)
        self.assertEqual(sum(p["nao_solicitar_sabor"] for p in depois["produtos"]), 118)
        self.assertEqual(len(depois["sabores_produto"]), 17)
        self.assertEqual(sum(i["sabor_id"] is not None for i in depois["itens"]), 23)
        self.assertEqual(sum(a["sabor_id"] is not None for a in depois["associacoes_produto"]), 21)
        self.assertEqual(depois["notas"], antes["notas"])
        self.assertEqual(depois["itens_tags"], antes["itens_tags"])
        for tabela in ("itens", "associacoes_produto"):
            def historico(linhas):
                return [{k: v for k, v in linha.items() if k not in ("apresentacao_id", "variacao_id", "sabor_id")} for linha in linhas]
            self.assertEqual(historico(depois[tabela]), historico(antes[tabela]))
        with self.conectar() as c:
            self.assertEqual(c.execute("SELECT id FROM categorias WHERE nome='Bebidas'").fetchone()[0], self.categorias["Refrigerantes"])
            self.assertIsNone(c.execute("SELECT id FROM categorias WHERE nome='Energético'").fetchone())
            for indice, caso in enumerate(CASOS):
                *_, destino, sabor, marca = caso
                linha = c.execute("SELECT p.nome produto,s.nome sabor,m.nome marca,v.quantidade,v.unidade_medida,p.unidade_medida base "
                    "FROM itens i JOIN apresentacoes_produto ap ON ap.id=i.apresentacao_id JOIN produtos p ON p.id=ap.produto_id "
                    "JOIN sabores_produto s ON s.id=i.sabor_id LEFT JOIN marcas m ON m.id=ap.marca_id "
                    "JOIN variacoes_produto v ON v.id=i.variacao_id WHERE i.id=?", (self.itens[indice],)).fetchone()
                self.assertEqual((linha["produto"], linha["sabor"], linha["marca"]), (destino, sabor, marca))
                if indice < 16:
                    self.assertEqual(linha["base"], "L")
            self.assertEqual(c.execute("SELECT count(*) FROM variacoes_produto v JOIN produtos p ON p.id=v.produto_id WHERE p.nome='Pepsi'").fetchone()[0], 1)
            for nome in ("Coca-Cola", "Pepsi", "Guaraná Antarctica", "Energético"):
                self.assertEqual(c.execute("SELECT id FROM produtos WHERE nome=?", (nome,)).fetchone()[0], self.produtos[nome])
            for nome in ("Coca-Cola café", "Pepsi Twist", "Energético Baly Banana"):
                self.assertIsNone(c.execute("SELECT id FROM produtos WHERE nome=?", (nome,)).fetchone())
            self.assertEqual(c.execute("SELECT count(*) FROM marcas WHERE nome IN ('Amaro','Lacta Shot')").fetchone()[0], 2)
            self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])
        # Reexecutar a revisão 0009 é idempotente e não altera preferências de novos produtos.
        BancoSQLite.migrar(self.caminho, "0009")
        self.assertEqual(self.snapshot(), depois)
        with self.conectar() as c:
            novo = self.inserir(c, "produtos", nome="Novo produto", categoria_id=self.categorias["Outros"],
                nao_solicitar_marca=1, tratar_apenas_como_unidades=1, contem_variacoes=0, unidade_medida=None)
            c.commit()
            self.assertEqual(c.execute("SELECT nao_solicitar_sabor FROM produtos WHERE id=?", (novo,)).fetchone()[0], 0)
        banco = BancoSQLite(self.caminho)
        self.addCleanup(banco.fechar)
        from src.entities import ItemEntity, NotaEntity
        with banco.session_factory.begin() as session:
            nota = NotaEntity(chave="2" * 44, numero="2", serie="1", estabelecimento_id=UUID(self.loja),
                emissao=datetime(2026, 10, 1), quantidade_itens=1,
                valor_total=Decimal("5"), desconto=Decimal("0"), valor_a_pagar=Decimal("5"),
                situacao=SituacaoNota.LIDA)
            nota.itens.append(ItemEntity(numero=1, codigo="14", descricao_original="ENERG ELEV 473ML", quantidade=Decimal(1),
                unidade_original="UNID", valor_unitario=Decimal(5), valor_total=Decimal(5), alertas=[]))
            session.add(nota)
        resultado = RevisaoNotaService(banco.session_factory).aplicar_classificacoes_automaticas("2" * 44)
        self.assertEqual(resultado.itens[0].sabor.nome, "Pink Limonade")
        self.assertTrue(resultado.itens[0].revisado)

    def test_banco_vazio_e_downgrade_bloqueado(self):
        BancoSQLite.migrar(self.caminho, "0009")
        self.assertEqual(self.snapshot()["produtos"], [])
        self.assertEqual(self.snapshot()["categorias"], [])
        with self.assertRaisesRegex(RuntimeError, "backup"):
            command.downgrade(BancoSQLite.configuracao_migrations(self.caminho), "0008")
        self.assertEqual(self.snapshot()["alembic_version"], [{"version_num": "0009"}])

    def test_descricao_desconhecida_aborta_antes_de_alterar(self):
        self.popular()
        with self.conectar() as c:
            c.execute("UPDATE itens SET descricao_original='ENERG DESCONHECIDO' WHERE id=?", (self.itens[13],))
            c.commit()
        antes = self.snapshot()
        with self.assertRaisesRegex(ErroPersistencia, "descrição desconhecida"):
            BancoSQLite.migrar(self.caminho, "0009")
        self.assertEqual(self.snapshot(), antes)

    def test_erro_de_escrita_reverte_tambem_preferencias_e_categoria(self):
        self.popular()
        with self.conectar() as c:
            c.execute("CREATE TRIGGER falha BEFORE INSERT ON sabores_produto BEGIN SELECT RAISE(ABORT, 'falha simulada'); END")
            c.commit()
        antes = self.snapshot()
        with self.assertRaisesRegex(ErroPersistencia, "falha simulada"):
            BancoSQLite.migrar(self.caminho, "0009")
        self.assertEqual(self.snapshot(), antes)

    def test_sabor_tamanho_marca_e_categoria_conflitantes(self):
        self.popular()
        original = self.snapshot()
        mudancas = (
            ("UPDATE variacoes_produto SET quantidade='999' WHERE produto_id=?", (self.produtos["Pepsi Twist"],)),
            ("UPDATE apresentacoes_produto SET marca_id=NULL WHERE produto_id=?", (self.produtos["Energético"],)),
            ("INSERT INTO categorias(id,nome) VALUES (?, 'Bebidas')", (uuid4().hex,)),
        )
        for sql, parametros in mudancas:
            with self.subTest(sql=sql):
                with self.conectar() as c:
                    c.execute(sql, parametros)
                    c.commit()
                antes = self.snapshot()
                with self.assertRaises(ErroPersistencia):
                    BancoSQLite.migrar(self.caminho, "0009")
                self.assertEqual(self.snapshot(), antes)
                # Restaura somente os dados artificiais desta fixture.
                with self.conectar() as c:
                    if sql.startswith("UPDATE variacoes"):
                        c.execute("UPDATE variacoes_produto SET quantidade='350' WHERE produto_id=?", parametros)
                    elif sql.startswith("UPDATE apresentacoes"):
                        for linha in original["apresentacoes_produto"]:
                            c.execute("UPDATE apresentacoes_produto SET marca_id=? WHERE id=?", (linha["marca_id"], linha["id"]))
                    else:
                        c.execute("DELETE FROM categorias WHERE id=?", parametros)
                    c.commit()

    def test_reutiliza_destino_sabor_apresentacao_e_tamanho_existentes(self):
        self.popular()
        with self.conectar() as c:
            destino = self.inserir(c, "produtos", nome="Fanta", categoria_id=self.categorias["Refrigerantes"],
                nao_solicitar_marca=1, nao_solicitar_sabor=0, tratar_apenas_como_unidades=0, contem_variacoes=1, unidade_medida="L")
            sabor = self.inserir(c, "sabores_produto", produto_id=destino, nome="Laranja Zero")
            apresentacao = self.inserir(c, "apresentacoes_produto", produto_id=destino, marca_id=None)
            tamanho = self.inserir(c, "variacoes_produto", produto_id=destino, quantidade="350.000", unidade_medida="ML")
            c.commit()
        BancoSQLite.migrar(self.caminho, "0009")
        with self.conectar() as c:
            linha = c.execute("SELECT apresentacao_id,sabor_id,variacao_id FROM itens WHERE id=?", (self.itens[6],)).fetchone()
            self.assertEqual(tuple(linha), (apresentacao, sabor, tamanho))
            self.assertEqual(c.execute("SELECT count(*) FROM sabores_produto WHERE produto_id=?", (destino,)).fetchone()[0], 1)
            self.assertEqual(c.execute("SELECT count(*) FROM variacoes_produto WHERE produto_id=?", (destino,)).fetchone()[0], 1)
            self.assertIsNone(c.execute("SELECT id FROM produtos WHERE nome='Fanta Laranja'").fetchone())

    def test_sabor_existente_incompativel_nao_e_sobrescrito(self):
        self.popular()
        with self.conectar() as c:
            sabor = self.inserir(c, "sabores_produto", produto_id=self.produtos["Pepsi"], nome="Original")
            c.execute("UPDATE itens SET sabor_id=? WHERE id=?", (sabor, self.itens[8]))
            c.commit()
        antes = self.snapshot()
        with self.assertRaisesRegex(ErroPersistencia, "sabor conflitante"):
            BancoSQLite.migrar(self.caminho, "0009")
        self.assertEqual(self.snapshot(), antes)
