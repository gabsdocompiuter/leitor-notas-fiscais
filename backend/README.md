# Backend do leitor de NFC-e

API FastAPI que recebe o link do QR Code, a chave de acesso de 44 dígitos ou o
link de consulta da SEFAZ RS de uma NFC-e do Rio Grande do Sul,
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

A API escuta em todas as interfaces na porta 8008. Na própria máquina, abra:

- Swagger UI: `http://localhost:8008/docs`
- ReDoc: `http://localhost:8008/redoc`
- OpenAPI: `http://localhost:8008/openapi.json`
- Estado da API: `http://localhost:8008/health`

Copie `.env.example` para `.env` na raiz do diretório `backend`. A aplicação Python carrega esse arquivo diretamente ao iniciar. No Docker Compose, ele é apenas montado como `/app/.env` em modo somente leitura; o Compose não interpreta nem injeta suas variáveis. `CORS_ALLOWED_ORIGINS` aceita uma lista de origens separada por vírgulas.

Executar `python main.py` já habilita a recarga automática ao alterar arquivos Python.
Também é possível iniciar diretamente pelo Uvicorn:

```bash
uvicorn main:app --host 0.0.0.0 --port 8008 --reload
```

## Endpoints da versão 1.0.1

| Método | Caminho | Função |
| --- | --- | --- |
| `GET` | `/health` | Verifica se a API está disponível |
| `GET` | `/version` | Retorna a versão do backend |
| `POST` | `/leituras` | Recebe link ou chave de acesso, consulta e salva a nota |
| `GET` | `/leituras/{chave}` | Recupera a captura, inclusive quando a consulta falhou |
| `GET` | `/notas` | Lista notas, com paginação e filtro por situação |
| `GET` | `/notas/{chave}` | Recupera uma nota e todos os itens |
| `PATCH` | `/notas/{chave}/itens/{item_id}` | Revisa e classifica um item |
| `POST` | `/notas/{chave}/importacao` | Importa uma nota totalmente revisada |
| `PATCH` | `/notas/{chave}` | Define `considerar_proximo_mes` |
| `PUT` | `/notas/{chave}/itens/{item_id}/tags` | Substitui as tags do item |
| `POST` | `/notas/{chave}/itens/tags` | Adiciona tags a todos os itens, sem remover as existentes |
| `GET/POST` | `/tags` | Sugere as cinco tags mais usadas, cria ou reutiliza tags |
| `GET` | `/relatorios/mensal?mes=AAAA-MM` | Resumo, categorias e tags do mês |
| `GET` | `/relatorios/mensal/itens?mes=AAAA-MM` | Detalha os itens, com paginação e filtros |
| `GET/POST` | `/categorias` | Lista ou cria categorias |
| `GET/PATCH` | `/categorias/{id}` | Consulta ou altera uma categoria |
| `GET/POST` | `/marcas` | Lista ou cria marcas |
| `GET/PATCH` | `/marcas/{id}` | Consulta ou altera uma marca |
| `GET/POST` | `/produtos` | Lista ou cria produtos |
| `GET/PATCH/DELETE` | `/produtos/{id}` | Consulta, altera ou exclui um produto sem uso |
| `GET` | `/produtos/{id}/restricoes` | Informa permissões de alteração estrutural e exclusão, com os motivos |
| `GET` | `/unidades-medida` | Lista unidades de peso e volume com descrição |
| `GET/POST` | `/produtos/{id}/variacoes` | Lista ou cria variações de peso ou volume |
| `PATCH` | `/variacoes/{id}` | Altera uma variação |
| `GET` | `/estabelecimentos` | Lista e pesquisa estabelecimentos |
| `PATCH` | `/estabelecimentos/{id}` | Altera somente o apelido do estabelecimento |

Exemplo de leitura:

```bash
curl -X POST http://localhost:8008/leituras \
  -H "Content-Type: application/json" \
  -d '{"url":"https://dfe-portal.svrs.rs.gov.br/Dfe/QrCodeNFce?p=CHAVE|3|1"}'
```

O campo `url` também aceita `43261008593122000302650530001850701977539572` ou
`https://www.sefaz.rs.gov.br/NFE/NFE-NFC.aspx?chaveNFe=43261008593122000302650530001850701977539572`.
Para essas entradas, a API monta
`https://dfe-portal.svrs.rs.gov.br/Dfe/QrCodeNFce?p={CHAVE}|3|1` e usa esse endereço
para consultar e salvar a origem da nota. Espaços nas extremidades são removidos.
Links de QR Code já suportados preservam seus parâmetros. Chaves devem conter
44 dígitos e começar com `43`; o link da SEFAZ deve usar HTTPS e conter um único
parâmetro `chaveNFe` válido. Entradas inválidas retornam HTTP 422 com
`qrcode_invalido` antes de consultar a rede.

Repetir a leitura da mesma chave, em qualquer um dos três formatos, retorna os registros existentes e não consulta
a SEFAZ novamente. Isso evita duplicatas e preserva IDs, apelidos e revisões.
Falhas na SEFAZ deixam a captura salva com `erro_consulta`, permitindo uma nova
tentativa posterior.

Quantidades e valores monetários são strings decimais nas respostas para preservar
a precisão. Datas usam ISO 8601 e identificadores usam UUID.

## Revisão, associações e importação

Revisar um item exige produto e quantidade confirmada. A marca também é
obrigatória, exceto quando o produto estiver cadastrado com
`nao_solicitar_marca=true`. Produtos tratados somente como unidades exigem uma
quantidade inteira. Produtos com variações também exigem quantidade inteira e
uma variação do próprio produto. Produtos a granel aceitam quantidade decimal.

Produtos tratados somente como unidades também podem ser revisados em pacotes.
Envie `quantidade_pacotes` e `unidades_por_pacote` como inteiros positivos, junto
de `quantidade_confirmada` igual ao produto dos dois valores. Por exemplo, dois
pacotes com 30 unidades têm `quantidade_confirmada=60`. As respostas retornam as
três quantidades como strings decimais. Para unidades avulsas, omita os campos
de pacote ou envie ambos como `null`. O conteúdo da embalagem é lembrado na
associação do item para futuras revisões automáticas.

A primeira revisão cria uma associação com o código interno do produto naquele
estabelecimento e guarda o fator usado na conversão da quantidade. Novas notas
aplicam essa classificação automaticamente. Quando não houver associação por
estabelecimento e código, a descrição original é comparada ignorando diferenças
de maiúsculas, minúsculas e espaços. Descrições com classificações conflitantes
continuam pendentes.

Uma nota só pode ser importada quando todos os itens estiverem revisados. A
importação grava `importada_em` em UTC. Depois disso, cada item ainda pode ser
reclassificado sem alterar a situação nem a data da importação, e a associação
usada nas notas futuras acompanha o ajuste. Cadastros referenciados por notas
importadas possuem restrições específicas: produtos permitem corrigir nome,
categoria e exigência de marca; categorias, marcas e variações mantêm seus
bloqueios atuais.

Correções de nome e categoria do produto aparecem também nas compras antigas
e nos relatórios, reagrupando gastos sem alterar valores financeiros. Unidade,
tratamento como unidades e uso de variações não podem mudar enquanto houver
itens de qualquer nota ou associações automáticas vinculados ao produto. Sem
esses vínculos, a estrutura pode mudar; desativar variações exige que não haja
variações cadastradas.

Passar a exigir marca preserva os itens e a situação/data das notas importadas.
Itens sem marca em notas ainda não importadas voltam a ficar não revisados,
preservando sua classificação e quantidades. Novas classificações e correções
manuais cumprem a regra atual; associações sem marca obrigatória não são
reaproveitadas automaticamente.

`GET /produtos/{id}/restricoes` retorna `pode_alterar_estrutura`, `pode_excluir`,
`motivo_alteracao_estrutura` e `motivo_exclusao` (motivos nulos quando permitido).
As restrições são verificadas novamente ao alterar ou excluir.
`DELETE /produtos/{id}` retorna 204 sem corpo, 404 para produto inexistente ou
409 se qualquer item referenciar sua apresentação ou variação. Quando permitido,
remove também associações, apresentações e variações em uma única transação,
preservando categorias, marcas e estabelecimentos. Falhas desfazem toda a limpeza.

## Tags e relatórios mensais

Tags são opcionais, múltiplas e vinculadas somente aos itens. Nomes são limpos
e comparados sem diferenças de maiúsculas, inclusive Unicode. O catálogo permanece
disponível mesmo quando uma tag não estiver em uso. As operações de marcação
recebem `{"tag_ids": ["UUID"]}`; uma lista vazia no PUT remove todas as tags do item.
A aplicação em lote é transacional e não guarda vínculo entre tag e nota.
Tags não participam das associações nem da classificação automática.
`GET /tags` retorna no máximo cinco tags, ordenadas pela quantidade de itens
marcados e, em caso de empate, pelo nome. O parâmetro `busca` filtra parte do
nome somente a partir de três caracteres; filtros menores retornam as populares.

O mês considerado usa a data local de emissão. Com
`{"considerar_proximo_mes": true}`, a nota inteira passa para o próximo mês civil,
incluindo dezembro para janeiro. Tags e mês podem ser ajustados antes ou depois
da importação sem mudar `importada_em` ou a situação da nota.

Os relatórios incluem apenas notas importadas. O resumo usa `valor_a_pagar`,
apresenta descontos e compara com o mês anterior. O desconto da nota é rateado
proporcionalmente em centavos inteiros, distribuindo o resto pelos maiores restos
fracionários; empates seguem a ordem dos itens. Categorias fecham com o total pago.
Um item marcado com várias tags aparece em cada uma delas: seus totais se
sobrepõem e não devem ser somados. Os detalhes aceitam `categoria_id`, `tag_id`,
`limite` (1–100, padrão 50) e `deslocamento`; os filtros são aplicados depois do rateio.
As totalizações consultam o mês inteiro, independentemente da paginação de notas.

## Persistência, SQLAlchemy e Alembic

O banco padrão fica em `backend/data/notas.sqlite3`, independentemente da pasta
de onde o processo foi iniciado. A pasta é criada automaticamente. O acesso aos
dados usa SQLAlchemy 2, com entidades declarativas tipadas por `Mapped` e
`mapped_column`. Os repositories não confirmam transações: cada service abre a
sessão e controla `commit`/`rollback` por caso de uso com `sessionmaker`.

As tabelas são `leituras`, `estabelecimentos`, `notas`, `itens`, `categorias`,
`marcas`, `produtos`, `variacoes_produto`, `apresentacoes_produto` e
`associacoes_produto`, `tags` e `itens_tags`. A gravação de cada nota é
transacional, com chaves estrangeiras habilitadas. Notas são únicas por chave e
estabelecimentos por CNPJ.

O Alembic é a única fonte de criação e evolução do schema. Esta refatoração parte
de um banco vazio e possui uma migration inicial (`0001`). A migration `0003` adiciona as tags e a opção de mês, preservando notas existentes com a opção desmarcada. Para aplicar as
migrations manualmente, dentro de `backend/`, execute:

```bash
alembic upgrade head
```

Para criar uma nova revisão depois de alterar as entidades:

```bash
alembic revision --autogenerate -m "descricao da alteracao"
```

## Organização

- `main.py`: entrada da API e objeto ASGI `app`.
- `src/api/`: aplicação FastAPI, rotas, dependências, erros e contratos Pydantic.
- `src/core/`: configurações, utilitários e exceções compartilhadas.
- `src/core/persistence/`: engine, `sessionmaker`, tipos e migrations do Alembic.
- `src/dtos/`: DTOs usados entre services e apresentação HTTP.
- `src/entities/`: entidades SQLAlchemy, uma classe por arquivo.
- `src/enums/`: enumerações compartilhadas pelo domínio e pelo ORM.
- `src/repositories/`: repositories SQLAlchemy, um para cada entidade.
- `src/services/`: regras e transações, com um service exclusivo por entidade.
- `tests/`: testes locais sem acesso à rede.

## Notas e itens ignorados

As respostas de notas incluem `ignorada` e as respostas de itens incluem `ignorado`,
ambos inicialmente `false`. As marcações persistem nas reconsultas da SEFAZ.

- `PATCH /notas/{chave}/ignorada`: recebe `{"ignorada": true}` ou `false`.
- `PATCH /notas/{chave}/itens/{item_id}/ignorado`: recebe `{"ignorado": true}` ou `false`.

Ambas as operações retornam a nota atualizada e podem ser repetidas. Uma nota ou
item inexistente, inclusive um item de outra nota, retorna `404`.
Ignorar não apaga os dados. Enquanto a nota estiver ignorada, a API retorna
`situacao: "ignorada"`. O filtro `GET /notas?situacao=ignorada` lista somente essas
notas; os demais filtros por situação não as incluem. A listagem sem filtro inclui
todas. A situação de importação anterior fica preservada internamente e volta a
ser exibida ao desmarcar a nota, mantendo as escolhas individuais dos itens.

Itens ignorados dispensam revisão. A conclusão da importação exige ao menos um item
não ignorado e a classificação completa de todos os itens considerados; caso
contrário, retorna `409`. Para desmarcar um item incompleto de uma nota importada,
revise-o primeiro pelo endpoint de revisão; uma tentativa antecipada retorna `409`.
Notas importadas podem ter todos os seus itens posteriormente ignorados.

Todos os relatórios, incluindo totais, contagens, quantidades e mês anterior,
excluem notas e itens ignorados. O desconto é rateado sobre os itens originais
antes da exclusão, sem redistribuição da parcela dos ignorados. Notas sem itens
considerados não são contadas. Os valores fiscais originais da nota permanecem
disponíveis na consulta. A migration `0005` atualiza bancos existentes com as
marcações desativadas.

## Testes

```bash
python -m unittest discover -s tests -v
```

Os testes cobrem OpenAPI, catálogos, revisão, importação, classificação
automática, migração do SQLite, leitura idempotente, extração e persistência.

O workspace em `../postman/` possui requisições organizadas para todos os
endpoints. Preencha as variáveis de IDs da collection com os valores retornados
pelas operações de criação e leitura.

## Versionamento

A versão atual do backend é **1.0.1**, definida somente em
`src/core/version.py`. Consulte-a pela API em `/version`.

A versão só deve ser alterada quando o usuário solicitar explicitamente. Mudanças
posteriores ficam em **Não lançado** no `CHANGELOG.md` até nova autorização.
Não há criação automática de tags ou releases Git.


## Importação e exportação do banco

- `GET /banco/configuracao`: informa `permitir_importacao`.
- `GET /banco/exportacao`: baixa uma cópia SQLite consistente de todos os dados.
- `POST /banco/importacao`: recebe multipart com o campo `arquivo` (até 100 MiB).

A importação substitui todos os dados. Configure `PERMITIR_IMPORTACAO_BANCO=true`
no `.env` do backend somente em ambientes locais; o padrão é `false` e deve
permanecer assim em produção. Reinicie a API depois de alterar a configuração.
A permissão é verificada na API, independentemente do frontend.

A API valida integridade, referências e estrutura, aceitando a versão atual e
revisões anteriores conhecidas do Alembic. Migrations são executadas apenas na
cópia recebida. Bancos antigos sem controle de versão Alembic não são aceitos.
Antes da substituição, a API aguarda requisições em andamento por até 60 segundos,
incluindo consultas à SEFAZ. Novas operações recebem 503 durante a troca;
importações simultâneas recebem 409. Uploads e validação não bloqueiam consultas.

O banco anterior é guardado em `data/notas.sqlite3.pre-importacao.bak`.
Somente a última cópia é mantida. Se a troca ou reabertura falhar, o banco anterior
é preservado/restaurado. Se a própria restauração falhar, o backup permanece
disponível e a API bloqueia o acesso ao banco com 503 até a intervenção no servidor.
Para restauração manual, pare a API antes de substituir
arquivos; a tela não oferece um botão de restauração.

Esta coordenação exige um único processo backend e nenhuma outra aplicação
acessando diretamente o arquivo SQLite durante a troca. Não execute múltiplos
workers/réplicas sobre este banco com importação habilitada.


### Compras manuais

- `POST /estabelecimentos`: cria um estabelecimento com `apelido` obrigatório (até 100 caracteres).
  CNPJ e razão social ficam nulos; o apelido desses estabelecimentos não pode ser removido.
- `POST /notas/manuais`: recebe `estabelecimento_id`, `data` (`AAAA-MM-DD`) e pelo menos um item.
  Cada item usa os campos de classificação de uma revisão (`produto_id`, marca/variação quando exigidas,
  `quantidade_confirmada` e, opcionalmente, `quantidade_pacotes` e `unidades_por_pacote`)
  e `valor_total`, em reais, com até duas casas decimais. Ao informar pacotes, a quantidade confirmada
  deve ser o total de unidades; quantidade e unidades por pacote devem ser inteiras.
- `POST /notas/{uuid}/itens`: adiciona um item a uma compra manual concluída e não ignorada,
  com os mesmos campos e validações do cadastro. Salva o item já revisado e recalcula
  a quantidade de itens e os totais da compra em uma transação, mantendo a conclusão.
- A compra é gravada atomicamente com origem `manual`, situação `importada`, itens revisados e desconto zero.
  Os totais e preços unitários são calculados no servidor; chave, número, série e URL fiscal ficam nulos.
- Os endpoints de consulta e ajustes de notas aceitam tanto a chave fiscal como o UUID.
  Os itens dos relatórios incluem `nota_id` para navegar até compras sem `chave_nota`.
- Compras manuais não alimentam o reconhecimento automático de produtos em notas fiscais.

- Ao ajustar um item manual, `PATCH /notas/{chave-ou-uuid}/itens/{item_id}` também aceita
  `valor_total` opcional. Se omitido, mantém o valor pago; produto, quantidade, unidade e preço
  unitário são sincronizados e os totais da compra são recalculados. Valores fiscais não são editáveis.

- Itens manuais também aceitam `valor_unitario` no cadastro e na edição, em alternativa a
  `valor_total`. Informe somente um deles. O servidor multiplica o preço unitário pela quantidade
  confirmada, arredonda o total para centavos e preserva o preço informado. Para pacotes, o preço
  unitário corresponde à unidade do produto. A tela inicia em valor total e permite trocar o tipo
  mantendo o número digitado.
