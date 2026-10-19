"""Separa sabores dos nomes e cadastra embalagens de sequilhos e óleo.

Reversão operacional pela restauração do backup anterior à migration.
"""
from decimal import Decimal, InvalidOperation
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None

# Origem, destino, sabor, descrição auditada, embalagem, unidade base, converter unidades.
CASOS = (
    ("Batata congelada (air fryer)", "Batata Congelada", "Air Fryer",
     "BATATA MCCAIN PALITO AIR FR PCT 600g", "600", "G", "KG", False),
    ("Biscoito Sequilhos", "Biscoito Sequilhos", "Maracujá",
     "BISCOITO SEQ.FERNANDES 200g MARAC. SGL", "200", "G", "G", True),
    ("Bis", "Bis", "Branco", "BIS LACTA WAFER LAKA BRANCO 1008G", "100.8", "G", "G", False),
    ("Cogumelo Shitake", "Cogumelos", "Shitake",
     "COGUMELO SHITAKE GRAEMBUENSE 200g", "200", "G", "G", False),
    ("Massa Talharim", "Macarrão", "Talharim",
     "MASSA CASEIRA COVOS ORQUIDEA 500g TALHARIM", "500", "G", "KG", False),
    ("Óleo Girassol", "Óleo de Cozinha", "Girassol",
     "OLEO GIRASSOL CBS 900ml", "900", "ML", "L", True),
)


def _nome(valor):
    return " ".join(valor.split()).casefold() if valor is not None else None


def _falhar(mensagem):
    raise RuntimeError(f"Migration 0012: {mensagem}. Migração interrompida sem alterações parciais.")


def _executar(conexao, sql, **valores):
    return conexao.execute(sa.text(sql), valores)


def _unico(linhas, nome, contexto):
    encontrados = [r for r in linhas if _nome(r["nome"]) == _nome(nome)]
    if len(encontrados) > 1:
        _falhar(f"há mais de um cadastro de {nome} em {contexto}")
    return encontrados[0] if encontrados else None


def _quantidade(valor, inteira=False):
    try:
        numero = Decimal(valor)
        if not numero.is_finite() or numero <= 0 or (inteira and numero != numero.to_integral_value()):
            raise ValueError()
        return numero
    except (InvalidOperation, ValueError, TypeError):
        _falhar(f"quantidade incompatível: {valor!r}")


def _validar(conexao):
    if conexao.exec_driver_sql("PRAGMA foreign_key_check").fetchall():
        _falhar("o banco contém referências inválidas")
    tabelas = ("produtos", "categorias", "apresentacoes_produto", "variacoes_produto",
               "sabores_produto", "itens", "associacoes_produto")
    dados = {t: [dict(r) for r in _executar(conexao, f"SELECT * FROM {t}").mappings()] for t in tabelas}
    categorias = {r["id"]: _nome(r["nome"]) for r in dados["categorias"]}
    apresentacoes = {r["id"]: r for r in dados["apresentacoes_produto"]}
    tamanhos = {r["id"]: r for r in dados["variacoes_produto"]}
    sabores = {r["id"]: r for r in dados["sabores_produto"]}
    planos = {}
    for caso in CASOS:
        origem, destino, sabor_nome, descricao, quantidade, unidade, base, converter = caso
        produto = _unico(dados["produtos"], origem, "produtos")
        if produto is None:
            continue
        outro = _unico(dados["produtos"], destino, "produtos")
        if outro is not None and outro["id"] != produto["id"]:
            _falhar(f"o nome de destino {destino} pertence a outro produto")
        produto_id = produto["id"]
        categoria = "doces" if origem == "Bis" else "alimentação"
        if categorias.get(produto["categoria_id"]) != categoria:
            _falhar(f"categoria inesperada para {origem}")
        apenas_unidades = (produto["tratar_apenas_como_unidades"] and not produto["contem_variacoes"]
                           and produto["unidade_medida"] is None)
        embalagens = (not produto["tratar_apenas_como_unidades"] and produto["contem_variacoes"]
                      and produto["unidade_medida"] == base)
        if not embalagens and not (converter and apenas_unidades):
            _falhar(f"configuração de medidas incompatível para {origem}")
        sabor = _unico([r for r in sabores.values() if r["produto_id"] == produto_id], sabor_nome, origem)
        candidatos = []
        for tamanho in tamanhos.values():
            if tamanho["produto_id"] != produto_id:
                continue
            valor = _quantidade(tamanho["quantidade"])
            if tamanho["unidade_medida"] != unidade:
                _falhar(f"unidade de embalagem incompatível para {origem}")
            if valor == Decimal(quantidade):
                candidatos.append(tamanho)
        candidatos.sort(key=lambda r: r["id"])
        planos[produto_id] = dict(caso=caso, sabor=sabor,
                                  tamanho=candidatos[0] if candidatos else None, linhas=[])

    # Também detecta referências a sabores/tamanhos destes produtos a partir de outro produto.
    for tabela in ("itens", "associacoes_produto"):
        for linha in dados[tabela]:
            apresentacao = apresentacoes.get(linha["apresentacao_id"])
            produto_id = apresentacao["produto_id"] if apresentacao else None
            for recurso in (tamanhos.get(linha["variacao_id"]), sabores.get(linha["sabor_id"])):
                if recurso and (produto_id in planos or recurso["produto_id"] in planos):
                    if recurso["produto_id"] != produto_id:
                        _falhar(f"vínculo de produto inconsistente em {tabela}/{linha['id']}")
            plano = planos.get(produto_id)
            if plano is None:
                continue
            origem, destino, sabor_nome, descricao, quantidade, unidade, base, converter = plano["caso"]
            if _nome(linha["descricao_original"]) != _nome(descricao):
                _falhar(f"descrição desconhecida em {tabela}/{linha['id']}: {linha['descricao_original']!r}")
            if linha["sabor_id"] is not None and _nome(sabores[linha["sabor_id"]]["nome"]) != _nome(sabor_nome):
                _falhar(f"sabor conflitante em {tabela}/{linha['id']}")
            tamanho = tamanhos.get(linha["variacao_id"])
            if tamanho is not None:
                if (tamanho["unidade_medida"] != unidade
                        or _quantidade(tamanho["quantidade"]) != Decimal(quantidade)):
                    _falhar(f"embalagem conflitante em {tabela}/{linha['id']}")
            elif not converter:
                _falhar(f"embalagem ausente em {tabela}/{linha['id']}")
            if converter:
                if linha["unidades_por_pacote"] is not None or (tabela == "itens" and linha["quantidade_pacotes"] is not None):
                    _falhar(f"pacotes incompatíveis em {tabela}/{linha['id']}")
                campo = "quantidade_confirmada" if tabela == "itens" else "fator_conversao"
                _quantidade(linha[campo], inteira=True)
            plano["linhas"].append((tabela, linha["id"]))
    return planos


def _migrar(conexao, planos):
    for produto_id, plano in planos.items():
        origem, destino, sabor_nome, descricao, quantidade, unidade, base, converter = plano["caso"]
        sabor_id = plano["sabor"]["id"] if plano["sabor"] else uuid4().hex
        if plano["sabor"] is None:
            _executar(conexao, "INSERT INTO sabores_produto(id,produto_id,nome) VALUES (:id,:produto,:nome)",
                      id=sabor_id, produto=produto_id, nome=sabor_nome)
        if converter:
            tamanho_id = plano["tamanho"]["id"] if plano["tamanho"] else uuid4().hex
            if plano["tamanho"] is None:
                _executar(conexao, "INSERT INTO variacoes_produto(id,produto_id,quantidade,unidade_medida) "
                          "VALUES (:id,:produto,:quantidade,:unidade)",
                          id=tamanho_id, produto=produto_id, quantidade=quantidade, unidade=unidade)
            _executar(conexao, "UPDATE produtos SET tratar_apenas_como_unidades=0,contem_variacoes=1,"
                      "unidade_medida=:base WHERE id=:id", base=base, id=produto_id)
        _executar(conexao, "UPDATE produtos SET nome=:nome,nao_solicitar_sabor=0 WHERE id=:id", nome=destino, id=produto_id)
        for tabela, identificador in plano["linhas"]:
            if converter:
                _executar(conexao, f"UPDATE {tabela} SET sabor_id=:sabor,variacao_id=:tamanho WHERE id=:id",
                          sabor=sabor_id, tamanho=tamanho_id, id=identificador)
            else:
                _executar(conexao, f"UPDATE {tabela} SET sabor_id=:sabor WHERE id=:id", sabor=sabor_id, id=identificador)
    if conexao.exec_driver_sql("PRAGMA foreign_key_check").fetchall():
        _falhar("a verificação final encontrou referências inválidas")


def upgrade():
    conexao = op.get_bind()
    if not conexao.connection.driver_connection.in_transaction:
        conexao.exec_driver_sql("BEGIN IMMEDIATE")
    with conexao.begin_nested():
        _migrar(conexao, _validar(conexao))


def downgrade():
    raise RuntimeError("A migration 0012 reorganiza produtos e sabores e não possui downgrade. Restaure o backup anterior à migração.")
