"""Ponto de entrada da API do leitor de NFC-e."""

import uvicorn

from src.api.app import criar_app


app = criar_app()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8008)
