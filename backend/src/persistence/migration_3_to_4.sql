PRAGMA foreign_keys = OFF;
BEGIN IMMEDIATE;

DELETE FROM leituras
WHERE nota_id IN (SELECT id FROM notas WHERE situacao <> 'lida');
DELETE FROM itens
WHERE nota_id IN (SELECT id FROM notas WHERE situacao <> 'lida');
DELETE FROM notas WHERE situacao <> 'lida';

DROP TABLE associacoes_produto;

UPDATE itens
SET apresentacao_id = NULL, revisado = 0;
DROP TABLE apresentacoes_produto;

ALTER TABLE produtos RENAME TO produtos_estrutura_3;

CREATE TABLE produtos (
    id TEXT PRIMARY KEY NOT NULL,
    nome TEXT NOT NULL,
    categoria_id TEXT NOT NULL REFERENCES categorias(id),
    nao_solicitar_marca INTEGER NOT NULL DEFAULT 0 CHECK (nao_solicitar_marca IN (0, 1)),
    tratar_apenas_como_unidades INTEGER NOT NULL DEFAULT 0 CHECK (tratar_apenas_como_unidades IN (0, 1)),
    contem_variacoes INTEGER NOT NULL DEFAULT 0 CHECK (contem_variacoes IN (0, 1)),
    unidade_medida TEXT CHECK (unidade_medida IN ('KG', 'G', 'L', 'ML')),
    CHECK (
        (tratar_apenas_como_unidades = 1 AND contem_variacoes = 0 AND unidade_medida IS NULL)
        OR (tratar_apenas_como_unidades = 0 AND unidade_medida IS NOT NULL)
    ),
    UNIQUE(nome, categoria_id)
);

INSERT INTO produtos (
    id, nome, categoria_id, nao_solicitar_marca,
    tratar_apenas_como_unidades, contem_variacoes, unidade_medida
)
SELECT
    id, nome, categoria_id, nao_solicitar_marca,
    CASE WHEN unidade_base = 'UN' THEN 1 ELSE 0 END,
    0,
    CASE WHEN unidade_base = 'UN' THEN NULL ELSE unidade_base END
FROM produtos_estrutura_3;

DROP TABLE produtos_estrutura_3;

CREATE UNIQUE INDEX idx_produtos_identidade
    ON produtos(nome COLLATE NOCASE, categoria_id);

CREATE TABLE apresentacoes_produto (
    id TEXT PRIMARY KEY NOT NULL,
    produto_id TEXT NOT NULL REFERENCES produtos(id),
    marca_id TEXT REFERENCES marcas(id)
);

CREATE TABLE variacoes_produto (
    id TEXT PRIMARY KEY NOT NULL,
    produto_id TEXT NOT NULL REFERENCES produtos(id),
    quantidade TEXT NOT NULL,
    unidade_medida TEXT NOT NULL CHECK (unidade_medida IN ('KG', 'G', 'L', 'ML')),
    descricao TEXT,
    UNIQUE(produto_id, quantidade, unidade_medida)
);

ALTER TABLE itens RENAME TO itens_estrutura_3;

CREATE TABLE itens (
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
    variacao_id TEXT REFERENCES variacoes_produto(id),
    quantidade_confirmada TEXT,
    revisado INTEGER NOT NULL CHECK (revisado IN (0, 1)),
    UNIQUE(nota_id, numero)
);

INSERT INTO itens (
    id, nota_id, numero, codigo, descricao_original, quantidade,
    unidade_original, valor_unitario, valor_total, alertas,
    apresentacao_id, variacao_id, quantidade_confirmada, revisado
)
SELECT
    id, nota_id, numero, codigo, descricao_original, quantidade,
    unidade_original, valor_unitario, valor_total, alertas,
    NULL, NULL, NULL, 0
FROM itens_estrutura_3;

DROP TABLE itens_estrutura_3;

CREATE TABLE associacoes_produto (
    id TEXT PRIMARY KEY NOT NULL,
    estabelecimento_id TEXT NOT NULL REFERENCES estabelecimentos(id),
    codigo_item TEXT NOT NULL,
    descricao_original TEXT NOT NULL,
    descricao_normalizada TEXT NOT NULL,
    apresentacao_id TEXT NOT NULL REFERENCES apresentacoes_produto(id),
    variacao_id TEXT REFERENCES variacoes_produto(id),
    fator_conversao TEXT NOT NULL,
    UNIQUE(estabelecimento_id, codigo_item)
);

CREATE INDEX idx_associacoes_descricao
    ON associacoes_produto(descricao_normalizada);

PRAGMA user_version = 4;
COMMIT;
PRAGMA foreign_keys = ON;
