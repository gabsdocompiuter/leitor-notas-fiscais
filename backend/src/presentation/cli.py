"""Primeira leitura da NFC-e do RS. Ler uma nota não confirma sua importação."""

import argparse
import sys
from pathlib import Path

from .apresentacao import mostrar
from ..core.config import CAMINHO_BANCO, URL_NOTA
from ..services.consulta import consultar_nota
from ..core.exceptions import ErroConsulta, ErroLeitura, ErroPersistencia
from ..persistence.banco_sqlite import BancoSQLite
from ..persistence.repositorio_notas import RepositorioNotas
from ..services.leitura import extrair_nota
from ..services.qrcode import extrair_chave
from .serializacao import serializar
from ..core.version import __version__


def main() -> int:
    argumentos = argparse.ArgumentParser(description=__doc__)
    argumentos.add_argument(
        "--version", action="version", version=__version__,
        help="Exibe a versão do backend e encerra, sem consultar a SEFAZ.",
    )
    argumentos.add_argument("--html", type=Path, help="Lê um HTML salvo, sem consultar a rede.")
    argumentos.add_argument("--url", default=URL_NOTA, help="URL do QR Code; usa a nota de exemplo quando omitida.")
    argumentos.add_argument("--json", type=Path, help="Grava a nota lida em JSON UTF-8.")
    argumentos.add_argument("--banco", type=Path, default=CAMINHO_BANCO, help="Arquivo SQLite; padrão: backend/data/notas.sqlite3.")
    argumentos.add_argument("--salvar-html", type=Path, help="Salva a resposta bruta para diagnóstico.")
    opcoes = argumentos.parse_args()
    repositorio = None
    leitura = None
    try:
        chave = extrair_chave(opcoes.url)
        banco = BancoSQLite(opcoes.banco)
        repositorio = RepositorioNotas(banco)
        leitura = repositorio.registrar_leitura(opcoes.url, chave)
        html = opcoes.html.read_bytes() if opcoes.html else consultar_nota(opcoes.url)
        if opcoes.salvar_html:
            opcoes.salvar_html.write_bytes(html)
        nota = extrair_nota(html, opcoes.url)
        nota = repositorio.salvar(nota, leitura.id)
        if opcoes.json:
            opcoes.json.write_text(serializar(nota), encoding="utf-8")
        mostrar(nota)
        print(f"\nNota disponível no SQLite: {banco.caminho}")
        if opcoes.json:
            print(f"\nJSON salvo em: {opcoes.json.resolve()}")
        return 0
    except (ErroConsulta, ErroLeitura, ErroPersistencia, OSError) as erro:
        if repositorio is not None and leitura is not None:
            try:
                repositorio.registrar_erro(leitura.id, str(erro))
            except (ErroPersistencia, OSError) as erro_registro:
                print(f"Não foi possível registrar a falha: {erro_registro}", file=sys.stderr)
        print(f"Erro: {erro}", file=sys.stderr)
        return 1
