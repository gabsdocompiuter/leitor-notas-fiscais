# Nginx

Gateway único da aplicação no Docker Compose. O serviço encaminha:

- `/` para o container `frontend` na porta 8080;
- `/api/*` para o container `backend` na porta 8008, removendo o prefixo `/api`;
- `/health` para uma resposta local usada pelo healthcheck do container.

O Compose publica o gateway em `http://localhost:8080` por padrão. Altere `APP_PORT` no arquivo `.env` para escolher outra porta.

## Acesso pelo Android

Para permitir a câmera via HTTP, configure no Chrome a origem `http://IP-DO-SERVIDOR:8080` como segura. O protocolo, o IP e a porta devem coincidir exatamente com o endereço acessado. Depois de alterar a configuração, reinicie o Chrome.
