BEGIN IMMEDIATE;

CREATE TABLE IF NOT EXISTS estabelecimentos (
    id TEXT PRIMARY KEY NOT NULL,
    cnpj TEXT NOT NULL UNIQUE,
    razao_social TEXT NOT NULL,
    apelido TEXT
);

CREATE TABLE IF NOT EXISTS categorias (
    id TEXT PRIMARY KEY NOT NULL,
    nome TEXT NOT NULL COLLATE NOCASE UNIQUE
);

CREATE TABLE IF NOT EXISTS marcas (
    id TEXT PRIMARY KEY NOT NULL,
    nome TEXT NOT NULL COLLATE NOCASE UNIQUE
);

CREATE TABLE IF NOT EXISTS produtos (
    id TEXT PRIMARY KEY NOT NULL,
    nome TEXT NOT NULL,
    categoria_id TEXT NOT NULL REFERENCES categorias(id),
    unidade_base TEXT NOT NULL CHECK (unidade_base IN ('UN', 'KG', 'G', 'L', 'ML')),
    nao_solicitar_marca INTEGER NOT NULL DEFAULT 0 CHECK (nao_solicitar_marca IN (0, 1)),
    UNIQUE(nome, categoria_id, unidade_base)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_produtos_identidade
    ON produtos(nome COLLATE NOCASE, categoria_id, unidade_base);

CREATE TABLE IF NOT EXISTS apresentacoes_produto (
    id TEXT PRIMARY KEY NOT NULL,
    produto_id TEXT NOT NULL REFERENCES produtos(id),
    marca_id TEXT REFERENCES marcas(id)
);

CREATE TABLE IF NOT EXISTS notas (
    id TEXT PRIMARY KEY NOT NULL,
    chave TEXT NOT NULL UNIQUE,
    numero TEXT NOT NULL,
    serie TEXT NOT NULL,
    estabelecimento_id TEXT NOT NULL REFERENCES estabelecimentos(id),
    emissao TEXT NOT NULL,
    quantidade_itens INTEGER NOT NULL CHECK (quantidade_itens > 0),
    valor_total TEXT NOT NULL,
    desconto TEXT NOT NULL,
    valor_a_pagar TEXT NOT NULL,
    url_origem TEXT NOT NULL,
    situacao TEXT NOT NULL CHECK (situacao IN ('lida', 'em_revisao', 'importada')),
    importada_em TEXT
);

CREATE INDEX IF NOT EXISTS idx_notas_emissao ON notas(emissao);

CREATE TABLE IF NOT EXISTS itens (
    id TEXT PRIMARY KEY NOT NULL,
    nota_id TEXT NOT NULL REFERENCES notas(id),
    numero INTEGER NOT NULL CHECK (numero > 0),
    codigo TEXT NOT NULL,
    descricao_original TEXT NOT NULL,
    quantidade TEXT NOT NULL,
    unidade_original TEXT NOT NULL,
    valor_unitario TEXT NOT NULL,
    valor_total TEXT NOT NULL,
    alertas TEXT NOT NULL,
    apresentacao_id TEXT REFERENCES apresentacoes_produto(id),
    unidade_corrigida TEXT CHECK (unidade_corrigida IN ('UN', 'KG', 'G', 'L', 'ML')),
    quantidade_normalizada TEXT,
    revisado INTEGER NOT NULL CHECK (revisado IN (0, 1)),
    UNIQUE(nota_id, numero)
);

CREATE TABLE IF NOT EXISTS leituras (
    id TEXT PRIMARY KEY NOT NULL,
    chave TEXT NOT NULL UNIQUE,
    url TEXT NOT NULL,
    nota_id TEXT REFERENCES notas(id),
    erro_consulta TEXT,
    criada_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS associacoes_produto (
    id TEXT PRIMARY KEY NOT NULL,
    estabelecimento_id TEXT NOT NULL REFERENCES estabelecimentos(id),
    codigo_item TEXT NOT NULL,
    descricao_original TEXT NOT NULL,
    descricao_normalizada TEXT NOT NULL,
    apresentacao_id TEXT NOT NULL REFERENCES apresentacoes_produto(id),
    unidade_corrigida TEXT NOT NULL CHECK (unidade_corrigida IN ('UN', 'KG', 'G', 'L', 'ML')),
    fator_normalizacao TEXT NOT NULL,
    UNIQUE(estabelecimento_id, codigo_item)
);

CREATE INDEX IF NOT EXISTS idx_associacoes_descricao
    ON associacoes_produto(descricao_normalizada);

PRAGMA user_version = 3;
COMMIT;
