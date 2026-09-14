import sqlite3
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from ..core.exceptions import Conflito, DadosInvalidos, NaoEncontrado
from ..core.normalizacao import decimal_texto, normalizar_nome
from ..models.nota import Nota
from ..models.situacao_nota import SituacaoNota
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
        variacao_id: UUID | None,
        quantidade_confirmada: Decimal,
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

            produto, variacao = self._validar_classificacao(
                conexao, produto_id, marca_id, variacao_id, quantidade_confirmada
            )
            apresentacao_id = self._obter_ou_criar_apresentacao(
                conexao, produto_id, marca_id
            )
            conexao.execute(
                """UPDATE itens
                   SET apresentacao_id = ?, variacao_id = ?,
                       quantidade_confirmada = ?, revisado = 1
                   WHERE id = ?""",
                (
                    apresentacao_id,
                    variacao["id"] if variacao else None,
                    decimal_texto(quantidade_confirmada),
                    str(item_id),
                ),
            )
            conexao.execute(
                "UPDATE notas SET situacao = 'em_revisao' WHERE id = ?", (nota["id"],)
            )

            fator = quantidade_confirmada / Decimal(item["quantidade"])
            self._salvar_associacao(
                conexao,
                nota["estabelecimento_id"],
                item["codigo"],
                item["descricao_original"],
                apresentacao_id,
                variacao["id"] if variacao else None,
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
                associacao = self._buscar_associacao(
                    conexao,
                    nota["estabelecimento_id"],
                    item["codigo"],
                    item["descricao_original"],
                )
                if associacao is None:
                    continue
                quantidade_original = Decimal(item["quantidade"])
                quantidade = quantidade_original * Decimal(
                    associacao["fator_conversao"]
                )
                if (
                    associacao["tratar_apenas_como_unidades"]
                    or associacao["contem_variacoes"]
                ) and (
                    quantidade_original != quantidade_original.to_integral_value()
                    or quantidade != quantidade.to_integral_value()
                ):
                    continue
                conexao.execute(
                    """UPDATE itens
                       SET apresentacao_id = ?, variacao_id = ?,
                           quantidade_confirmada = ?, revisado = 1
                       WHERE id = ?""",
                    (
                        associacao["apresentacao_id"],
                        associacao["variacao_id"],
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
                """SELECT i.revisado, i.apresentacao_id, i.variacao_id,
                          i.quantidade_confirmada, a.marca_id, a.produto_id,
                          p.nao_solicitar_marca, p.tratar_apenas_como_unidades,
                          p.contem_variacoes, v.produto_id AS variacao_produto_id
                   FROM itens i
                   LEFT JOIN apresentacoes_produto a ON a.id = i.apresentacao_id
                   LEFT JOIN produtos p ON p.id = a.produto_id
                   LEFT JOIN variacoes_produto v ON v.id = i.variacao_id
                   WHERE i.nota_id = ?""",
                (nota["id"],),
            ).fetchall()
            incompletos = [item for item in itens if not self._item_completo(item)]
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
    def _validar_classificacao(
        conexao: sqlite3.Connection,
        produto_id: UUID,
        marca_id: UUID | None,
        variacao_id: UUID | None,
        quantidade: Decimal,
    ) -> tuple[sqlite3.Row, sqlite3.Row | None]:
        if quantidade <= 0:
            raise DadosInvalidos("A quantidade confirmada deve ser maior que zero.")
        produto = conexao.execute(
            "SELECT * FROM produtos WHERE id = ?", (str(produto_id),)
        ).fetchone()
        if produto is None:
            raise NaoEncontrado("Produto não encontrado.")
        if not produto["nao_solicitar_marca"] and marca_id is None:
            raise DadosInvalidos("A marca é obrigatória para o produto selecionado.")
        if marca_id is not None and conexao.execute(
            "SELECT id FROM marcas WHERE id = ?", (str(marca_id),)
        ).fetchone() is None:
            raise NaoEncontrado("Marca não encontrada.")

        variacao = None
        if produto["contem_variacoes"]:
            if variacao_id is None:
                raise DadosInvalidos("A variação é obrigatória para o produto selecionado.")
            variacao = conexao.execute(
                "SELECT * FROM variacoes_produto WHERE id = ? AND produto_id = ?",
                (str(variacao_id), str(produto_id)),
            ).fetchone()
            if variacao is None:
                raise DadosInvalidos("A variação não pertence ao produto selecionado.")
        elif variacao_id is not None:
            raise DadosInvalidos("O produto selecionado não possui variações.")

        if (produto["tratar_apenas_como_unidades"] or produto["contem_variacoes"]) and (
            quantidade != quantidade.to_integral_value()
        ):
            raise DadosInvalidos("A quantidade deve ser um número inteiro para esse produto.")
        return produto, variacao

    @staticmethod
    def _item_completo(item: sqlite3.Row) -> bool:
        if (
            not item["revisado"]
            or item["apresentacao_id"] is None
            or item["quantidade_confirmada"] is None
            or Decimal(item["quantidade_confirmada"]) <= 0
            or (not item["nao_solicitar_marca"] and item["marca_id"] is None)
        ):
            return False
        inteiro = item["tratar_apenas_como_unidades"] or item["contem_variacoes"]
        quantidade = Decimal(item["quantidade_confirmada"])
        if inteiro and quantidade != quantidade.to_integral_value():
            return False
        if item["contem_variacoes"]:
            return (
                item["variacao_id"] is not None
                and item["variacao_produto_id"] == item["produto_id"]
            )
        return item["variacao_id"] is None

    @staticmethod
    def _buscar_associacao(
        conexao: sqlite3.Connection,
        estabelecimento_id: str,
        codigo_item: str,
        descricao_original: str,
    ) -> sqlite3.Row | None:
        selecao = """SELECT ap.apresentacao_id, ap.variacao_id, ap.fator_conversao,
                            p.tratar_apenas_como_unidades, p.contem_variacoes
                     FROM associacoes_produto ap
                     JOIN apresentacoes_produto a ON a.id = ap.apresentacao_id
                     JOIN produtos p ON p.id = a.produto_id
                     LEFT JOIN variacoes_produto v ON v.id = ap.variacao_id
                     WHERE {filtro}
                       AND (p.nao_solicitar_marca = 1 OR a.marca_id IS NOT NULL)
                       AND ((p.contem_variacoes = 1 AND v.produto_id = p.id)
                            OR (p.contem_variacoes = 0 AND ap.variacao_id IS NULL))"""
        associacao = conexao.execute(
            selecao.format(filtro="ap.estabelecimento_id = ? AND ap.codigo_item = ?"),
            (estabelecimento_id, codigo_item),
        ).fetchone()
        if associacao:
            return associacao
        candidatas = conexao.execute(
            selecao.format(filtro="ap.descricao_normalizada = ?"),
            (normalizar_nome(descricao_original),),
        ).fetchall()
        return candidatas[0] if len(candidatas) == 1 else None

    @staticmethod
    def _obter_ou_criar_apresentacao(
        conexao: sqlite3.Connection, produto_id: UUID, marca_id: UUID | None
    ) -> str:
        marca = str(marca_id) if marca_id else None
        existente = conexao.execute(
            """SELECT id FROM apresentacoes_produto
               WHERE produto_id = ?
                 AND ((marca_id = ?) OR (marca_id IS NULL AND ? IS NULL))""",
            (str(produto_id), marca, marca),
        ).fetchone()
        if existente:
            return existente["id"]
        apresentacao_id = str(uuid4())
        conexao.execute(
            "INSERT INTO apresentacoes_produto (id, produto_id, marca_id) VALUES (?, ?, ?)",
            (apresentacao_id, str(produto_id), marca),
        )
        return apresentacao_id

    @staticmethod
    def _salvar_associacao(
        conexao: sqlite3.Connection,
        estabelecimento_id: str,
        codigo_item: str,
        descricao_original: str,
        apresentacao_id: str,
        variacao_id: str | None,
        fator: Decimal,
    ) -> None:
        conexao.execute(
            """INSERT INTO associacoes_produto
                   (id, estabelecimento_id, codigo_item, descricao_original,
                    descricao_normalizada, apresentacao_id, variacao_id, fator_conversao)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(estabelecimento_id, codigo_item) DO UPDATE SET
                   descricao_original = excluded.descricao_original,
                   descricao_normalizada = excluded.descricao_normalizada,
                   apresentacao_id = excluded.apresentacao_id,
                   variacao_id = excluded.variacao_id,
                   fator_conversao = excluded.fator_conversao""",
            (
                str(uuid4()), estabelecimento_id, codigo_item, descricao_original,
                normalizar_nome(descricao_original), apresentacao_id, variacao_id,
                decimal_texto(fator),
            ),
        )

    def _obter_nota(self, chave: str) -> Nota:
        nota = self.repositorio_notas.obter_por_chave(chave)
        if nota is None:
            raise NaoEncontrado("Nota não encontrada.")
        return nota
