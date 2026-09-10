# Backend do leitor de NFC-e

API FastAPI que recebe o conteúdo do QR Code de uma NFC-e do Rio Grande do Sul,
consulta a SVRS e salva a leitura, o estabelecimento, a nota e seus itens no
SQLite. A nota permanece com situação `lida`: a importação será confirmada em
uma etapa futura de revisão.

## Executar a API

Use Python 3.10 ou superior. Dentro de `backend/`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

No Windows, crie o ambiente com `py -m venv .venv`, ative-o com
`.venv\Scripts\activate` e execute `python main.py`.

A API escuta em todas as interfaces na porta 8000. Na própria máquina, abra:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI: `http://localhost:8000/openapi.json`
- Estado da API: `http://localhost:8000/health`

Para recarregar o servidor automaticamente durante o desenvolvimento:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Endpoints da versão 0.2.0

| Método | Caminho | Função |
| --- | --- | --- |
| `GET` | `/health` | Verifica se a API está disponível |
| `GET` | `/version` | Retorna a versão do backend |
| `POST` | `/leituras` | Recebe a URL do QR Code, consulta e salva a nota |
| `GET` | `/leituras/{chave}` | Recupera a captura, inclusive quando a consulta falhou |
| `GET` | `/notas` | Lista notas, com paginação e filtro por situação |
| `GET` | `/notas/{chave}` | Recupera uma nota e todos os itens |

Exemplo de leitura:

```bash
curl -X POST http://localhost:8000/leituras \
  -H "Content-Type: application/json" \
  -d '{"url":"https://dfe-portal.svrs.rs.gov.br/Dfe/QrCodeNFce?p=CHAVE|3|1"}'
```

Repetir a leitura da mesma chave retorna os registros existentes e não consulta
a SEFAZ novamente. Isso evita duplicatas e preserva IDs, apelidos e revisões.
Falhas na SEFAZ deixam a captura salva com `erro_consulta`, permitindo uma nova
tentativa posterior.

Quantidades e valores monetários são strings decimais nas respostas para preservar
a precisão. Datas usam ISO 8601 e identificadores usam UUID.

## SQLite

O banco padrão fica em `backend/data/notas.sqlite3`, independentemente da pasta
de onde o processo foi iniciado. A pasta é criada automaticamente.

As tabelas são `leituras`, `estabelecimentos`, `notas`, `itens`, `categorias`,
`marcas`, `produtos` e `apresentacoes_produto`. A gravação de cada nota é
transacional, com chaves estrangeiras habilitadas. Notas são únicas por chave e
estabelecimentos por CNPJ.

## CLI preservada

A ferramenta anterior continua disponível em `cli.py`:

```bash
python cli.py --url "URL_DO_QR_CODE" --json nota.json
python cli.py --url "URL_DO_QR_CODE" --salvar-html pagina.html --json nota.json
python cli.py --url "URL_DO_QR_CODE" --html pagina.html --json nota.json
python cli.py --banco /caminho/notas.sqlite3 --json nota.json
python cli.py --version
```

Sem `--url`, a CLI usa a URL de exemplo de `src/core/config.py`. A CLI ainda
reconsulta a SEFAZ ao ser repetida; a API aplica o comportamento idempotente.

## Organização

- `main.py`: entrada da API e objeto ASGI `app`.
- `cli.py`: entrada da ferramenta de terminal.
- `src/api/`: aplicação FastAPI, rotas, dependências, erros e contratos Pydantic.
- `src/core/`: configuração, versão e exceções compartilhadas.
- `src/models/`: entidades e enumerações, com uma classe por arquivo.
- `src/services/`: validação do QR Code, consulta, extração e fluxo da leitura.
- `src/persistence/`: conexão, esquema SQL e repositório.
- `src/presentation/`: CLI, terminal e serialização JSON.
- `tests/`: testes locais sem acesso à rede.

## Testes

```bash
python -m unittest discover -s tests -v
```

Os testes cobrem o OpenAPI e o Swagger, erros HTTP, leitura idempotente, consulta,
extração, entidades, serialização, persistência, transações e CLI.

## Versionamento

A versão atual do backend é **0.2.0**, definida somente em
`src/core/version.py`. Consulte-a pela API em `/version` ou pela CLI com
`python cli.py --version`.

A versão só deve ser alterada quando o usuário solicitar explicitamente. Mudanças
posteriores ficam em **Não lançado** no `CHANGELOG.md` até nova autorização.
Não há criação automática de tags ou releases Git.
