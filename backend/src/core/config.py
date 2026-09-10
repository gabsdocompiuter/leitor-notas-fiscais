"""Configuração: URL de exemplo usada somente pela CLI e limite da resposta."""

from pathlib import Path

URL_NOTA = (
    "https://dfe-portal.svrs.rs.gov.br/Dfe/QrCodeNFce"
    "?p=43260907718633007868650080002005971056148317|3|1"
)
LIMITE_HTML = 5 * 1024 * 1024
CAMINHO_BANCO = Path(__file__).resolve().parents[2] / "data" / "notas.sqlite3"
