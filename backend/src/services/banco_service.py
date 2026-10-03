import os
import re
import shutil
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path
from typing import BinaryIO

from alembic.script import ScriptDirectory
from sqlalchemy import text

from ..core.config import LIMITE_IMPORTACAO_BANCO
from ..core.exceptions import DadosInvalidos, ErroPersistencia
from ..core.persistence.banco_sqlite import BancoSQLite
from ..core.persistence.coordenacao_banco import CoordenacaoBanco


class ArquivoMuitoGrande(Exception):
    pass


class BancoService:
    def __init__(self, banco: BancoSQLite, coordenacao: CoordenacaoBanco):
        self.banco = banco
        self.coordenacao = coordenacao

    def temporario(self) -> Path:
        try:
            descritor, nome = tempfile.mkstemp(
                prefix="transferencia-", suffix=".sqlite3", dir=self.banco.caminho.parent
            )
            os.close(descritor)
            return Path(nome)
        except OSError as erro:
            raise ErroPersistencia("Não foi possível criar o arquivo temporário do banco.") from erro

    @staticmethod
    def limpar(caminho: Path) -> None:
        for sufixo in ("", "-wal", "-shm", "-journal"):
            Path(str(caminho) + sufixo).unlink(missing_ok=True)

    @staticmethod
    def copiar_banco(origem: Path, destino: Path) -> None:
        with closing(sqlite3.connect(origem.as_uri() + "?mode=ro", uri=True)) as entrada:
            with closing(sqlite3.connect(destino)) as saida:
                entrada.backup(saida)

    def exportar(self) -> Path:
        caminho = self.temporario()
        try:
            self.copiar_banco(self.banco.caminho, caminho)
            return caminho
        except Exception as erro:
            self.limpar(caminho)
            raise ErroPersistencia("Não foi possível exportar o banco.") from erro

    @staticmethod
    def estrutura(conexao: sqlite3.Connection) -> dict:
        objetos = conexao.execute("SELECT type, name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchall()
        if any(tipo in ("view", "trigger") for tipo, _, _ in objetos):
            raise DadosInvalidos("O banco contém uma estrutura incompatível.")
        estrutura = {}
        for tipo, nome, sql in objetos:
            if tipo != "table":
                continue
            identificador = '"' + nome.replace('"', '""') + '"'
            colunas = sorted(tuple(linha[1:]) for linha in conexao.execute(f"PRAGMA table_info({identificador})"))
            estrangeiras = sorted(tuple(linha[2:]) for linha in conexao.execute(f"PRAGMA foreign_key_list({identificador})"))
            indices = []
            for indice in conexao.execute(f"PRAGMA index_list({identificador})"):
                nome_indice = '"' + indice[1].replace('"', '""') + '"'
                campos = tuple(linha[2] for linha in conexao.execute(f"PRAGMA index_info({nome_indice})"))
                indices.append((indice[2], indice[3], indice[4], campos))
            # Inclui CHECKs e collations que os PRAGMAs não descrevem. Aceitamos
            # schemas produzidos pelas migrations do aplicativo, ignorando formatação.
            definicao = re.sub(r"\s+", "", sql.replace('"', ''))
            estrutura[nome] = (colunas, estrangeiras, sorted(indices), definicao)
        return estrutura

    @staticmethod
    def verificar_integridade(conexao: sqlite3.Connection) -> None:
        if conexao.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
            raise DadosInvalidos("O banco SQLite está corrompido.")
        if conexao.execute("PRAGMA foreign_key_check").fetchone() is not None:
            raise DadosInvalidos("O banco possui referências inválidas entre registros.")

    def validar_e_migrar(self, caminho: Path) -> None:
        referencia = self.temporario()
        try:
            with caminho.open("rb") as arquivo:
                if arquivo.read(16) != b"SQLite format 3\x00":
                    raise DadosInvalidos("Selecione um arquivo SQLite válido.")
            with closing(sqlite3.connect(caminho)) as conexao:
                self.verificar_integridade(conexao)
                revisoes = conexao.execute("SELECT version_num FROM alembic_version").fetchall()
                scripts = ScriptDirectory.from_config(BancoSQLite.configuracao_migrations(caminho))
                conhecidas = {r.revision for r in scripts.walk_revisions()}
                if len(revisoes) != 1 or revisoes[0][0] not in conhecidas:
                    raise DadosInvalidos("A versão do banco não é compatível com este aplicativo.")
                revisao = revisoes[0][0]
                estrutura_recebida = self.estrutura(conexao)
            BancoSQLite.migrar(referencia, revisao)
            with closing(sqlite3.connect(referencia)) as conexao:
                if estrutura_recebida != self.estrutura(conexao):
                    raise DadosInvalidos("A estrutura do banco não é compatível com este aplicativo.")
            BancoSQLite.migrar(caminho)
            BancoSQLite.migrar(referencia)
            with closing(sqlite3.connect(caminho)) as conexao, closing(sqlite3.connect(referencia)) as esperado:
                self.verificar_integridade(conexao)
                if self.estrutura(conexao) != self.estrutura(esperado):
                    raise DadosInvalidos("A estrutura do banco atualizado não é compatível.")
                conexao.execute("PRAGMA journal_mode = DELETE")
        except DadosInvalidos:
            raise
        except Exception as erro:
            raise DadosInvalidos("Não foi possível validar ou atualizar o banco selecionado.") from erro
        finally:
            self.limpar(referencia)

    def verificar_abertura(self) -> None:
        with self.banco.session_factory() as sessao:
            sessao.execute(text("SELECT version_num FROM alembic_version")).one()
            sessao.execute(text("SELECT id FROM notas LIMIT 1")).all()

    def substituir(self, caminho: Path) -> None:
        backup_temporario = self.temporario()
        backup = self.banco.caminho.with_name(self.banco.caminho.name + ".pre-importacao.bak")
        substituido = False
        try:
            with self.coordenacao.substituir():
                try:
                    self.copiar_banco(self.banco.caminho, backup_temporario)
                    os.replace(backup_temporario, backup)
                    self.banco.fechar()
                    with closing(sqlite3.connect(self.banco.caminho)) as conexao:
                        checkpoint = conexao.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
                        if checkpoint and checkpoint[0] != 0:
                            raise ErroPersistencia("Não foi possível encerrar as conexões do banco.")
                        conexao.execute("PRAGMA journal_mode = DELETE")
                    os.replace(caminho, self.banco.caminho)
                    substituido = True
                    self.verificar_abertura()
                except Exception as erro:
                    if substituido:
                        restauracao = None
                        try:
                            self.banco.fechar()
                            restauracao = self.temporario()
                            shutil.copyfile(backup, restauracao)
                            for sufixo in ("-wal", "-shm", "-journal"):
                                Path(str(self.banco.caminho) + sufixo).unlink(missing_ok=True)
                            os.replace(restauracao, self.banco.caminho)
                            self.verificar_abertura()
                        except Exception as falha_restauracao:
                            self.coordenacao.bloquear()
                            raise ErroPersistencia(
                                "Não foi possível restaurar o banco anterior. "
                                "A cópia foi preservada no servidor e o acesso ao banco foi bloqueado."
                            ) from falha_restauracao
                        finally:
                            if restauracao is not None:
                                self.limpar(restauracao)
                    raise ErroPersistencia("Não foi possível substituir o banco. O banco anterior foi preservado.") from erro
        finally:
            self.limpar(backup_temporario)

    def importar(self, arquivo: BinaryIO) -> None:
        caminho = self.temporario()
        try:
            tamanho = 0
            with caminho.open("wb") as destino:
                while bloco := arquivo.read(1024 * 1024):
                    tamanho += len(bloco)
                    if tamanho > LIMITE_IMPORTACAO_BANCO:
                        raise ArquivoMuitoGrande()
                    destino.write(bloco)
            self.validar_e_migrar(caminho)
            self.substituir(caminho)
        except OSError as erro:
            raise ErroPersistencia("Não foi possível gravar o arquivo do banco no servidor.") from erro
        finally:
            self.limpar(caminho)
