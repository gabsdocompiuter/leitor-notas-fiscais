# Leitor de notas fiscais

Monorepo de uma aplicação pessoal para ler NFC-e, revisar os produtos e acompanhar
os gastos da casa. O uso inicial será pela rede local, com servidor Linux e
leitura do QR Code pelo Android.

**Ler uma nota não significa importá-la.** O fluxo planejado é:
leitura do QR Code → nota pendente → revisão no celular ou computador →
confirmação da importação → dashboard.

## Estrutura

```text
backend/
  main.py           # Ponto de entrada do backend
  src/              # Implementação: modelos, consulta, extração e CLI
  requirements.txt  # Dependências Python
  tests/            # Testes sem acesso à rede
  examples/         # Resultados JSON da validação inicial
  data/             # Banco SQLite local, criado automaticamente
  README.md         # Execução e detalhes do backend
  CHANGELOG.md      # Histórico de alterações do backend
frontend/
  README.md         # Escopo da interface Angular + Bootstrap
.gitignore
README.md
```

Cada aplicação mantém suas próprias dependências e instruções de execução.
O ambiente virtual Python deve ficar em `backend/.venv`; os futuros arquivos
do workspace Angular, incluindo `package.json` e `angular.json`, ficarão em
`frontend/`. Quando a execução integrada for implementada, o arquivo Compose
ficará na raiz, com contextos de build apontando para cada aplicação.

## Backend: iniciar no Linux

Na raiz do repositório:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py --json nota.json
```

Para executar os testes, dentro de `backend/` e com o ambiente ativo:

```bash
python -m unittest discover -s tests -v
```

Consulte o [README do backend](backend/README.md) para uso no Windows,
leitura offline e detalhes do JSON.

## Estado atual

O leitor Python recebe uma URL de QR Code do RS (com uma URL de exemplo por
padrão na CLI), extrai os itens e o estabelecimento, verifica os totais e gera
uma nota com situação `lida`, persistida no SQLite com seu estabelecimento e
itens. O arquivo padrão é `backend/data/notas.sqlite3`; use `--banco` para
escolher outro caminho. As entidades de revisão já estão definidas. A API
FastAPI, a interface Angular e o ambiente Docker ainda serão implementados.

O [README do frontend](frontend/README.md) registra o escopo previsto para a interface.

## Versionamento do backend

A versão é definida em `backend/src/core/version.py` e pode ser consultada com
`python backend/main.py --version`, a partir da raiz.

Incrementos de versão dependem de solicitação explícita do usuário. Mudanças
posteriores ficam em **Não lançado**, no [changelog do backend](backend/CHANGELOG.md),
até a autorização de uma nova versão.
