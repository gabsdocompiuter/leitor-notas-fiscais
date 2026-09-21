import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import Session, sessionmaker

from ..exceptions import ErroPersistencia


class BancoSQLite:
    """Configura o engine, as sessões e a execução das migrations do SQLite."""

    def __init__(self, caminho: str | Path):
        self.caminho = Path(caminho).resolve()
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(
            f"sqlite:///{self.caminho.as_posix()}",
            connect_args={"timeout": 30, "check_same_thread": False},
            poolclass=NullPool,
        )
        event.listen(self.engine, "connect", self._configurar_conexao)
        self.session_factory = sessionmaker(
            bind=self.engine, class_=Session, expire_on_commit=False
        )
        self.inicializar()

    @staticmethod
    def _configurar_conexao(conexao: sqlite3.Connection, _: object) -> None:
        cursor = conexao.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()

    def inicializar(self) -> None:
        """Atualiza um banco vazio até a revisão mais recente do Alembic."""
        configuracao = Config(str(Path(__file__).resolve().parents[3] / "alembic.ini"))
        configuracao.set_main_option(
            "script_location", str(Path(__file__).with_name("migrations"))
        )
        configuracao.set_main_option("sqlalchemy.url", f"sqlite:///{self.caminho.as_posix()}")
        try:
            command.upgrade(configuracao, "head")
        except Exception as erro:
            raise ErroPersistencia(f"Falha ao migrar o SQLite: {erro}") from erro

    @contextmanager
    def conectar(self) -> Iterator[sqlite3.Connection]:
        """Acesso DB-API mantido apenas para diagnósticos e compatibilidade."""
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

    def fechar(self) -> None:
        self.engine.dispose()
