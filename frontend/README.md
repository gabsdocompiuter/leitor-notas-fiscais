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

Acesse `http://localhost:4200`. O servidor de desenvolvimento encaminha chamadas de `/api` para `http://localhost:8008` conforme `proxy.conf.json`.

Para acessar por outro dispositivo da rede:

```powershell
npm run start:network
```

Para usar a câmera pelo Android via HTTP, cadastre exatamente a origem do servidor, incluindo a porta, como segura na [configuração experimental do Chrome](chrome://flags/#unsafely-treat-insecure-origin-as-secure) e reinicie o navegador.

## Funcionalidades

- Lista e filtro de notas lidas, em revisão e importadas.
- Leitura do QR Code pela câmera com `@zxing/browser`.
- Campo alternativo para colar o conteúdo do QR Code.
- Revisão de produto, marca, conteúdo, unidade e quantidade normalizada.
- Cadastros rápidos de categorias, marcas e produtos.
- Alertas e progresso da revisão.
- Importação liberada somente depois da revisão de todos os itens.
- Consulta somente leitura de notas importadas.

O dashboard mensal será implementado depois da definição dos endpoints de totalização no backend.

## Comandos

```bash
npm start
npm run start:network
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
