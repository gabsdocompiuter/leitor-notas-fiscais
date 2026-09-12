import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from ..core.exceptions import ErroPersistencia


class BancoSQLite:
    def __init__(self, caminho: str | Path):
        self.caminho = Path(caminho).resolve()

    @contextmanager
    def conectar(self) -> Iterator[sqlite3.Connection]:
        conexao = None
        try:
            conexao = sqlite3.connect(self.caminho, timeout=30)
            conexao.row_factory = sqlite3.Row
            conexao.execute("PRAGMA foreign_keys = ON")
            with conexao:
                yield conexao
        except sqlite3.Error as erro:
            raise ErroPersistencia(f"Falha no SQLite: {erro}") from erro
        finally:
            if conexao is not None:
                conexao.close()

    def inicializar(self) -> None:
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        with self.conectar() as conexao:
            versao = conexao.execute("PRAGMA user_version").fetchone()[0]
            if versao == 0:
                schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
                conexao.executescript(schema)
            elif versao == 1:
                migracao = Path(__file__).with_name("migration_1_to_2.sql").read_text(
                    encoding="utf-8"
                )
                conexao.executescript(migracao)
            elif versao != 2:
                raise ErroPersistencia(f"Versão de estrutura SQLite não suportada: {versao}.")
