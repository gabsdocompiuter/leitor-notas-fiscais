"""Consolida bebidas e classifica os sabores do catálogo existente.

A reversão exige restaurar o backup anterior à migração.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


@dataclass(frozen=True)
class Regra:
    descricao: str
    sabor: str
    quantidade: str
    unidade: str
    marca: str | None = None
    marcas_anteriores: tuple[str | None, ...] = (None,)


@dataclass(frozen=True)
class Grupo:
    nome: str
    origens: tuple[str, ...]
    categorias: tuple[str, ...]
    regras: tuple[Regra, ...]
    bebida: bool = True
    solicitar_marca: bool = False


GRUPOS = (
    Grupo("Coca-Cola", ("Coca-Cola", "Coca-Cola café"), ("Refrigerantes", "Bebidas"), (
        Regra("REFRIGERANTE COCA COLA 600ml ZERO", "Zero", "600", "ML"),
        Regra("REFRIGERANTE COCA COLA ZERO PET 600ML", "Zero", "600", "ML"),
        Regra("REFRIG COCA COLA 2L S AC", "Zero", "2", "L"),
        Regra("REFRI COCA COLA CAFE LT 220ml", "Café", "220", "ML"),
        Regra("REFRIGERANTE COCA COLA PLUS CAFE ESPRESS", "Café", "220", "ML"),
    )),
    Grupo("Pepsi", ("Pepsi", "Pepsi Twist"), ("Refrigerantes", "Bebidas"), (
        Regra("REFRIGERANTE PEPSI ZERO 350ML", "Zero", "350", "ML"),
        Regra("REFRI PEPSI TWIST LT 350ml", "Twist", "350", "ML"),
    )),
    Grupo("Fanta", ("Fanta Laranja", "Fanta"), ("Refrigerantes", "Bebidas"), (
        Regra("REFRI FANTA LAR ZERO LT 350ml", "Laranja Zero", "350", "ML"),
    )),
    Grupo("Fruki", ("Refri Fruki Guaraná Bergamota", "Fruki"), ("Refrigerantes", "Bebidas"), (
        Regra("REFRI FRUKI GUARANA BERGA ZERO LT 350ml", "Guaraná com Bergamota Zero", "350", "ML"),
    )),
    Grupo("Guaraná Antarctica", ("Guaraná Antarctica",), ("Refrigerantes", "Bebidas"), (
        Regra("REFRI ANTAR GUARANA ZERO FIBRAS LT 350ml", "Zero com Fibras", "350", "ML"),
    )),
    Grupo("Energético", ("Energético", "Energético Baly Banana"), ("Energético", "Bebidas"), (
        Regra("ENERG ELEV ZERO", "Zero", "473", "ML", "Elev", ("Elev",)),
        Regra("ENERG ELEV 473ML", "Pink Limonade", "473", "ML", "Elev", ("Elev",)),
        Regra("ENERG RED HORSE UVA VERDE ZERO 473ML", "Uva Verde Zero", "473", "ML", "Red Horse", ("Red Horse",)),
        Regra("ENERGETICO BALY PRO 250ML BANANA 15G PR", "Banana", "250", "ML", "Baly", (None, "Baly")),
    ), solicitar_marca=True),
    Grupo("Barra de Chocolate", ("Barra de Chocolate",), ("Alimentação",), (
        Regra("CHOC LACTA AMARO FAMILIA 40% 145g", "Amaro", "145", "G", "Lacta", ("Amaro", "Lacta")),
        Regra("CHOCOLATE LACTA 145g AMARO", "Amaro", "145", "G", "Lacta", ("Amaro", "Lacta")),
        Regra("CHOC LACTA SHOT FAMILIA 145g", "Shot", "145", "G", "Lacta", ("Lacta Shot", "Lacta")),
    ), bebida=False),
    Grupo("Café", ("Café",), ("Alimentação",), (
        Regra("CAFE PO MELITTA REGIOES BRASIL.250g MOGIANA", "Mogiana", "250", "G", "Melitta", ("Melitta",)),
        Regra("CAFE PO 3 CORACOES GOURMET 250g SUL DE MINAS", "Sul de Minas", "250", "G", "Três Corações", ("Três Corações",)),
        Regra("CAFE SOLUVEL LOR 130g CLASSIQUE VD", "Classique", "130", "G", "Lor", ("Lor",)),
    ), bebida=False),
    Grupo("Salgadinho", ("Salgadinho",), ("Larica",), (
        Regra("SALGADINHO MILHO LOBITS CEBOLA 200G", "Cebola", "200", "G", "Lobits", ("Lobits",)),
    ), bebida=False),
)


def _nome(valor):
    return " ".join(valor.split()).casefold() if valor is not None else None


def _linhas(conexao, tabela):
    # Nomes de tabelas são constantes locais, nunca entradas externas.
    return [dict(linha) for linha in conexao.execute(sa.text(f"SELECT * FROM {tabela}")).mappings()]


def _executar(conexao, sql, **valores):
    return conexao.execute(sa.text(sql), valores)


def _falhar(mensagem):
    raise RuntimeError(f"Migration 0009: {mensagem}. Nenhum dado deve ser migrado parcialmente.")


def _decimal(valor):
    try:
        numero = Decimal(valor)
        if not numero.is_finite() or numero <= 0:
            raise ValueError()
        return numero
    except (InvalidOperation, ValueError, TypeError):
        _falhar(f"quantidade de embalagem inválida: {valor!r}")


def _validar(conexao):
    dados = {t: _linhas(conexao, t) for t in (
        "categorias", "produtos", "marcas", "apresentacoes_produto",
        "variacoes_produto", "sabores_produto", "itens", "associacoes_produto",
    )}
    if conexao.exec_driver_sql("PRAGMA foreign_key_check").fetchall():
        _falhar("o banco já contém referências inválidas")
    categorias = {c["id"]: c["nome"] for c in dados["categorias"]}
    por_nome = {_nome(c["nome"]): c for c in dados["categorias"]}
    if "refrigerantes" in por_nome and "bebidas" in por_nome:
        _falhar("as categorias Refrigerantes e Bebidas já coexistem; é necessário reconciliá-las")
    grupos = []
    por_produto = {}
    for grupo in GRUPOS:
        fontes = [p for p in dados["produtos"] if _nome(p["nome"]) in {_nome(n) for n in grupo.origens}
                  and _nome(categorias[p["categoria_id"]]) in {_nome(n) for n in grupo.categorias}]
        if not fontes:
            continue
        canonicos = [p for p in fontes if _nome(p["nome"]) == _nome(grupo.nome)]
        if len(canonicos) > 1:
            _falhar(f"há mais de um destino para {grupo.nome}")
        destino = canonicos[0] if canonicos else fontes[0]
        for produto in fontes:
            if grupo.bebida:
                somente_unidades = produto["nome"] in ("Coca-Cola café", "Energético Baly Banana")
                if produto["tratar_apenas_como_unidades"] != somente_unidades or (
                    not somente_unidades and (not produto["contem_variacoes"] or produto["unidade_medida"] not in ("L", "ML"))
                ):
                    _falhar(f"estrutura incompatível no produto {produto['nome']}")
            por_produto[produto["id"]] = grupo
        grupos.append((grupo, fontes, destino))
    categoria_energia = por_nome.get(_nome("Energético"))
    if categoria_energia and any(p["categoria_id"] == categoria_energia["id"] and p["id"] not in por_produto
                                 for p in dados["produtos"]):
        _falhar("há produtos não previstos na categoria Energético")
    apresentacoes = {a["id"]: a for a in dados["apresentacoes_produto"]}
    tamanhos = {v["id"]: v for v in dados["variacoes_produto"]}
    sabores = {s["id"]: s for s in dados["sabores_produto"]}
    marcas = {m["id"]: m["nome"] for m in dados["marcas"]}
    produtos = {p["id"]: p for p in dados["produtos"]}
    planos = []
    for tabela in ("itens", "associacoes_produto"):
        for linha in dados[tabela]:
            apresentacao = apresentacoes.get(linha["apresentacao_id"])
            produto_id = apresentacao["produto_id"] if apresentacao else None
            tamanho = tamanhos.get(linha["variacao_id"])
            sabor = sabores.get(linha["sabor_id"])
            if produto_id not in por_produto:
                if any(v and v["produto_id"] in por_produto for v in (tamanho, sabor)):
                    _falhar(f"vínculo de produto inconsistente em {tabela}/{linha['id']}")
                continue
            grupo = por_produto[produto_id]
            regra = next((r for r in grupo.regras if _nome(r.descricao) == _nome(linha["descricao_original"])), None)
            if regra is None:
                _falhar(f"descrição desconhecida em {tabela}/{linha['id']}: {linha['descricao_original']!r}")
            if _nome(marcas.get(apresentacao["marca_id"])) not in {_nome(m) for m in regra.marcas_anteriores}:
                _falhar(f"marca conflitante em {tabela}/{linha['id']}")
            if sabor and (sabor["produto_id"] != produto_id or _nome(sabor["nome"]) != _nome(regra.sabor)):
                _falhar(f"sabor conflitante em {tabela}/{linha['id']}")
            if tamanho:
                if (tamanho["produto_id"] != produto_id or tamanho["unidade_medida"] != regra.unidade
                        or _decimal(tamanho["quantidade"]) != Decimal(regra.quantidade)):
                    _falhar(f"tamanho conflitante em {tabela}/{linha['id']}")
            elif not produtos[produto_id]["tratar_apenas_como_unidades"]:
                _falhar(f"tamanho ausente em {tabela}/{linha['id']}")
            planos.append((tabela, linha, grupo, regra))
    for grupo, fontes, destino in grupos:
        ids = {p["id"] for p in fontes}
        for tamanho in dados["variacoes_produto"]:
            if tamanho["produto_id"] in ids:
                _decimal(tamanho["quantidade"])
                if grupo.bebida and tamanho["unidade_medida"] not in ("L", "ML"):
                    _falhar(f"tamanho incompatível em {grupo.nome}")
        for sabor in dados["sabores_produto"]:
            if sabor["produto_id"] in ids - {destino["id"]} and _nome(sabor["nome"]) not in {_nome(r.sabor) for r in grupo.regras}:
                _falhar(f"sabor não previsto no cadastro incorporado de {grupo.nome}")
    return dados, grupos, planos


def _sabor(conexao, produto_id, nome):
    existente = _executar(conexao, "SELECT id FROM sabores_produto WHERE produto_id=:produto AND nome=:nome",
                         produto=produto_id, nome=nome).scalar()
    if existente:
        return existente
    identificador = uuid4().hex
    _executar(conexao, "INSERT INTO sabores_produto(id, produto_id, nome) VALUES (:id, :produto, :nome)",
              id=identificador, produto=produto_id, nome=nome)
    return identificador


def _marca(conexao, nome):
    if nome is None:
        return None
    existente = _executar(conexao, "SELECT id FROM marcas WHERE nome=:nome", nome=nome).scalar()
    if existente:
        return existente
    identificador = uuid4().hex
    _executar(conexao, "INSERT INTO marcas(id, nome) VALUES (:id, :nome)", id=identificador, nome=nome)
    return identificador


def _apresentacao(conexao, produto_id, marca_id):
    existente = _executar(conexao, "SELECT id FROM apresentacoes_produto WHERE produto_id=:produto AND marca_id IS :marca ORDER BY id",
                         produto=produto_id, marca=marca_id).scalar()
    if existente:
        return existente
    identificador = uuid4().hex
    _executar(conexao, "INSERT INTO apresentacoes_produto(id, produto_id, marca_id) VALUES (:id, :produto, :marca)",
              id=identificador, produto=produto_id, marca=marca_id)
    return identificador


def _migrar(conexao, dados, grupos, planos):
    _executar(conexao, "UPDATE produtos SET nao_solicitar_sabor=1")
    categoria_bebidas = next((c for c in dados["categorias"] if _nome(c["nome"]) in ("refrigerantes", "bebidas")), None)
    if any(g.bebida for g, _, _ in grupos):
        if categoria_bebidas is None:
            categoria_bebidas = {"id": uuid4().hex}
            _executar(conexao, "INSERT INTO categorias(id, nome) VALUES (:id, 'Bebidas')", id=categoria_bebidas["id"])
    if categoria_bebidas:
        _executar(conexao, "UPDATE categorias SET nome='Bebidas' WHERE id=:id", id=categoria_bebidas["id"])
    destinos = {}
    tamanhos_destino = {}
    incorporados = set()
    for grupo, fontes, destino in grupos:
        produto_id = destino["id"]
        destinos[grupo.nome] = produto_id
        ids = {p["id"] for p in fontes}
        incorporados.update(ids - {produto_id})
        _executar(conexao, "UPDATE produtos SET nome=:nome, nao_solicitar_sabor=0 WHERE id=:id", nome=grupo.nome, id=produto_id)
        if grupo.bebida:
            _executar(conexao, "UPDATE produtos SET categoria_id=:categoria, nao_solicitar_marca=:sem_marca, "
                      "tratar_apenas_como_unidades=0, contem_variacoes=1, unidade_medida='L' WHERE id=:id",
                      categoria=categoria_bebidas["id"], sem_marca=not grupo.solicitar_marca, id=produto_id)
        # O tamanho do destino tem prioridade; equivalentes dos produtos incorporados serão removidos.
        tamanhos = sorted((v for v in dados["variacoes_produto"] if v["produto_id"] in ids),
                          key=lambda v: (v["produto_id"] != produto_id, v["id"]))
        indice = {}
        for tamanho in tamanhos:
            chave = (_decimal(tamanho["quantidade"]), tamanho["unidade_medida"])
            if chave not in indice:
                indice[chave] = tamanho["id"]
                _executar(conexao, "UPDATE variacoes_produto SET produto_id=:produto WHERE id=:id", produto=produto_id, id=tamanho["id"])
        for regra in grupo.regras:
            _sabor(conexao, produto_id, regra.sabor)
            chave = (Decimal(regra.quantidade), regra.unidade)
            if chave not in indice:
                indice[chave] = uuid4().hex
                _executar(conexao, "INSERT INTO variacoes_produto(id, produto_id, quantidade, unidade_medida) "
                          "VALUES (:id, :produto, :quantidade, :unidade)", id=indice[chave], produto=produto_id,
                          quantidade=regra.quantidade, unidade=regra.unidade)
        tamanhos_destino[grupo.nome] = indice
    for tabela, linha, grupo, regra in planos:
        produto_id = destinos[grupo.nome]
        apresentacao_id = _apresentacao(conexao, produto_id, _marca(conexao, regra.marca))
        sabor_id = _sabor(conexao, produto_id, regra.sabor)
        tamanho_id = tamanhos_destino[grupo.nome][(Decimal(regra.quantidade), regra.unidade)]
        _executar(conexao, f"UPDATE {tabela} SET apresentacao_id=:apresentacao, sabor_id=:sabor, variacao_id=:tamanho WHERE id=:id",
                  apresentacao=apresentacao_id, sabor=sabor_id, tamanho=tamanho_id, id=linha["id"])
    for produto_id in incorporados:
        for tabela in ("apresentacoes_produto", "variacoes_produto", "sabores_produto"):
            _executar(conexao, f"DELETE FROM {tabela} WHERE produto_id=:produto", produto=produto_id)
        _executar(conexao, "DELETE FROM produtos WHERE id=:id", id=produto_id)
    categoria_energia = next((c for c in dados["categorias"] if _nome(c["nome"]) == _nome("Energético")), None)
    if categoria_energia:
        if _executar(conexao, "SELECT count(*) FROM produtos WHERE categoria_id=:id", id=categoria_energia["id"]).scalar():
            _falhar("a categoria Energético não ficou vazia")
        _executar(conexao, "DELETE FROM categorias WHERE id=:id", id=categoria_energia["id"])
    if conexao.exec_driver_sql("PRAGMA foreign_key_check").fetchall():
        _falhar("a verificação final encontrou referências inválidas")


def upgrade():
    conexao = op.get_bind()
    # SQLite pode adiar BEGIN até o primeiro DML. A reserva explícita protege a
    # leitura inicial e mantém dados e alembic_version na mesma transação real.
    if not conexao.connection.driver_connection.in_transaction:
        conexao.exec_driver_sql("BEGIN IMMEDIATE")
    with conexao.begin_nested():
        dados, grupos, planos = _validar(conexao)
        _migrar(conexao, dados, grupos, planos)


def downgrade():
    raise RuntimeError("A migration 0009 consolida cadastros e não possui downgrade. Restaure o backup anterior à migração.")
