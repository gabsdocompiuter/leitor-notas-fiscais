"""Consolida barras de chocolate e transfere o produto para Doces.

Reversão somente pela restauração do backup anterior à migration.
"""
from decimal import Decimal, InvalidOperation
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None

ORIGENS = {
    "barra chocolate ao leite": ("Ao leite", "CHOC LACTA 145G LEIT TAM FAMILIA", ("lacta",)),
    "barra diamante negro": ("Diamante Negro", "CHOC LACTA 145G DIAM NEGRO TAM FAMILIA", (None, "lacta")),
}


def _nome(valor):
    return " ".join(valor.split()).casefold() if valor is not None else None


def _falhar(mensagem):
    raise RuntimeError(f"Migration 0010: {mensagem}. A consolidação foi interrompida sem alterações parciais.")


def _executar(conexao, sql, **valores):
    return conexao.execute(sa.text(sql), valores)


def _quantidade(valor):
    try:
        numero = Decimal(valor)
        if not numero.is_finite() or numero <= 0:
            raise ValueError()
        return numero
    except (InvalidOperation, ValueError, TypeError):
        _falhar(f"quantidade de embalagem inválida: {valor!r}")


def _unico(linhas, nome, contexto):
    encontrados = [r for r in linhas if _nome(r["nome"]) == _nome(nome)]
    if len(encontrados) > 1:
        _falhar(f"há mais de um cadastro de {nome} em {contexto}")
    return encontrados[0] if encontrados else None


def _validar(conexao):
    if conexao.exec_driver_sql("PRAGMA foreign_key_check").fetchall():
        _falhar("o banco contém referências inválidas")
    tabelas = ("produtos", "categorias", "marcas", "apresentacoes_produto", "variacoes_produto", "sabores_produto", "itens", "associacoes_produto")
    dados = {t: [dict(r) for r in _executar(conexao, f"SELECT * FROM {t}").mappings()] for t in tabelas}
    destino = _unico(dados["produtos"], "Barra de Chocolate", "produtos")
    fontes = [p for nome in ORIGENS if (p := _unico(dados["produtos"], nome, "produtos")) is not None]
    if destino is None:
        if fontes:
            _falhar("não existe um destino inequívoco Barra de Chocolate")
        return None
    doces = _unico(dados["categorias"], "Doces", "categorias")
    lacta = _unico(dados["marcas"], "Lacta", "marcas")
    categorias = {r["id"]: _nome(r["nome"]) for r in dados["categorias"]}
    for produto in [destino, *fontes]:
        if produto["tratar_apenas_como_unidades"] or not produto["contem_variacoes"] or produto["unidade_medida"] != "G":
            _falhar(f"estrutura incompatível no produto {produto['nome']}")
        permitidas = ("alimentação", "doces") if produto is destino else ("doces",)
        if categorias[produto["categoria_id"]] not in permitidas:
            _falhar(f"categoria inesperada no produto {produto['nome']}")
    fontes_por_id = {p["id"]: p for p in fontes}
    relacionados = {*fontes_por_id, destino["id"]}
    apresentacoes = {r["id"]: r for r in dados["apresentacoes_produto"]}
    tamanhos = {r["id"]: r for r in dados["variacoes_produto"]}
    sabores = {r["id"]: r for r in dados["sabores_produto"]}
    marcas = {r["id"]: _nome(r["nome"]) for r in dados["marcas"]}
    for ap in dados["apresentacoes_produto"]:
        if ap["produto_id"] in fontes_por_id:
            regra = ORIGENS[_nome(fontes_por_id[ap["produto_id"]]["nome"])]
            if marcas.get(ap["marca_id"]) not in regra[2]:
                _falhar("marca conflitante no cadastro de uma origem")
    for tamanho in dados["variacoes_produto"]:
        produto_id = tamanho["produto_id"]
        if produto_id not in relacionados:
            continue
        quantidade = _quantidade(tamanho["quantidade"])
        if tamanho["unidade_medida"] != "G" or (produto_id in fontes_por_id and quantidade != Decimal(145)):
            _falhar("tamanho de embalagem incompatível")
    for sabor in dados["sabores_produto"]:
        if sabor["produto_id"] in fontes_por_id:
            esperado = ORIGENS[_nome(fontes_por_id[sabor["produto_id"]]["nome"])][0]
            if _nome(sabor["nome"]) != _nome(esperado):
                _falhar("sabor conflitante no cadastro de uma origem")
    sabores_destino = [s for s in dados["sabores_produto"] if s["produto_id"] == destino["id"]]
    for nome in ("Ao leite", "Diamante Negro"):
        _unico(sabores_destino, nome, "sabores do destino")
    planos = []
    for tabela in ("itens", "associacoes_produto"):
        for linha in dados[tabela]:
            ap = apresentacoes.get(linha["apresentacao_id"])
            produto_id = ap["produto_id"] if ap else None
            tamanho = tamanhos.get(linha["variacao_id"])
            sabor = sabores.get(linha["sabor_id"])
            for recurso in (tamanho, sabor):
                if recurso and (produto_id in relacionados or recurso["produto_id"] in relacionados) and recurso["produto_id"] != produto_id:
                    _falhar(f"vínculo de produto inconsistente em {tabela}/{linha['id']}")
            if produto_id not in fontes_por_id:
                continue
            regra = ORIGENS[_nome(fontes_por_id[produto_id]["nome"])]
            if _nome(linha["descricao_original"]) != _nome(regra[1]):
                _falhar(f"descrição desconhecida em {tabela}/{linha['id']}: {linha['descricao_original']!r}")
            if tamanho is None:
                _falhar(f"tamanho ausente em {tabela}/{linha['id']}")
            if sabor and _nome(sabor["nome"]) != _nome(regra[0]):
                _falhar(f"sabor conflitante em {tabela}/{linha['id']}")
            planos.append((tabela, linha["id"], regra[0]))
    return dados, destino, fontes, doces, lacta, planos


def _criar_nome(conexao, tabela, nome):
    identificador = uuid4().hex
    _executar(conexao, f"INSERT INTO {tabela}(id, nome) VALUES (:id, :nome)", id=identificador, nome=nome)
    return identificador


def _migrar(conexao, contexto):
    if contexto is None:
        return
    dados, destino, fontes, doces, lacta, planos = contexto
    produto_id = destino["id"]
    categoria_id = doces["id"] if doces else _criar_nome(conexao, "categorias", "Doces")
    _executar(conexao, "UPDATE produtos SET categoria_id=:categoria, nao_solicitar_marca=0, nao_solicitar_sabor=0 WHERE id=:id",
              categoria=categoria_id, id=produto_id)
    sabores = {}
    existentes = [s for s in dados["sabores_produto"] if s["produto_id"] == produto_id]
    for nome in ("Ao leite", "Diamante Negro"):
        sabor = _unico(existentes, nome, "sabores do destino")
        identificador = sabor["id"] if sabor else uuid4().hex
        if sabor:
            _executar(conexao, "UPDATE sabores_produto SET nome=:nome WHERE id=:id", nome=nome, id=identificador)
        else:
            _executar(conexao, "INSERT INTO sabores_produto(id, produto_id, nome) VALUES (:id, :produto, :nome)",
                      id=identificador, produto=produto_id, nome=nome)
        sabores[nome] = identificador
    if fontes:
        marca_id = lacta["id"] if lacta else _criar_nome(conexao, "marcas", "Lacta")
        apresentacao_id = _executar(conexao, "SELECT id FROM apresentacoes_produto WHERE produto_id=:produto AND marca_id=:marca ORDER BY id",
                                   produto=produto_id, marca=marca_id).scalar()
        if apresentacao_id is None:
            apresentacao_id = uuid4().hex
            _executar(conexao, "INSERT INTO apresentacoes_produto(id, produto_id, marca_id) VALUES (:id, :produto, :marca)",
                      id=apresentacao_id, produto=produto_id, marca=marca_id)
        tamanhos = sorted((v for v in dados["variacoes_produto"] if v["produto_id"] == produto_id
                           and v["unidade_medida"] == "G" and _quantidade(v["quantidade"]) == Decimal(145)), key=lambda v: v["id"])
        tamanho_id = tamanhos[0]["id"] if tamanhos else uuid4().hex
        if not tamanhos:
            _executar(conexao, "INSERT INTO variacoes_produto(id, produto_id, quantidade, unidade_medida) VALUES (:id, :produto, '145', 'G')",
                      id=tamanho_id, produto=produto_id)
        for tabela, identificador, sabor in planos:
            _executar(conexao, f"UPDATE {tabela} SET apresentacao_id=:apresentacao, variacao_id=:tamanho, sabor_id=:sabor WHERE id=:id",
                      apresentacao=apresentacao_id, tamanho=tamanho_id, sabor=sabores[sabor], id=identificador)
        for fonte in fontes:
            for tabela in ("apresentacoes_produto", "variacoes_produto", "sabores_produto"):
                _executar(conexao, f"DELETE FROM {tabela} WHERE produto_id=:produto", produto=fonte["id"])
            _executar(conexao, "DELETE FROM produtos WHERE id=:id", id=fonte["id"])
    if conexao.exec_driver_sql("PRAGMA foreign_key_check").fetchall():
        _falhar("a verificação final encontrou referências inválidas")


def upgrade():
    conexao = op.get_bind()
    if not conexao.connection.driver_connection.in_transaction:
        conexao.exec_driver_sql("BEGIN IMMEDIATE")
    with conexao.begin_nested():
        _migrar(conexao, _validar(conexao))


def downgrade():
    raise RuntimeError("A migration 0010 consolida cadastros e não possui downgrade. Restaure o backup anterior à migração.")
