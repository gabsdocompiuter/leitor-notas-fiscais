# Leitor de notas fiscais

Monorepo de uma aplicação pessoal para ler NFC-e, revisar produtos e acompanhar os gastos da casa. O uso inicial é pela rede local, com servidor Linux e leitura do QR Code pelo Android.

Ler uma nota não significa importá-la. O fluxo da aplicação é: leitura do QR Code, nota pendente, revisão no celular ou computador e confirmação da importação.

## Estrutura

```text
backend/
  main.py            # API FastAPI
  cli.py             # Ferramenta de terminal
  src/               # API, modelos, serviços e persistência
  tests/             # Testes sem acesso à rede
  data/              # Banco SQLite local
  README.md          # Execução e contratos da API
  CHANGELOG.md       # Histórico do backend
frontend/
  src/               # Aplicação Angular
  nginx/             # Proxy da API e exemplo para HTTPS local
  Dockerfile         # Build Angular e servidor Nginx
  README.md          # Execução e arquitetura do frontend
  CHANGELOG.md       # Histórico do frontend
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

No Windows, ative o ambiente virtual com `venv\Scripts\Activate.ps1`.

A documentação Swagger fica em `http://localhost:8008/docs`. A API recebe a URL do QR Code, consulta a NFC-e do RS, valida os dados e persiste a leitura no SQLite. Também oferece catálogos, revisão dos itens, classificação automática e confirmação da importação.

## Frontend 0.1.0

O frontend usa Angular 21, Bootstrap e Node.js 20.19.6. Dentro de `frontend/`:

```bash
nvm use 20.19.6
npm install
npm start
```

Acesse `http://localhost:4200`. O proxy de desenvolvimento encaminha `/api` para o backend na porta 8008.

Consulte os READMEs de cada aplicação para execução, testes e Docker.

## Versionamento

Backend e frontend têm versões independentes. A versão do backend é definida em `backend/src/core/version.py` e exposta por `/version`. A versão do frontend está em `frontend/package.json`. Os incrementos dependem de solicitação explícita do usuário.
