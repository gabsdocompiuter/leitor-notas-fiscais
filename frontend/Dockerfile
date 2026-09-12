FROM node:20.19.6-alpine AS build

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20.19.6-alpine

RUN npm install --global serve@14.2.6
WORKDIR /app
COPY --from=build --chown=node:node /app/dist/leitor-notas-fiscais/browser ./public

USER node
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD node -e "fetch('http://127.0.0.1:8080').then(r=>{if(!r.ok)process.exit(1)}).catch(()=>process.exit(1))"

CMD ["serve", "--single", "--listen", "8080", "public"]
