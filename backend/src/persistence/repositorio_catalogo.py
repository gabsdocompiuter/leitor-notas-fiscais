import sqlite3
from uuid import UUID

from ..core.exceptions import Conflito, NaoEncontrado
from ..models.categoria import Categoria
from ..models.marca import Marca
from ..models.produto import Produto
from ..models.unidade_medida import UnidadeMedida
from .banco_sqlite import BancoSQLite


class RepositorioCatalogo:
    def __init__(self, banco: BancoSQLite):
        self.banco = banco
        self.banco.inicializar()

    def listar_categorias(self, busca: str | None = None) -> list[Categoria]:
        consulta = "SELECT * FROM categorias"
        parametros: tuple[object, ...] = ()
        if busca:
            consulta += " WHERE nome LIKE ? COLLATE NOCASE"
            parametros = (f"%{busca}%",)
        consulta += " ORDER BY nome COLLATE NOCASE"
        with self.banco.conectar() as conexao:
            return [self._categoria(linha) for linha in conexao.execute(consulta, parametros)]

    def obter_categoria(self, categoria_id: UUID) -> Categoria:
        with self.banco.conectar() as conexao:
            linha = conexao.execute(
                "SELECT * FROM categorias WHERE id = ?", (str(categoria_id),)
            ).fetchone()
            if linha is None:
                raise NaoEncontrado("Categoria não encontrada.")
            return self._categoria(linha)

    def criar_categoria(self, categoria: Categoria) -> Categoria:
        with self.banco.conectar() as conexao:
            existente = conexao.execute(
                "SELECT * FROM categorias WHERE nome = ? COLLATE NOCASE", (categoria.nome,)
            ).fetchone()
            if existente:
                return self._categoria(existente)
            conexao.execute(
                "INSERT INTO categorias (id, nome) VALUES (?, ?)",
                (str(categoria.id), categoria.nome),
            )
        return categoria

    def atualizar_categoria(self, categoria_id: UUID, nome: str) -> Categoria:
        with self.banco.conectar() as conexao:
            self._exigir_nao_importada(conexao, "categoria", categoria_id)
            duplicada = conexao.execute(
                "SELECT id FROM categorias WHERE nome = ? COLLATE NOCASE AND id <> ?",
                (nome, str(categoria_id)),
            ).fetchone()
            if duplicada:
                raise Conflito("Já existe uma categoria com esse nome.")
            alteracao = conexao.execute(
                "UPDATE categorias SET nome = ? WHERE id = ?", (nome, str(categoria_id))
            )
            if alteracao.rowcount != 1:
                raise NaoEncontrado("Categoria não encontrada.")
        return self.obter_categoria(categoria_id)

    def excluir_categoria(self, categoria_id: UUID) -> None:
        with self.banco.conectar() as conexao:
            self._exigir_nao_importada(conexao, "categoria", categoria_id)
            if conexao.execute(
                "SELECT 1 FROM produtos WHERE categoria_id = ? LIMIT 1", (str(categoria_id),)
            ).fetchone():
                raise Conflito("A categoria está vinculada a um produto.")
            exclusao = conexao.execute(
                "DELETE FROM categorias WHERE id = ?", (str(categoria_id),)
            )
            if exclusao.rowcount != 1:
                raise NaoEncontrado("Categoria não encontrada.")

    def listar_marcas(self, busca: str | None = None) -> list[Marca]:
        consulta = "SELECT * FROM marcas"
        parametros: tuple[object, ...] = ()
        if busca:
            consulta += " WHERE nome LIKE ? COLLATE NOCASE"
            parametros = (f"%{busca}%",)
        consulta += " ORDER BY nome COLLATE NOCASE"
        with self.banco.conectar() as conexao:
            return [self._marca(linha) for linha in conexao.execute(consulta, parametros)]

    def obter_marca(self, marca_id: UUID) -> Marca:
        with self.banco.conectar() as conexao:
            linha = conexao.execute(
                "SELECT * FROM marcas WHERE id = ?", (str(marca_id),)
            ).fetchone()
            if linha is None:
                raise NaoEncontrado("Marca não encontrada.")
            return self._marca(linha)

    def criar_marca(self, marca: Marca) -> Marca:
        with self.banco.conectar() as conexao:
            existente = conexao.execute(
                "SELECT * FROM marcas WHERE nome = ? COLLATE NOCASE", (marca.nome,)
            ).fetchone()
            if existente:
                return self._marca(existente)
            conexao.execute(
                "INSERT INTO marcas (id, nome) VALUES (?, ?)",
                (str(marca.id), marca.nome),
            )
        return marca

    def atualizar_marca(self, marca_id: UUID, nome: str) -> Marca:
        with self.banco.conectar() as conexao:
            self._exigir_nao_importada(conexao, "marca", marca_id)
            duplicada = conexao.execute(
                "SELECT id FROM marcas WHERE nome = ? COLLATE NOCASE AND id <> ?",
                (nome, str(marca_id)),
            ).fetchone()
            if duplicada:
                raise Conflito("Já existe uma marca com esse nome.")
            alteracao = conexao.execute(
                "UPDATE marcas SET nome = ? WHERE id = ?", (nome, str(marca_id))
            )
            if alteracao.rowcount != 1:
                raise NaoEncontrado("Marca não encontrada.")
        return self.obter_marca(marca_id)

    def excluir_marca(self, marca_id: UUID) -> None:
        with self.banco.conectar() as conexao:
            self._exigir_nao_importada(conexao, "marca", marca_id)
            if conexao.execute(
                "SELECT 1 FROM apresentacoes_produto WHERE marca_id = ? LIMIT 1",
                (str(marca_id),),
            ).fetchone():
                raise Conflito("A marca está vinculada a uma apresentação.")
            exclusao = conexao.execute("DELETE FROM marcas WHERE id = ?", (str(marca_id),))
            if exclusao.rowcount != 1:
                raise NaoEncontrado("Marca não encontrada.")

    def listar_produtos(
        self, busca: str | None = None, categoria_id: UUID | None = None
    ) -> list[Produto]:
        consulta = """
            SELECT p.*, c.nome AS categoria_nome
            FROM produtos p JOIN categorias c ON c.id = p.categoria_id
        """
        filtros: list[str] = []
        parametros: list[object] = []
        if busca:
            filtros.append("p.nome LIKE ? COLLATE NOCASE")
            parametros.append(f"%{busca}%")
        if categoria_id:
            filtros.append("p.categoria_id = ?")
            parametros.append(str(categoria_id))
        if filtros:
            consulta += " WHERE " + " AND ".join(filtros)
        consulta += " ORDER BY p.nome COLLATE NOCASE"
        with self.banco.conectar() as conexao:
            return [self._produto(linha) for linha in conexao.execute(consulta, parametros)]

    def obter_produto(self, produto_id: UUID) -> Produto:
        with self.banco.conectar() as conexao:
            linha = conexao.execute(
                """
                SELECT p.*, c.nome AS categoria_nome
                FROM produtos p JOIN categorias c ON c.id = p.categoria_id
                WHERE p.id = ?
                """,
                (str(produto_id),),
            ).fetchone()
            if linha is None:
                raise NaoEncontrado("Produto não encontrado.")
            return self._produto(linha)

    def criar_produto(self, produto: Produto) -> Produto:
        with self.banco.conectar() as conexao:
            categoria = conexao.execute(
                "SELECT id FROM categorias WHERE id = ?", (str(produto.categoria.id),)
            ).fetchone()
            if categoria is None:
                raise NaoEncontrado("Categoria não encontrada.")
            existente = conexao.execute(
                """
                SELECT p.*, c.nome AS categoria_nome
                FROM produtos p JOIN categorias c ON c.id = p.categoria_id
                WHERE p.nome = ? COLLATE NOCASE AND p.categoria_id = ? AND p.unidade_base = ?
                """,
                (produto.nome, str(produto.categoria.id), produto.unidade_base.value),
            ).fetchone()
            if existente:
                return self._produto(existente)
            conexao.execute(
                "INSERT INTO produtos (id, nome, categoria_id, unidade_base) VALUES (?, ?, ?, ?)",
                (str(produto.id), produto.nome, str(produto.categoria.id), produto.unidade_base.value),
            )
        return self.obter_produto(produto.id)

    def atualizar_produto(
        self, produto_id: UUID, nome: str, categoria_id: UUID, unidade_base: UnidadeMedida
    ) -> Produto:
        with self.banco.conectar() as conexao:
            self._exigir_nao_importada(conexao, "produto", produto_id)
            if conexao.execute(
                "SELECT id FROM categorias WHERE id = ?", (str(categoria_id),)
            ).fetchone() is None:
                raise NaoEncontrado("Categoria não encontrada.")
            duplicado = conexao.execute(
                """
                SELECT id FROM produtos
                WHERE nome = ? COLLATE NOCASE AND categoria_id = ? AND unidade_base = ? AND id <> ?
                """,
                (nome, str(categoria_id), unidade_base.value, str(produto_id)),
            ).fetchone()
            if duplicado:
                raise Conflito("Já existe esse produto na categoria e unidade informadas.")
            alteracao = conexao.execute(
                "UPDATE produtos SET nome = ?, categoria_id = ?, unidade_base = ? WHERE id = ?",
                (nome, str(categoria_id), unidade_base.value, str(produto_id)),
            )
            if alteracao.rowcount != 1:
                raise NaoEncontrado("Produto não encontrado.")
        return self.obter_produto(produto_id)

    def excluir_produto(self, produto_id: UUID) -> None:
        with self.banco.conectar() as conexao:
            self._exigir_nao_importada(conexao, "produto", produto_id)
            if conexao.execute(
                "SELECT 1 FROM apresentacoes_produto WHERE produto_id = ? LIMIT 1",
                (str(produto_id),),
            ).fetchone():
                raise Conflito("O produto está vinculado a uma apresentação.")
            exclusao = conexao.execute(
                "DELETE FROM produtos WHERE id = ?", (str(produto_id),)
            )
            if exclusao.rowcount != 1:
                raise NaoEncontrado("Produto não encontrado.")

    @staticmethod
    def _categoria(linha: sqlite3.Row) -> Categoria:
        return Categoria(id=UUID(linha["id"]), nome=linha["nome"])

    @staticmethod
    def _marca(linha: sqlite3.Row) -> Marca:
        return Marca(id=UUID(linha["id"]), nome=linha["nome"])

    @staticmethod
    def _produto(linha: sqlite3.Row) -> Produto:
        return Produto(
            id=UUID(linha["id"]),
            nome=linha["nome"],
            categoria=Categoria(id=UUID(linha["categoria_id"]), nome=linha["categoria_nome"]),
            unidade_base=UnidadeMedida(linha["unidade_base"]),
        )

    @staticmethod
    def _exigir_nao_importada(
        conexao: sqlite3.Connection, tipo: str, entidade_id: UUID
    ) -> None:
        filtros = {
            "categoria": "p.categoria_id = ?",
            "produto": "p.id = ?",
            "marca": "a.marca_id = ?",
        }
        encontrada = conexao.execute(
            f"""
            SELECT 1
            FROM itens i
            JOIN notas n ON n.id = i.nota_id
            JOIN apresentacoes_produto a ON a.id = i.apresentacao_id
            JOIN produtos p ON p.id = a.produto_id
            WHERE n.situacao = 'importada' AND {filtros[tipo]}
            LIMIT 1
            """,
            (str(entidade_id),),
        ).fetchone()
        if encontrada:
            raise Conflito("O cadastro pertence a uma nota importada e não pode ser alterado.")
