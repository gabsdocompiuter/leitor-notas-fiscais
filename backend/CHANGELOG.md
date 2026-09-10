# Changelog do backend

As versões só são alteradas por solicitação explícita do usuário.

## Não lançado

Nenhuma alteração pendente.

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

- Consulta inicial da NFC-e do RS por URL fixa, com timeout e verificação TLS.
- Extração dos itens, emitente, emissão, identificação e totais da nota.
- Validação da chave, quantidade de itens, soma e desconto geral.
- Precisão decimal e exportação para JSON com situação `lida`.
- Leitura de HTML salvo e opção de salvar a resposta para diagnóstico.
- Alerta de divergência entre descrição em kg e unidade declarada.
- Testes de extração e validação sem acesso à rede.
- Ponto de entrada em `main.py` e módulos organizados em `src/`.
- Fonte única de versão em `src/core/version.py` e comando `--version`.
