BEGIN IMMEDIATE;

ALTER TABLE notas ADD COLUMN importada_em TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_categorias_nome
    ON categorias(nome COLLATE NOCASE);
CREATE UNIQUE INDEX IF NOT EXISTS idx_marcas_nome
    ON marcas(nome COLLATE NOCASE);
CREATE UNIQUE INDEX IF NOT EXISTS idx_produtos_identidade
    ON produtos(nome COLLATE NOCASE, categoria_id, unidade_base);

CREATE TABLE associacoes_produto (
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

CREATE INDEX idx_associacoes_descricao
    ON associacoes_produto(descricao_normalizada);

PRAGMA user_version = 2;
COMMIT;
