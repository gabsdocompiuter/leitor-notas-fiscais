"""Configurações compartilhadas da API e da consulta à SEFAZ."""

import os
from pathlib import Path

from dotenv import load_dotenv

RAIZ_BACKEND = Path(__file__).resolve().parents[2]
load_dotenv(RAIZ_BACKEND / ".env")

URL_NOTA = (
    "https://dfe-portal.svrs.rs.gov.br/Dfe/QrCodeNFce"
    "?p=43260907718633007868650080002005971056148317|3|1"
)
LIMITE_HTML = 5 * 1024 * 1024
CAMINHO_BANCO = RAIZ_BACKEND / "data" / "notas.sqlite3"

PERMITIR_IMPORTACAO_BANCO = os.getenv("PERMITIR_IMPORTACAO_BANCO", "false").strip().lower() == "true"
LIMITE_IMPORTACAO_BANCO = 100 * 1024 * 1024

ORIGENS_CORS = [
    origem.strip()
    for origem in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
    if origem.strip()
]
