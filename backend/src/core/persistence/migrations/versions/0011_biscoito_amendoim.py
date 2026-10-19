"""Incorpora Biscoito de Amendoim ao produto Biscoito.

Reversão somente pela restauração do backup anterior à migration.
"""
from decimal import Decimal, InvalidOperation
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None

DESCRICAO = "BISCOITO PASETTO 250g AMENDOIM"


def _nome(valor):
    return " ".join(valor.split()).casefold() if valor is not None else None


def _falhar(mensagem):
    raise RuntimeError(f"Migration 0011: {mensagem}. A consolidação foi interrompida sem alterações parciais.")


def _executar(conexao, sql, **valores):
    return conexao.execute(sa.text(sql), valores)


def _unico(linhas, nome, contexto):
    encontrados = [r for r in linhas if _nome(r["nome"]) == _nome(nome)]
    if len(encontrados) > 1:
        _falhar(f"há mais de um cadastro de {nome} em {contexto}")
    return encontrados[0] if encontrados else None


def _quantidade(valor):
    try:
        numero = Decimal(valor)
        if not numero.is_finite() or numero <= 0:
            raise ValueError()
        return numero
    except (InvalidOperation, ValueError, TypeError):
        _falhar(f"quantidade inválida: {valor!r}")


def _validar(conexao):
    if conexao.exec_driver_sql("PRAGMA foreign_key_check").fetchall():
        _falhar("o banco contém referências inválidas")
    tabelas = ("produtos", "categorias", "marcas", "apresentacoes_produto", "variacoes_produto", "sabores_produto", "itens", "associacoes_produto")
    dados = {t: [dict(r) for r in _executar(conexao, f"SELECT * FROM {t}").mappings()] for t in tabelas}
    fonte = _unico(dados["produtos"], "Biscoito de Amendoim", "produtos")
    if fonte is None:
        return None
    destino = _unico(dados["produtos"], "Biscoito", "produtos")
    if destino is None:
        _falhar("não existe um destino inequívoco Biscoito")
    categorias = {c["id"]: _nome(c["nome"]) for c in dados["categorias"]}
    if fonte["categoria_id"] != destino["categoria_id"] or categorias[destino["categoria_id"]] != "alimentação":
        _falhar("origem e destino devem pertencer à mesma categoria Alimentação")
    if not fonte["tratar_apenas_como_unidades"] or fonte["contem_variacoes"] or fonte["unidade_medida"] is not None:
        _falhar("a origem não está configurada para contagem em unidades")
    if (destino["tratar_apenas_como_unidades"] or not destino["contem_variacoes"] or destino["unidade_medida"] != "G"
            or destino["nao_solicitar_marca"] or destino["nao_solicitar_sabor"]):
        _falhar("o destino deve solicitar marca, sabor e embalagem em gramas")
    marca = _unico(dados["marcas"], "Pasetto", "marcas")
    sabores_destino = [s for s in dados["sabores_produto"] if s["produto_id"] == destino["id"]]
    sabor_destino = _unico(sabores_destino, "Amendoim", "sabores do destino")
    apresentacoes = {a["id"]: a for a in dados["apresentacoes_produto"]}
    tamanhos = {v["id"]: v for v in dados["variacoes_produto"]}
    sabores = {s["id"]: s for s in dados["sabores_produto"]}
    marcas = {m["id"]: _nome(m["nome"]) for m in dados["marcas"]}
    relacionados = {fonte["id"], destino["id"]}
    for ap in dados["apresentacoes_produto"]:
        if ap["produto_id"] == fonte["id"] and marcas.get(ap["marca_id"]) not in (None, "pasetto"):
            _falhar("marca conflitante no cadastro da origem")
    for tamanho in dados["variacoes_produto"]:
        if tamanho["produto_id"] == fonte["id"]:
            _falhar("há embalagens inesperadas na origem tratada como unidades")
        if tamanho["produto_id"] == destino["id"]:
            _quantidade(tamanho["quantidade"])
            if tamanho["unidade_medida"] != "G":
                _falhar("há uma embalagem incompatível no destino")
    for sabor in dados["sabores_produto"]:
        if sabor["produto_id"] == fonte["id"] and _nome(sabor["nome"]) != "amendoim":
            _falhar("sabor conflitante no cadastro da origem")
    planos = []
    for tabela in ("itens", "associacoes_produto"):
        for linha in dados[tabela]:
            ap = apresentacoes.get(linha["apresentacao_id"])
            produto_id = ap["produto_id"] if ap else None
            for recurso in (tamanhos.get(linha["variacao_id"]), sabores.get(linha["sabor_id"])):
                if recurso and (produto_id in relacionados or recurso["produto_id"] in relacionados) and recurso["produto_id"] != produto_id:
                    _falhar(f"vínculo de produto inconsistente em {tabela}/{linha['id']}")
            if produto_id != fonte["id"]:
                continue
            if _nome(linha["descricao_original"]) != _nome(DESCRICAO):
                _falhar(f"descrição desconhecida em {tabela}/{linha['id']}: {linha['descricao_original']!r}")
            if linha["unidades_por_pacote"] is not None or (tabela == "itens" and linha["quantidade_pacotes"] is not None):
                _falhar(f"há pacotes incompatíveis com o destino em {tabela}/{linha['id']}")
            if tabela == "itens" and linha["quantidade_confirmada"] is not None:
                quantidade = _quantidade(linha["quantidade_confirmada"])
                if quantidade != quantidade.to_integral_value():
                    _falhar(f"quantidade de embalagens fracionária em {tabela}/{linha['id']}")
            planos.append((tabela, linha["id"]))
    return dados, fonte, destino, marca, sabor_destino, planos


def _migrar(conexao, contexto):
    if contexto is None:
        return
    dados, fonte, destino, marca, sabor, planos = contexto
    produto_id = destino["id"]
    sabor_id = sabor["id"] if sabor else uuid4().hex
    if sabor is None:
        _executar(conexao, "INSERT INTO sabores_produto(id, produto_id, nome) VALUES (:id, :produto, 'Amendoim')",
                  id=sabor_id, produto=produto_id)
    marca_id = marca["id"] if marca else uuid4().hex
    if marca is None:
        _executar(conexao, "INSERT INTO marcas(id, nome) VALUES (:id, 'Pasetto')", id=marca_id)
    apresentacao_id = _executar(conexao, "SELECT id FROM apresentacoes_produto WHERE produto_id=:produto AND marca_id=:marca ORDER BY id",
                               produto=produto_id, marca=marca_id).scalar()
    if apresentacao_id is None:
        apresentacao_id = uuid4().hex
        _executar(conexao, "INSERT INTO apresentacoes_produto(id, produto_id, marca_id) VALUES (:id, :produto, :marca)",
                  id=apresentacao_id, produto=produto_id, marca=marca_id)
    tamanhos = sorted((v for v in dados["variacoes_produto"] if v["produto_id"] == produto_id
                       and _quantidade(v["quantidade"]) == Decimal(250)), key=lambda v: v["id"])
    tamanho_id = tamanhos[0]["id"] if tamanhos else uuid4().hex
    if not tamanhos:
        _executar(conexao, "INSERT INTO variacoes_produto(id, produto_id, quantidade, unidade_medida) VALUES (:id, :produto, '250', 'G')",
                  id=tamanho_id, produto=produto_id)
    for tabela, identificador in planos:
        _executar(conexao, f"UPDATE {tabela} SET apresentacao_id=:apresentacao, variacao_id=:tamanho, sabor_id=:sabor WHERE id=:id",
                  apresentacao=apresentacao_id, tamanho=tamanho_id, sabor=sabor_id, id=identificador)
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
    raise RuntimeError("A migration 0011 consolida cadastros e não possui downgrade. Restaure o backup anterior à migração.")
