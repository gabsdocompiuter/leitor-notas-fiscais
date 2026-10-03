# Nginx

Gateway único da aplicação no Docker Compose. O serviço encaminha:

- `/` para o container `frontend` na porta 8080;
- `/api/*` para o container `backend` na porta 8008, removendo o prefixo `/api`;
- `/health` para uma resposta local usada pelo healthcheck do container.

O Compose publica o gateway em `http://localhost:8080` por padrão. Altere `APP_PORT` no arquivo `.env` para escolher outra porta.

## Acesso pelo Android

Para permitir a câmera via HTTP, configure no Chrome a origem `http://IP-DO-SERVIDOR:8080` como segura. O protocolo, o IP e a porta devem coincidir exatamente com o endereço acessado. Depois de alterar a configuração, reinicie o Chrome.

Uploads para `/api/` aceitam corpos até 101 MiB, acomodando o limite de arquivo SQLite de 100 MiB e o multipart. O timeout de leitura da API é de 300 segundos para acomodar validação, migrations e espera de requisições antes da substituição.
