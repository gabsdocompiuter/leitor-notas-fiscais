PRAGMA foreign_keys = OFF;
BEGIN IMMEDIATE;

ALTER TABLE produtos
    ADD COLUMN nao_solicitar_marca INTEGER NOT NULL DEFAULT 0
    CHECK (nao_solicitar_marca IN (0, 1));

-- Uma ausência de marca já confirmada representa a mesma decisão da nova flag.
UPDATE produtos
SET nao_solicitar_marca = 1
WHERE id IN (
    SELECT produto_id
    FROM apresentacoes_produto
    WHERE marca_id IS NULL AND marca_confirmada = 1
);

CREATE TABLE apresentacoes_produto_nova (
    id TEXT PRIMARY KEY NOT NULL,
    produto_id TEXT NOT NULL REFERENCES produtos(id),
    marca_id TEXT REFERENCES marcas(id)
);

INSERT INTO apresentacoes_produto_nova (id, produto_id, marca_id)
SELECT id, produto_id, marca_id
FROM apresentacoes_produto;

DROP TABLE apresentacoes_produto;
ALTER TABLE apresentacoes_produto_nova RENAME TO apresentacoes_produto;

PRAGMA user_version = 3;
COMMIT;
PRAGMA foreign_keys = ON;
