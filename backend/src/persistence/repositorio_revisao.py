import sqlite3
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from ..core.exceptions import Conflito, NaoEncontrado
from ..core.normalizacao import decimal_texto, normalizar_nome
from ..models.nota import Nota
from ..models.situacao_nota import SituacaoNota
from ..models.unidade_medida import UnidadeMedida
from .banco_sqlite import BancoSQLite
from .repositorio_notas import RepositorioNotas


class RepositorioRevisao:
    def __init__(self, banco: BancoSQLite, repositorio_notas: RepositorioNotas):
        self.banco = banco
        self.repositorio_notas = repositorio_notas
        self.banco.inicializar()

    def revisar_item(
        self,
        chave: str,
        item_id: UUID,
        produto_id: UUID,
        marca_id: UUID | None,
        marca_confirmada: bool,
        conteudo_embalagem: Decimal | None,
        unidade_embalagem: UnidadeMedida | None,
        unidade_corrigida: UnidadeMedida,
        quantidade_normalizada: Decimal,
    ) -> Nota:
        with self.banco.conectar() as conexao:
            conexao.execute("BEGIN IMMEDIATE")
            nota = conexao.execute(
                "SELECT id, estabelecimento_id, situacao FROM notas WHERE chave = ?", (chave,)
            ).fetchone()
            if nota is None:
                raise NaoEncontrado("Nota não encontrada.")
            if nota["situacao"] == SituacaoNota.IMPORTADA.value:
                raise Conflito("Uma nota importada não pode mais ser alterada.")

            item = conexao.execute(
                "SELECT * FROM itens WHERE id = ? AND nota_id = ?",
                (str(item_id), nota["id"]),
            ).fetchone()
            if item is None:
                raise NaoEncontrado("Item não encontrado nessa nota.")
            if conexao.execute(
                "SELECT id FROM produtos WHERE id = ?", (str(produto_id),)
            ).fetchone() is None:
                raise NaoEncontrado("Produto não encontrado.")
            if marca_id is not None and conexao.execute(
                "SELECT id FROM marcas WHERE id = ?", (str(marca_id),)
            ).fetchone() is None:
                raise NaoEncontrado("Marca não encontrada.")

            apresentacao_id = self._obter_ou_criar_apresentacao(
                conexao,
                produto_id,
                marca_id,
                marca_confirmada,
                conteudo_embalagem,
                unidade_embalagem,
            )
            conexao.execute(
                """
                UPDATE itens
                SET apresentacao_id = ?, unidade_corrigida = ?,
                    quantidade_normalizada = ?, revisado = 1
                WHERE id = ?
                """,
                (
                    apresentacao_id,
                    unidade_corrigida.value,
                    decimal_texto(quantidade_normalizada),
                    str(item_id),
                ),
            )
            conexao.execute(
                "UPDATE notas SET situacao = 'em_revisao' WHERE id = ?", (nota["id"],)
            )

            fator = quantidade_normalizada / Decimal(item["quantidade"])
            self._salvar_associacao(
                conexao,
                nota["estabelecimento_id"],
                item["codigo"],
                item["descricao_original"],
                apresentacao_id,
                unidade_corrigida,
                fator,
            )
        return self._obter_nota(chave)

    def aplicar_classificacoes_automaticas(self, chave: str) -> Nota:
        with self.banco.conectar() as conexao:
            conexao.execute("BEGIN IMMEDIATE")
            nota = conexao.execute(
                "SELECT id, estabelecimento_id, situacao FROM notas WHERE chave = ?", (chave,)
            ).fetchone()
            if nota is None:
                raise NaoEncontrado("Nota não encontrada.")
            if nota["situacao"] == SituacaoNota.IMPORTADA.value:
                return self._obter_nota(chave)

            alterados = 0
            itens = conexao.execute(
                "SELECT * FROM itens WHERE nota_id = ? AND revisado = 0 ORDER BY numero",
                (nota["id"],),
            ).fetchall()
            for item in itens:
                associacao = conexao.execute(
                    """
                    SELECT apresentacao_id, unidade_corrigida, fator_normalizacao
                    FROM associacoes_produto
                    WHERE estabelecimento_id = ? AND codigo_item = ?
                    """,
                    (nota["estabelecimento_id"], item["codigo"]),
                ).fetchone()
                if associacao is None:
                    candidatas = conexao.execute(
                        """
                        SELECT DISTINCT apresentacao_id, unidade_corrigida, fator_normalizacao
                        FROM associacoes_produto
                        WHERE descricao_normalizada = ?
                        """,
                        (normalizar_nome(item["descricao_original"]),),
                    ).fetchall()
                    associacao = candidatas[0] if len(candidatas) == 1 else None
                if associacao is None:
                    continue
                quantidade = Decimal(item["quantidade"]) * Decimal(
                    associacao["fator_normalizacao"]
                )
                conexao.execute(
                    """
                    UPDATE itens
                    SET apresentacao_id = ?, unidade_corrigida = ?,
                        quantidade_normalizada = ?, revisado = 1
                    WHERE id = ?
                    """,
                    (
                        associacao["apresentacao_id"],
                        associacao["unidade_corrigida"],
                        decimal_texto(quantidade),
                        item["id"],
                    ),
                )
                alterados += 1
            if alterados:
                conexao.execute(
                    "UPDATE notas SET situacao = 'em_revisao' WHERE id = ?", (nota["id"],)
                )
        return self._obter_nota(chave)

    def concluir_importacao(self, chave: str) -> Nota:
        with self.banco.conectar() as conexao:
            conexao.execute("BEGIN IMMEDIATE")
            nota = conexao.execute(
                "SELECT id, situacao FROM notas WHERE chave = ?", (chave,)
            ).fetchone()
            if nota is None:
                raise NaoEncontrado("Nota não encontrada.")
            if nota["situacao"] == SituacaoNota.IMPORTADA.value:
                return self._obter_nota(chave)

            itens = conexao.execute(
                """
                SELECT i.revisado, i.apresentacao_id, i.unidade_corrigida,
                       i.quantidade_normalizada, a.marca_confirmada
                FROM itens i
                LEFT JOIN apresentacoes_produto a ON a.id = i.apresentacao_id
                WHERE i.nota_id = ?
                """,
                (nota["id"],),
            ).fetchall()
            incompletos = [
                item
                for item in itens
                if not item["revisado"]
                or item["apresentacao_id"] is None
                or item["unidade_corrigida"] is None
                or item["quantidade_normalizada"] is None
                or Decimal(item["quantidade_normalizada"]) <= 0
                or not item["marca_confirmada"]
            ]
            if not itens or incompletos:
                raise Conflito(
                    f"A nota possui {len(incompletos)} item(ns) que ainda precisam de revisão."
                )
            importada_em = datetime.now(timezone.utc).isoformat()
            conexao.execute(
                "UPDATE notas SET situacao = 'importada', importada_em = ? WHERE id = ?",
                (importada_em, nota["id"]),
            )
        return self._obter_nota(chave)

    @staticmethod
    def _obter_ou_criar_apresentacao(
        conexao: sqlite3.Connection,
        produto_id: UUID,
        marca_id: UUID | None,
        marca_confirmada: bool,
        conteudo_embalagem: Decimal | None,
        unidade_embalagem: UnidadeMedida | None,
    ) -> str:
        marca = str(marca_id) if marca_id else None
        conteudo = decimal_texto(conteudo_embalagem) if conteudo_embalagem else None
        unidade = unidade_embalagem.value if unidade_embalagem else None
        existente = conexao.execute(
            """
            SELECT id FROM apresentacoes_produto
            WHERE produto_id = ?
              AND ((marca_id = ?) OR (marca_id IS NULL AND ? IS NULL))
              AND ((conteudo_embalagem = ?) OR (conteudo_embalagem IS NULL AND ? IS NULL))
              AND ((unidade_embalagem = ?) OR (unidade_embalagem IS NULL AND ? IS NULL))
              AND marca_confirmada = ?
            """,
            (
                str(produto_id),
                marca,
                marca,
                conteudo,
                conteudo,
                unidade,
                unidade,
                int(marca_confirmada),
            ),
        ).fetchone()
        if existente:
            return existente["id"]
        apresentacao_id = str(uuid4())
        conexao.execute(
            """
            INSERT INTO apresentacoes_produto
                (id, produto_id, marca_id, conteudo_embalagem, unidade_embalagem, marca_confirmada)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                apresentacao_id,
                str(produto_id),
                marca,
                conteudo,
                unidade,
                int(marca_confirmada),
            ),
        )
        return apresentacao_id

    @staticmethod
    def _salvar_associacao(
        conexao: sqlite3.Connection,
        estabelecimento_id: str,
        codigo_item: str,
        descricao_original: str,
        apresentacao_id: str,
        unidade_corrigida: UnidadeMedida,
        fator: Decimal,
    ) -> None:
        conexao.execute(
            """
            INSERT INTO associacoes_produto
                (id, estabelecimento_id, codigo_item, descricao_original,
                 descricao_normalizada, apresentacao_id, unidade_corrigida,
                 fator_normalizacao)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(estabelecimento_id, codigo_item) DO UPDATE SET
                descricao_original = excluded.descricao_original,
                descricao_normalizada = excluded.descricao_normalizada,
                apresentacao_id = excluded.apresentacao_id,
                unidade_corrigida = excluded.unidade_corrigida,
                fator_normalizacao = excluded.fator_normalizacao
            """,
            (
                str(uuid4()),
                estabelecimento_id,
                codigo_item,
                descricao_original,
                normalizar_nome(descricao_original),
                apresentacao_id,
                unidade_corrigida.value,
                decimal_texto(fator),
            ),
        )

    def _obter_nota(self, chave: str) -> Nota:
        nota = self.repositorio_notas.obter_por_chave(chave)
        if nota is None:
            raise NaoEncontrado("Nota não encontrada.")
        return nota
