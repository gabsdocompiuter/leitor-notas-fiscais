# Leitor de notas fiscais

Monorepo de uma aplicação pessoal para ler NFC-e, revisar os produtos e
acompanhar os gastos da casa. O uso inicial será pela rede local, com servidor
Linux e leitura do QR Code pelo Android.

Ler uma nota não significa importá-la. O fluxo planejado é: leitura do QR Code,
nota pendente, revisão no celular ou computador, confirmação da importação e
dashboard.

## Estrutura

```text
backend/
  main.py            # API FastAPI
  cli.py             # Ferramenta de terminal preservada
  src/               # API, modelos, serviços, persistência e apresentação
  requirements.txt   # Dependências Python
  tests/             # Testes sem acesso à rede
  examples/          # Resultados da validação inicial
  data/              # Banco SQLite local, criado automaticamente
  README.md          # Execução e contratos da API
  CHANGELOG.md       # Histórico do backend
frontend/
  README.md          # Escopo da futura interface Angular + Bootstrap
postman/
  postman/           # Collection local com as chamadas do backend
```

## Backend 0.2.0

Dentro de `backend/`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

A documentação Swagger fica em `http://localhost:8000/docs`. A API recebe a
URL do QR Code, consulta a NFC-e do RS, valida os dados e persiste a leitura no
SQLite. A nota continua como `lida` até que a futura tela de revisão confirme a
importação.

O arquivo padrão do banco é `backend/data/notas.sqlite3`. Consulte o
[README do backend](backend/README.md) para endpoints, execução no Windows,
uso da CLI e testes.

## Versionamento

Backend e frontend têm versões independentes. A versão do backend é definida em
`backend/src/core/version.py` e exposta por `/version`. Incrementos dependem
de solicitação explícita do usuário; mudanças posteriores ficam em **Não
lançado** no [changelog](backend/CHANGELOG.md).
