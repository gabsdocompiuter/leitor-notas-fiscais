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

A leitura pela câmera exige uma origem segura no Android. `localhost` é aceito durante o desenvolvimento no próprio aparelho, mas um endereço como `http://192.168.0.10:4200` precisa ser publicado por HTTPS com um certificado confiável no celular.

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

## Docker e Nginx

Crie a imagem:

```bash
docker build -t leitor-notas-fiscais-frontend ./frontend
```

Por padrão, o Nginx encaminha `/api` para `backend:8008`. O host e a porta podem ser alterados pelas variáveis `BACKEND_HOST` e `BACKEND_PORT`.

```bash
docker run --rm -p 8080:80 \
  -e BACKEND_HOST=host.docker.internal \
  -e BACKEND_PORT=8008 \
  leitor-notas-fiscais-frontend
```

O arquivo `nginx/https.conf.template.example` contém a configuração para HTTPS. Para usá-la, monte esse arquivo como `/etc/nginx/templates/default.conf.template` e monte o certificado e a chave em `/etc/nginx/certs/`. Em uma rede doméstica, ferramentas como `mkcert` podem gerar uma autoridade local; o certificado raiz também precisa ser instalado como confiável no Android.

## Estrutura

```text
src/app/
  core/       # contratos da API, serviços e regras auxiliares
  features/   # leitura de QR Code, lista e revisão das notas
  shared/     # componentes reutilizáveis
```
