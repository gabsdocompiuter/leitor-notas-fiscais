import sqlite3
from decimal import Decimal
from uuid import UUID

from ..core.exceptions import Conflito, NaoEncontrado
from ..models.categoria import Categoria
from ..models.estabelecimento import Estabelecimento
from ..models.marca import Marca
from ..models.produto import Produto
from ..models.unidade_medida import UnidadeMedida
from ..models.variacao_produto import VariacaoProduto
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
                WHERE p.nome = ? COLLATE NOCASE AND p.categoria_id = ?
                """,
                (produto.nome, str(produto.categoria.id)),
            ).fetchone()
            if existente:
                return self._produto(existente)
            conexao.execute(
                """INSERT INTO produtos
                    (id, nome, categoria_id, nao_solicitar_marca,
                     tratar_apenas_como_unidades, contem_variacoes, unidade_medida)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(produto.id),
                    produto.nome,
                    str(produto.categoria.id),
                    int(produto.nao_solicitar_marca),
                    int(produto.tratar_apenas_como_unidades),
                    int(produto.contem_variacoes),
                    produto.unidade_medida.value if produto.unidade_medida else None,
                ),
            )
        return self.obter_produto(produto.id)

    def atualizar_produto(
        self,
        produto_id: UUID,
        nome: str,
        categoria_id: UUID,
        nao_solicitar_marca: bool,
        tratar_apenas_como_unidades: bool,
        contem_variacoes: bool,
        unidade_medida: UnidadeMedida | None,
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
                WHERE nome = ? COLLATE NOCASE AND categoria_id = ? AND id <> ?
                """,
                (nome, str(categoria_id), str(produto_id)),
            ).fetchone()
            if duplicado:
                raise Conflito("Já existe esse produto na categoria e unidade informadas.")
            alteracao = conexao.execute(
                """UPDATE produtos
                   SET nome = ?, categoria_id = ?, nao_solicitar_marca = ?,
                       tratar_apenas_como_unidades = ?, contem_variacoes = ?, unidade_medida = ?
                   WHERE id = ?""",
                (
                    nome,
                    str(categoria_id),
                    int(nao_solicitar_marca),
                    int(tratar_apenas_como_unidades),
                    int(contem_variacoes),
                    unidade_medida.value if unidade_medida else None,
                    str(produto_id),
                ),
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
            nao_solicitar_marca=bool(linha["nao_solicitar_marca"]),
            tratar_apenas_como_unidades=bool(linha["tratar_apenas_como_unidades"]),
            contem_variacoes=bool(linha["contem_variacoes"]),
            unidade_medida=(
                UnidadeMedida(linha["unidade_medida"])
                if linha["unidade_medida"]
                else None
            ),
        )

    def listar_variacoes(self, produto_id: UUID) -> list[VariacaoProduto]:
        produto = self.obter_produto(produto_id)
        with self.banco.conectar() as conexao:
            linhas = conexao.execute(
                """SELECT * FROM variacoes_produto
                   WHERE produto_id = ?
                   ORDER BY CAST(quantidade AS REAL), unidade_medida, descricao""",
                (str(produto_id),),
            ).fetchall()
        return [self._variacao(linha, produto) for linha in linhas]

    def obter_variacao(self, variacao_id: UUID) -> VariacaoProduto:
        with self.banco.conectar() as conexao:
            linha = conexao.execute(
                "SELECT * FROM variacoes_produto WHERE id = ?", (str(variacao_id),)
            ).fetchone()
        if linha is None:
            raise NaoEncontrado("Variação não encontrada.")
        return self._variacao(linha, self.obter_produto(UUID(linha["produto_id"])))

    def salvar_variacao(self, variacao: VariacaoProduto) -> VariacaoProduto:
        if not variacao.produto.contem_variacoes:
            raise Conflito("O produto não está configurado para possuir variações.")
        with self.banco.conectar() as conexao:
            existente = conexao.execute(
                """SELECT id FROM variacoes_produto
                   WHERE produto_id = ? AND quantidade = ? AND unidade_medida = ?""",
                (
                    str(variacao.produto.id),
                    str(variacao.quantidade),
                    variacao.unidade_medida.value,
                ),
            ).fetchone()
            if existente:
                return self.obter_variacao(UUID(existente["id"]))
            conexao.execute(
                """INSERT INTO variacoes_produto
                   (id, produto_id, quantidade, unidade_medida, descricao)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    str(variacao.id),
                    str(variacao.produto.id),
                    str(variacao.quantidade),
                    variacao.unidade_medida.value,
                    variacao.descricao,
                ),
            )
        return variacao

    def atualizar_variacao(
        self,
        variacao_id: UUID,
        quantidade: Decimal,
        unidade_medida: UnidadeMedida,
        descricao: str | None,
    ) -> VariacaoProduto:
        atual = self.obter_variacao(variacao_id)
        with self.banco.conectar() as conexao:
            if conexao.execute(
                """SELECT 1 FROM itens i
                   JOIN notas n ON n.id = i.nota_id
                   WHERE n.situacao = 'importada' AND i.variacao_id = ? LIMIT 1""",
                (str(variacao_id),),
            ).fetchone():
                raise Conflito(
                    "A variação pertence a uma nota importada e não pode ser alterada."
                )
            duplicada = conexao.execute(
                """SELECT id FROM variacoes_produto
                   WHERE produto_id = ? AND quantidade = ?
                     AND unidade_medida = ? AND id <> ?""",
                (
                    str(atual.produto.id), str(quantidade), unidade_medida.value,
                    str(variacao_id),
                ),
            ).fetchone()
            if duplicada:
                raise Conflito("Já existe essa variação para o produto.")
            conexao.execute(
                """UPDATE variacoes_produto
                   SET quantidade = ?, unidade_medida = ?, descricao = ? WHERE id = ?""",
                (str(quantidade), unidade_medida.value, descricao, str(variacao_id)),
            )
        return VariacaoProduto(
            id=variacao_id,
            produto=atual.produto,
            quantidade=quantidade,
            unidade_medida=unidade_medida,
            descricao=descricao,
        )

    def listar_estabelecimentos(self, busca: str | None = None) -> list[Estabelecimento]:
        consulta = "SELECT * FROM estabelecimentos"
        parametros: tuple[object, ...] = ()
        if busca:
            consulta += " WHERE razao_social LIKE ? COLLATE NOCASE OR apelido LIKE ? COLLATE NOCASE"
            parametros = (f"%{busca}%", f"%{busca}%")
        consulta += " ORDER BY COALESCE(apelido, razao_social) COLLATE NOCASE"
        with self.banco.conectar() as conexao:
            return [self._estabelecimento(linha) for linha in conexao.execute(consulta, parametros)]

    def obter_estabelecimento(self, estabelecimento_id: UUID) -> Estabelecimento:
        with self.banco.conectar() as conexao:
            linha = conexao.execute(
                "SELECT * FROM estabelecimentos WHERE id = ?",
                (str(estabelecimento_id),),
            ).fetchone()
        if linha is None:
            raise NaoEncontrado("Estabelecimento não encontrado.")
        return self._estabelecimento(linha)

    def atualizar_apelido_estabelecimento(
        self, estabelecimento_id: UUID, apelido: str | None
    ) -> Estabelecimento:
        with self.banco.conectar() as conexao:
            alteracao = conexao.execute(
                "UPDATE estabelecimentos SET apelido = ? WHERE id = ?",
                (apelido, str(estabelecimento_id)),
            )
            if alteracao.rowcount != 1:
                raise NaoEncontrado("Estabelecimento não encontrado.")
            linha = conexao.execute(
                "SELECT * FROM estabelecimentos WHERE id = ?", (str(estabelecimento_id),)
            ).fetchone()
        return self._estabelecimento(linha)

    @staticmethod
    def _variacao(linha: sqlite3.Row, produto: Produto) -> VariacaoProduto:
        return VariacaoProduto(
            id=UUID(linha["id"]),
            produto=produto,
            quantidade=Decimal(linha["quantidade"]),
            unidade_medida=UnidadeMedida(linha["unidade_medida"]),
            descricao=linha["descricao"],
        )

    @staticmethod
    def _estabelecimento(linha: sqlite3.Row) -> Estabelecimento:
        return Estabelecimento(
            id=UUID(linha["id"]),
            cnpj=linha["cnpj"],
            razao_social=linha["razao_social"],
            apelido=linha["apelido"],
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
