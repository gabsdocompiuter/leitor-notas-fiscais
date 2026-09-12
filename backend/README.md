# Backend do leitor de NFC-e

API FastAPI que recebe o conteúdo do QR Code de uma NFC-e do Rio Grande do Sul,
consulta a SVRS e salva a leitura, o estabelecimento, a nota e seus itens no
SQLite. A API também permite classificar os itens e concluir a importação depois
que todos estiverem revisados.

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

- Swagger UI: `http://localhost:8008/docs`
- ReDoc: `http://localhost:8008/redoc`
- OpenAPI: `http://localhost:8008/openapi.json`
- Estado da API: `http://localhost:8008/health`

Para recarregar o servidor automaticamente durante o desenvolvimento:

```bash
uvicorn main:app --host 0.0.0.0 --port 8008 --reload
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
| `PATCH` | `/notas/{chave}/itens/{item_id}` | Revisa e classifica um item |
| `POST` | `/notas/{chave}/importacao` | Importa uma nota totalmente revisada |
| `GET/POST` | `/categorias` | Lista ou cria categorias |
| `GET/PATCH/DELETE` | `/categorias/{id}` | Consulta, altera ou exclui uma categoria |
| `GET/POST` | `/marcas` | Lista ou cria marcas |
| `GET/PATCH/DELETE` | `/marcas/{id}` | Consulta, altera ou exclui uma marca |
| `GET/POST` | `/produtos` | Lista ou cria produtos |
| `GET/PATCH/DELETE` | `/produtos/{id}` | Consulta, altera ou exclui um produto |

Exemplo de leitura:

```bash
curl -X POST http://localhost:8008/leituras \
  -H "Content-Type: application/json" \
  -d '{"url":"https://dfe-portal.svrs.rs.gov.br/Dfe/QrCodeNFce?p=CHAVE|3|1"}'
```

Repetir a leitura da mesma chave retorna os registros existentes e não consulta
a SEFAZ novamente. Isso evita duplicatas e preserva IDs, apelidos e revisões.
Falhas na SEFAZ deixam a captura salva com `erro_consulta`, permitindo uma nova
tentativa posterior.

Quantidades e valores monetários são strings decimais nas respostas para preservar
a precisão. Datas usam ISO 8601 e identificadores usam UUID.

## Revisão, associações e importação

Revisar um item exige produto, unidade corrigida, quantidade normalizada e uma
decisão explícita sobre a marca. `marca_confirmada=true` com `marca_id=null`
registra que o item não possui uma marca identificada. Conteúdo e unidade da
embalagem são opcionais, mas devem ser enviados juntos.

A primeira revisão cria uma associação com o código interno do produto naquele
estabelecimento e guarda o fator usado na normalização da quantidade. Novas notas
aplicam essa classificação automaticamente. Quando não houver associação por
estabelecimento e código, a descrição original é comparada ignorando diferenças
de maiúsculas, minúsculas e espaços. Descrições com classificações conflitantes
continuam pendentes.

Uma nota só pode ser importada quando todos os itens estiverem revisados. A
importação grava `importada_em` em UTC. Depois disso, a nota e os cadastros que
alterariam seus dados históricos ficam imutáveis.

## SQLite

O banco padrão fica em `backend/data/notas.sqlite3`, independentemente da pasta
de onde o processo foi iniciado. A pasta é criada automaticamente.

As tabelas são `leituras`, `estabelecimentos`, `notas`, `itens`, `categorias`,
`marcas`, `produtos`, `apresentacoes_produto` e `associacoes_produto`. A gravação de cada nota é
transacional, com chaves estrangeiras habilitadas. Notas são únicas por chave e
estabelecimentos por CNPJ.

`PRAGMA user_version=2` identifica a estrutura atual. Ao abrir um banco da
estrutura 1, o backend adiciona as associações e o momento da importação sem
apagar as notas existentes.

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
- `src/services/`: consulta, extração, catálogos, revisão e classificação.
- `src/persistence/`: conexão, migrações, esquema SQL e repositórios.
- `src/presentation/`: CLI, terminal e serialização JSON.
- `tests/`: testes locais sem acesso à rede.

## Testes

```bash
python -m unittest discover -s tests -v
```

Os testes cobrem OpenAPI, catálogos, revisão, importação, classificação
automática, migração do SQLite, leitura idempotente, extração, persistência e CLI.

O workspace em `../postman/` possui requisições organizadas para todos os
endpoints. Preencha as variáveis de IDs da collection com os valores retornados
pelas operações de criação e leitura.

## Versionamento

A versão atual do backend é **0.2.0**, definida somente em
`src/core/version.py`. Consulte-a pela API em `/version` ou pela CLI com
`python cli.py --version`.

A versão só deve ser alterada quando o usuário solicitar explicitamente. Mudanças
posteriores ficam em **Não lançado** no `CHANGELOG.md` até nova autorização.
Não há criação automática de tags ou releases Git.
