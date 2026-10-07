# Changelog do backend

As versões só são alteradas por solicitação explícita do usuário.

## Não lançado

- Edição de nome, categoria e exigência de marca em produtos utilizados, com proteção dos campos estruturais e retorno à revisão dos itens sem marca em notas não importadas.
- Consulta das restrições do produto e exclusão de produtos sem itens vinculados, com limpeza transacional de associações, apresentações e variações.

- Importação e exportação do SQLite, com permissão no backend, validação/migrations, backup anterior e substituição coordenada com recuperação de falhas.

- Sugestões de tags limitadas às cinco mais usadas por item, com desempate por nome e filtro a partir de três caracteres.

### Adicionado

- Recarga automática da API ao executar `python main.py`.

- Tags reutilizáveis por item, marcação em lote e opção de considerar notas no mês seguinte.
- Relatórios mensais de resumo, categorias e tags, com rateio proporcional de descontos em centavos e detalhes paginados.
- Migration `0003` preservando notas existentes.

- Modos de produto por unidade, a granel ou por variações de peso e volume.
- Cadastro de variações e catálogo descritivo de unidades de medida.
- Consulta e edição do apelido dos estabelecimentos.
- Flag `nao_solicitar_marca` no cadastro de produtos.
- Container do backend para execução pelo Docker Compose da raiz.
- Workspace local do Postman organizado por sistema, leituras e notas, com
  variáveis compartilhadas e todas as chamadas da API.
- CRUD de categorias, marcas e produtos.
- Revisão de itens com produto, marca confirmada, apresentação, unidade corrigida
  e quantidade normalizada.
- Associações reutilizáveis por estabelecimento e código interno do item.
- Classificação automática por associação específica ou descrição original
  normalizada sem conflitos.
- Confirmação da importação somente quando todos os itens estiverem revisados.
- Entidades ORM tipadas, repositories por entidade e services transacionais com
  SQLAlchemy 2 e `sessionmaker`.
- Alembic como fonte única do schema, com uma nova migration inicial para banco vazio.

### Alterado

- A persistência deixa de usar SQL manual e passa a usar a API ORM do SQLAlchemy.
- As migrations SQL legadas e o controle por `PRAGMA user_version` foram removidos.
- DTOs, entidades, repositories e services passam a seguir nomes e diretórios
  explícitos por responsabilidade.
- Os services de catálogo foram separados por entidade.
- Itens de notas importadas podem ser reclassificados sem alterar a situação ou
  a data da importação, atualizando também sua associação automática.

### Removido

- CLI e camada `presentation`, mantendo os utilitários reutilizáveis em `core/utils.py`.
- Adaptador legado `RepositorioNotas`.

- A revisão passa a confirmar somente a quantidade e, quando aplicável, a variação.
- Produtos por unidade e com variações exigem quantidades inteiras.
- As rotas de exclusão dos cadastros foram removidas.

- A marca passa a ser obrigatória conforme a configuração do produto.
- Remove confirmação de marca, conteúdo e unidade da embalagem dos itens.
- Cadastros relacionados a notas importadas não podem mais ser alterados.
- O campo de descrição livre das variações foi removido da API e do banco.
- O workspace Postman agora inclui os catálogos, a revisão e a importação.

## 1.0.1 — 2026-09-22

### Corrigido

- Leitura de NFC-e sem desconto quando a SVRS omite a linha de valor total.

## 0.2.0 — 2026-09-10

### API

- API FastAPI com contratos Pydantic e documentação OpenAPI automática.
- Swagger UI em `/docs`, ReDoc em `/redoc` e especificação em `/openapi.json`.
- Endpoints de saúde, versão, criação e consulta de leituras e listagem e
  consulta de notas.
- Erros estruturados para QR Code inválido, recurso ausente, falha na SEFAZ,
  resposta fiscal inválida e falha no SQLite.
- Leitura idempotente: uma chave já salva é devolvida sem nova consulta à SEFAZ.
- Valores e quantidades publicados como strings decimais para preservar precisão.
- CLI anterior preservada em `cli.py`; `main.py` passa a iniciar a API.

### Modelo e persistência

- `id` como primeiro campo de todas as entidades, com UUID automático.
- Entidades de estabelecimento com apelido opcional, categoria, marca, produto,
  apresentação, associação por estabelecimento e leitura pendente.
- URL recebida por parâmetro na consulta e validação dos QR Codes suportados do RS.
- Gravação transacional no SQLite de leituras, estabelecimentos, notas, itens e
  classificações presentes.
- Reconsulta preserva IDs, apelidos, situação e revisões existentes.
- Captura da URL antes da consulta e armazenamento do erro para nova tentativa.
- Campos de revisão separados dos dados fiscais originais.
- Testes de API, extração, persistência, rollback, reabertura e duplicidade.

A operação de revisão e a confirmação da importação continuam pendentes.

## 0.1.0 — 2026-09-09

### Adicionado

- Tags reutilizáveis por item, marcação em lote e opção de considerar notas no mês seguinte.
- Relatórios mensais de resumo, categorias e tags, com rateio proporcional de descontos em centavos e detalhes paginados.
- Migration `0003` preservando notas existentes.

- Consulta inicial da NFC-e do RS por URL fixa, com timeout e verificação TLS.
- Extração dos itens, emitente, emissão, identificação e totais da nota.
- Validação da chave, quantidade de itens, soma e desconto geral.
- Precisão decimal e exportação para JSON com situação `lida`.
- Leitura de HTML salvo e opção de salvar a resposta para diagnóstico.
- Alerta de divergência entre descrição em kg e unidade declarada.
- Testes de extração e validação sem acesso à rede.
- Ponto de entrada em `main.py` e módulos organizados em `src/`.
- Fonte única de versão em `src/core/version.py` e comando `--version`.
