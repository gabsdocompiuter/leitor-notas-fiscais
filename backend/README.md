# Backend do leitor de NFC-e

O backend consulta a URL de QR Code recebida, extrai a nota e o estabelecimento
e salva o resultado no SQLite. A exportação em JSON é opcional. A CLI usa a URL de exemplo de
`src/core/config.py` somente quando `--url` é omitido.

**Ler não confirma a importação.** A nota extraída tem situação `lida`.
A nota é persistida com seus itens, mantendo a situação `lida`, sem confirmar
a importação. Ainda não há API, classificação automática, conversões de quantidade
ou operação de confirmação da importação.

## Executar

Dentro de `backend/`, com Python 3.10 ou superior e suporte a `venv`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py --json nota.json
```

Para escolher a nota, passe o link entre aspas (ele pode conter `|` e `&`):

```bash
python main.py --url "URL_DO_QR_CODE" --json nota.json
```

Substitua `URL_DO_QR_CODE` pelo endereço completo. Sem `--url`, a leitura da
nota de exemplo continua funcionando. No Windows, crie o ambiente com
`py -m venv .venv` e use `.venv\Scripts\python.exe` no lugar de `python`.

## Consulta e extração separadas

As duas funções recebem o endereço explicitamente:

```python
from src.services.consulta import consultar_nota
from src.services.leitura import extrair_nota

def ler(url: str):
    html = consultar_nota(url)
    return extrair_nota(html, url)
```

`consultar_nota(url)` retorna os bytes recebidos, com timeout de 30 segundos e
verificação TLS. `extrair_nota(html, url)` não acessa a rede: valida os campos,
confere a chave contida no endereço recebido e retorna uma entidade `Nota`.
Nenhum desses serviços importa a constante da URL de exemplo.

Nesta etapa, são aceitos os endereços HTTPS `/Dfe/QrCodeNFce` da SVRS e
`/NFCE/NFCE-COM.aspx` da SEFAZ RS, com parâmetro `p` e chave do RS. URLs de
outros estados ou formatos são rejeitadas. O parser lê o layout QR Code da SVRS;
o layout alternativo do portal SEFAZ RS com iframe ainda não é suportado.

## Leitura offline e diagnóstico

```bash
python main.py --url "URL_DO_QR_CODE" --salvar-html pagina.html --json nota.json
python main.py --url "URL_DO_QR_CODE" --html pagina.html --json nota.json
```

Use a mesma URL ao ler o HTML salvo: ela fornece a chave esperada. Os caminhos
de HTML e JSON precisam ter uma pasta existente. A pasta do SQLite é criada
automaticamente. Falhas encerram o processo com código 1, sem sobrescrever um
JSON anterior quando a consulta ou a gravação no banco falhar. `--salvar-html` grava a resposta antes da
extração, inclusive páginas de erro retornadas com HTTP 200.

## Entidades

Cada classe fica em seu arquivo em `src/models/`:

| Entidade | Papel e relações |
| --- | --- |
| `Estabelecimento` | CNPJ, razão social e `apelido` opcional; `nome_exibicao` usa o apelido quando preenchido |
| `LeituraNota` | URL capturada, data de captura UTC, nota opcional e erro opcional; pode existir antes da consulta |
| `Nota` | Chave, URL de origem, emissão, estabelecimento, itens, totais e situação |
| `Item` | Linha original da nota e campos separados para revisão |
| `Categoria` | Agrupamento, como Alimentação ou Limpeza |
| `Produto` | Nome padronizado, categoria e unidade base para futuras somas |
| `Marca` | Identificação da marca |
| `ApresentacaoProduto` | Produto, marca opcional e conteúdo/unidade da embalagem |
| `AssociacaoProduto` | Estabelecimento + código interno associados a uma apresentação; permite guardar uma correção de unidade reutilizável |

`UnidadeMedida` enumera UN, KG, G, L e ML. `SituacaoNota` enumera `lida`,
`em_revisao` e `importada`; definir essas situações ainda não implementa as
operações de revisão ou importação.

Todas as entidades declaram `id` como primeiro campo; essa ordem também aparece
no JSON e nas tabelas SQLite. O UUID continua sendo gerado automaticamente. Para
restaurar um identificador existente, passe `id=...` por nome (`kw_only=True`);
os outros argumentos posicionais continuam compatíveis.

A persistência reutiliza estabelecimentos por CNPJ e notas/leituras pela chave.
Uma nova extração cria UUIDs temporários, mas salvar uma chave existente retorna
os objetos e IDs já armazenados. As associações reutilizáveis entre códigos e
produtos ainda não têm operação de persistência; serão implementadas junto da
classificação automática.

### Produtos e revisão

Leite integral e leite desnatado são produtos diferentes. Marcas e embalagens
de 1 L ou 500 ML podem ter apresentações distintas ligadas ao mesmo produto.
`marca_confirmada=True` com `marca=None` permite registrar uma revisão que
confirmou a ausência de marca, distinguindo-a de uma informação pendente.

O item preserva `descricao_original`, `quantidade`, `unidade_original` e valores.
Os campos `apresentacao`, `unidade_corrigida`, `quantidade_normalizada` e
`revisado` ficam separados e começam vazios ou falsos. A quantidade normalizada,
quando preenchida no futuro, será expressa na unidade base do produto.
O conteúdo da embalagem pertence à apresentação; a quantidade comprada pertence
ao item. A associação reutilizável não guarda quantidades de uma compra.

O parser já preenche a entidade de estabelecimento e mantém seu apelido como
`None`. Alterar o apelido não modifica a razão social obtida da nota.

## JSON e valores

A saída agora contém `estabelecimento` com CNPJ, razão social, apelido e ID,
substituindo os antigos campos `emitente` e `cnpj_emitente`. Inclui também
`url_origem`, IDs e os campos de revisão dos itens.

Valores e quantidades usam `Decimal` e viram strings com ponto no JSON.
UUIDs viram strings e datas usam ISO 8601. A emissão é um `datetime` que preserva
a hora local exibida pela SEFAZ, sem inventar um fuso não informado na página.
O total de cada item vem da origem, preservando seu arredondamento. O desconto
geral permanece no nível da nota; seu rateio será implementado na importação.
O JSON não inclui dados do consumidor.

Os exemplos em `examples/` usam esse formato. A consulta real e o HTML salvo
foram conferidos: 21 itens, total R$ 169,18, desconto R$ 2,60 e valor a pagar
R$ 166,58. Os dados fiscais coincidem; os UUIDs de cada extração são diferentes.

## Organização e testes

- `src/core/`: configuração, versão e exceções compartilhadas.
- `src/models/`: entidades e enumerações, uma classe por arquivo.
- `src/services/`: validação do QR Code, consulta HTTP e extração do HTML.
- `src/presentation/`: CLI, terminal e JSON.
- `src/persistence/`: conexão, esquema SQL e repositório de notas.
- `tests/`: testes sem rede; `examples/`: resultados da nota de exemplo.

```bash
python -m unittest discover -s tests -v
```

Os testes cobrem URLs recebidas por parâmetro, correspondência de chave,
extração e totais, apelidos, revisão, serialização, reabertura do SQLite,
transações, chaves estrangeiras e consultas repetidas sem duplicação.

## Persistência SQLite

O comando `python main.py` já consulta e salva no banco. Por padrão, o arquivo
fica em `backend/data/notas.sqlite3`, independentemente da pasta de execução.
É usado `sqlite3`, da biblioteca padrão do Python, sem novas dependências.

Para escolher outro arquivo:

```bash
python main.py --banco /caminho/notas.sqlite3 --json nota.json
```

O fluxo da CLI é:

1. Validar o QR Code e registrar a leitura com URL e chave no SQLite.
2. Consultar e extrair os dados da nota (ou ler o HTML local).
3. Salvar estabelecimento, nota e itens em uma transação, ligando-os à leitura.
4. Mostrar a nota recuperada do banco e, se solicitado, exportar o JSON.

Uma falha de consulta ou extração deixa a leitura pendente com o erro registrado,
sem criar uma nota parcial. Uma tentativa posterior reutiliza essa leitura e
limpa o erro quando a gravação termina com sucesso.

Notas têm chave única; estabelecimentos têm CNPJ único; cada linha é única por
nota/número. Repetir o comando consulta novamente a SEFAZ, mas devolve a nota já
armazenada, com seus IDs, apelido, situação e revisões preservados. A gravação de
consulta não substitui dados existentes e não funciona como edição da nota.

Os campos de classificação do item também são preservados quando presentes.
Categorias, marcas, produtos e apresentações referenciados são salvos junto da
nota. O catálogo fica vazio para itens que ainda não foram classificados.

As tabelas são `leituras`, `estabelecimentos`, `notas`, `itens`, `categorias`,
`marcas`, `produtos` e `apresentacoes_produto`. Chaves estrangeiras são ativadas
em cada conexão. UUIDs e datas são armazenados como texto; valores e quantidades
também usam texto decimal para evitar arredondamento binário. Os cálculos e as
validações usam `Decimal` no Python.

Se qualquer inserção falhar, a transação desfaz todos os registros da nota.
A leitura registrada anteriormente continua disponível para uma nova tentativa.
O esquema inicial está em `src/persistence/schema.sql`; `PRAGMA user_version=1`
identifica a estrutura do banco, independentemente da versão `0.1.0` da aplicação.

### Recuperar dados em Python

```python
from src.core.config import CAMINHO_BANCO
from src.persistence.banco_sqlite import BancoSQLite
from src.persistence.repositorio_notas import RepositorioNotas

repositorio = RepositorioNotas(BancoSQLite(CAMINHO_BANCO))
nota = repositorio.obter_por_chave("CHAVE_DE_44_DIGITOS")
leitura = repositorio.obter_leitura_por_chave("CHAVE_DE_44_DIGITOS")
```

Ambos retornam `None` quando a chave não existe. `--version` e `--help` não criam
o banco. Os arquivos SQLite são ignorados pelo Git. O JSON é exportado depois da
transação; se apenas essa exportação falhar, a nota já estará salva no banco.

## Versionamento

A versão inicial do backend é **0.1.0**, definida exclusivamente no código em
`src/core/version.py`, na variável `__version__`. Dentro de `backend/`, consulte-a com:

```bash
python main.py --version
```

O comando imprime a versão e encerra com sucesso, sem consultar a SEFAZ,
ler uma nota ou gerar arquivos.

**A versão só deve ser alterada quando o usuário solicitar explicitamente.**
Correções, funcionalidades, testes, commits e builds não provocam incrementos.
O frontend terá seu próprio versionamento quando for implementado.

As mudanças seguintes devem ser registradas em **Não lançado**, no
[CHANGELOG.md](CHANGELOG.md), mantendo a versão atual. Quando o usuário autorizar
uma nova versão, atualizar `src/core/version.py` e mover as mudanças correspondentes
para uma seção datada dessa versão no changelog.

A numeração segue `MAJOR.MINOR.PATCH`, mas a escolha e aplicação do próximo número
dependem dessa autorização. Não há criação automática de tags ou releases Git.
