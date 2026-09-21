# Leitor de notas fiscais

Monorepo de uma aplicação pessoal para ler NFC-e, revisar produtos e acompanhar os gastos da casa. O uso inicial é pela rede local, com servidor Linux e leitura do QR Code pelo Android.

Ler uma nota não significa importá-la. O fluxo da aplicação é: leitura do QR Code, nota pendente, revisão no celular ou computador e confirmação da importação.

## Estrutura

```text
backend/
  main.py            # API FastAPI
  src/               # API, DTOs, entidades, repositories, services e infraestrutura
  tests/             # Testes sem acesso à rede
  data/              # Banco SQLite local
  README.md          # Execução e contratos da API
  CHANGELOG.md       # Histórico do backend
frontend/
  src/               # Aplicação Angular
  Dockerfile         # Build Angular e servidor estático interno
  README.md          # Execução e arquitetura do frontend
  CHANGELOG.md       # Histórico do frontend
nginx/
  Dockerfile         # Gateway HTTP do projeto
  default.conf.template
postman/
  postman/           # Collection local com as chamadas do backend
docker-compose.yml   # Orquestra frontend, backend e Nginx
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

## Executar com Docker Compose

Na raiz do projeto:

```bash
docker compose up --build -d
```

Acesse `http://localhost:8080`. Somente o container `nginx` publica uma porta no servidor. O Nginx encaminha `/` para o frontend e remove o prefixo `/api` antes de encaminhar as chamadas ao backend.

O banco permanece em `backend/data/notas.sqlite3` por meio de um bind mount. Para escolher outra porta pública, copie `.env.example` para `.env` e altere `APP_PORT`.

```bash
docker compose ps
docker compose logs -f
docker compose down
```

No Android, cadastre exatamente `http://IP-DO-SERVIDOR:8080` como origem segura na configuração experimental do Chrome e reinicie o navegador. Se alterar `APP_PORT`, use a mesma porta nesse endereço.

Consulte os READMEs de cada aplicação para execução e testes.

## Versionamento

Backend e frontend têm versões independentes. A versão do backend é definida em `backend/src/core/version.py` e exposta por `/version`. A versão do frontend está em `frontend/package.json`. Os incrementos dependem de solicitação explícita do usuário.

## Licença

Este projeto é distribuído sob a [WTFPL, versão 2](LICENSE).
