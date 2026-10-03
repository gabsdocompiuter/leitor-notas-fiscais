# Frontend

Aplicação Angular para ler o QR Code de NFC-e, revisar a classificação dos itens e concluir a importação. A versão atual do frontend é **0.1.0**.

## Requisitos

- Node.js 20.19.6, gerenciado pelo NVM
- npm 10 ou superior
- Backend em execução em `http://localhost:8008`

## Executar em desenvolvimento

No Windows:

```powershell
nvm use 20.19.6
cd frontend
npm install
npm start
```

Acesse `http://localhost:4200`. A configuração `local` usa `src/environments/environment.local.ts` e chama o backend diretamente em `http://localhost:8008`.

Para executar com o proxy de desenvolvimento e a URL relativa `/api`, use `npm run start:proxy`.

Para acessar por outro dispositivo da rede:

```powershell
npm run start:network
```

Esse comando mantém o proxy `/api`, pois `localhost` no arquivo de ambiente apontaria para o próprio dispositivo que abriu a aplicação.

Para usar a câmera pelo Android via HTTP, cadastre exatamente a origem do servidor, incluindo a porta, como segura na [configuração experimental do Chrome](chrome://flags/#unsafely-treat-insecure-origin-as-secure) e reinicie o navegador.

## Funcionalidades

- Lista e filtro de notas aguardando revisão, em revisão e importadas.
- Leitura do QR Code pela câmera com `@zxing/browser`.
- Campo alternativo para colar o conteúdo do QR Code.
- Revisão de produto, marca quando exigida, quantidade e variação de peso ou volume.
- Cadastros de categorias, marcas, produtos, variações e apelidos de estabelecimentos.
- Cadastros rápidos de categorias, marcas e produtos.
- Alertas e progresso da revisão.
- Importação liberada somente depois da revisão de todos os itens.
- Consulta e ajuste individual dos itens de notas importadas.

A área **Relatórios** reúne o resumo mensal e os gastos por categoria e por tag,
com seleção de mês, comparação com o anterior e detalhes paginados dos itens.
Ela inclui apenas notas importadas e distribui proporcionalmente os descontos.

Na revisão, o campo **Considerar no próximo mês** move a nota inteira para o
mês seguinte, sem alterar a emissão. Cada item aceita várias tags, exibidas como badges arredondadas. Ao abrir o
campo, o backend sugere as cinco mais usadas; a busca por parte do nome começa
com três caracteres. A opção de criar uma tag aparece antes das sugestões.
**Aplicar tag a todos os itens** faz uma marcação em lote; depois, as tags podem
ser removidas individualmente. Esses controles continuam disponíveis após a
importação. As novas telas usam componentes e classes Bootstrap responsivos.

## Comandos

```bash
npm start
npm run start:network
npm run start:proxy
npm test
npm run build
```

## Docker

O container do frontend compila o Angular e publica os arquivos estáticos internamente na porta 8080. Ele não publica portas no host e não contém Nginx.

```bash
docker build -t leitor-notas-fiscais-frontend ./frontend
```

Use `docker compose up --build -d` na raiz do monorepo para iniciar frontend, backend e o gateway Nginx.

## Estrutura

```text
src/app/
  core/       # contratos da API, serviços e regras auxiliares
  features/   # leitura de QR Code, lista e revisão das notas
  shared/     # componentes reutilizáveis
```


## Banco de dados

O menu **Banco de dados** abre `/banco-de-dados`. Exportação está disponível em
todos os ambientes. A seção de importação só aparece quando
`GET /banco/configuracao` retorna `permitir_importacao=true`; não há configuração
nos environments Angular. Falha nessa consulta mantém apenas a exportação.
A seleção aceita `.sqlite3`, `.sqlite` e `.db`, até 100 MiB. O modal de confirmação
antecede o envio; cancelar não chama a API. Após sucesso, a aplicação recarrega
em `/notas` para consultar os dados substituídos.
