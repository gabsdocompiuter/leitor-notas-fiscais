# Changelog do backend

As versões só são alteradas por solicitação explícita do usuário.
Registre mudanças futuras em **Não lançado**, mantendo a versão vigente até
a autorização de uma nova versão.

## Não lançado

### Persistência SQLite e ordem dos campos

- `id` como primeiro campo de todas as entidades, mantendo geração automática
  de UUID e permitindo restauração com `id=...`.
- Gravação automática da nota consultada no SQLite, com estabelecimento, itens
  e dados relacionados de classificação, quando presentes.
- Captura da URL antes da consulta e registro de erros para nova tentativa.
- Transações, chaves estrangeiras e unicidade por chave da nota e CNPJ.
- Reconsulta preserva IDs, apelidos, situação e revisões existentes.
- Opção `--banco`, padrão `backend/data/notas.sqlite3`, e recuperação por chave.
- Testes de persistência, rollback, reabertura e ausência de duplicatas.

### Adicionado

- URL recebida por parâmetro em `consultar_nota(url)` e `extrair_nota(html, url)`.
- Opção `--url` na CLI, mantendo a nota de exemplo como padrão.
- Validação de QR Codes HTTPS dos endereços suportados do RS e da chave recebida.
- Entidades de estabelecimento (com apelido opcional), categoria, marca, produto,
  apresentação, associação por estabelecimento e leitura pendente.
- Identificadores UUID, unidades de medida e situações da nota.
- Campos de revisão separados dos dados originais de cada item.

### Alterado

- A nota contém `estabelecimento`, `url_origem` e emissão como `datetime`.
- JSON com objetos relacionados, UUIDs, emissão ISO e decimais como strings.
  `emitente` e `cnpj_emitente` foram substituídos pelo objeto `estabelecimento`.
- Exemplos e testes adaptados ao novo modelo de dados.

A versão permanece em **0.1.0**. As operações de edição/revisão e confirmação
da importação continuam pendentes; salvar a consulta mantém a nota como lida.

## 0.1.0 — 2026-09-09

### Adicionado

- Consulta da NFC-e do RS por URL fixa, com timeout e verificação TLS.
- Extração dos itens, emitente, emissão, identificação e totais da nota.
- Validação da chave, quantidade de itens, soma e desconto geral.
- Precisão decimal e exportação para JSON com situação `lida`.
- Leitura de HTML salvo e opção de salvar a resposta para diagnóstico.
- Alerta de divergência entre descrição em kg e unidade declarada.
- Testes de extração e validação sem acesso à rede.
- Ponto de entrada em `main.py` e módulos em `src/core`, `src/models`,
  `src/services` e `src/presentation`, com classes separadas.
- Fonte única de versão em `src/core/version.py` e comando `--version`.

A versão cobre a leitura inicial. Revisão, confirmação da importação, banco,
API e interface web ainda serão implementados.
