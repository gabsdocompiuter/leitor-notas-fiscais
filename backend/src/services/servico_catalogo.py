from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session, sessionmaker

from ..core.exceptions import Conflito, DadosInvalidos, NaoEncontrado
from ..core.normalizacao import limpar_nome
from ..models.categoria import Categoria
from ..models.estabelecimento import Estabelecimento
from ..models.marca import Marca
from ..models.produto import Produto
from ..models.unidade_medida import UnidadeMedida
from ..models.variacao_produto import VariacaoProduto
from ..persistence.entities import (
    CategoriaEntity,
    MarcaEntity,
    ProdutoEntity,
    VariacaoProdutoEntity,
)
from ..persistence.mappers import (
    categoria_modelo,
    estabelecimento_modelo,
    marca_modelo,
    produto_modelo,
    variacao_modelo,
)
from ..persistence.repositories import (
    CategoriaRepository,
    EstabelecimentoRepository,
    MarcaRepository,
    ProdutoRepository,
    VariacaoProdutoRepository,
)


class ServicoCatalogo:
    """Regras dos catálogos e fronteira transacional de cada caso de uso."""

    def __init__(self, session_factory: sessionmaker[Session]):
        self.session_factory = session_factory

    @staticmethod
    def _nome(valor: str) -> str:
        nome = limpar_nome(valor)
        if not nome:
            raise DadosInvalidos("O nome não pode ficar vazio.")
        return nome

    def listar_categorias(self, busca: str | None = None) -> list[Categoria]:
        with self.session_factory() as session:
            entidades = CategoriaRepository(session).listar(
                limpar_nome(busca) if busca else None
            )
            return [categoria_modelo(item) for item in entidades]

    def obter_categoria(self, categoria_id: UUID) -> Categoria:
        with self.session_factory() as session:
            entidade = CategoriaRepository(session).obter(categoria_id)
            if entidade is None:
                raise NaoEncontrado("Categoria não encontrada.")
            return categoria_modelo(entidade)

    def criar_categoria(self, nome: str) -> Categoria:
        nome = self._nome(nome)
        with self.session_factory.begin() as session:
            repositorio = CategoriaRepository(session)
            entidade = repositorio.obter_por_nome(nome)
            if entidade is None:
                entidade = repositorio.adicionar(CategoriaEntity(nome=nome))
            return categoria_modelo(entidade)

    def atualizar_categoria(self, categoria_id: UUID, nome: str) -> Categoria:
        nome = self._nome(nome)
        with self.session_factory.begin() as session:
            repositorio = CategoriaRepository(session)
            entidade = repositorio.obter(categoria_id)
            if entidade is None:
                raise NaoEncontrado("Categoria não encontrada.")
            if repositorio.esta_em_nota_importada(categoria_id):
                raise Conflito("O cadastro pertence a uma nota importada e não pode ser alterado.")
            duplicada = repositorio.obter_por_nome(nome)
            if duplicada and duplicada.id != categoria_id:
                raise Conflito("Já existe uma categoria com esse nome.")
            entidade.nome = nome
            session.flush()
            return categoria_modelo(entidade)

    def excluir_categoria(self, categoria_id: UUID) -> None:
        with self.session_factory.begin() as session:
            repositorio = CategoriaRepository(session)
            entidade = repositorio.obter(categoria_id)
            if entidade is None:
                raise NaoEncontrado("Categoria não encontrada.")
            if repositorio.esta_em_nota_importada(categoria_id):
                raise Conflito("O cadastro pertence a uma nota importada e não pode ser alterado.")
            if repositorio.possui_produtos(categoria_id):
                raise Conflito("A categoria está vinculada a um produto.")
            repositorio.excluir(entidade)

    def listar_marcas(self, busca: str | None = None) -> list[Marca]:
        with self.session_factory() as session:
            return [
                marca_modelo(item)
                for item in MarcaRepository(session).listar(
                    limpar_nome(busca) if busca else None
                )
            ]

    def obter_marca(self, marca_id: UUID) -> Marca:
        with self.session_factory() as session:
            entidade = MarcaRepository(session).obter(marca_id)
            if entidade is None:
                raise NaoEncontrado("Marca não encontrada.")
            return marca_modelo(entidade)

    def criar_marca(self, nome: str) -> Marca:
        nome = self._nome(nome)
        with self.session_factory.begin() as session:
            repositorio = MarcaRepository(session)
            entidade = repositorio.obter_por_nome(nome)
            if entidade is None:
                entidade = repositorio.adicionar(MarcaEntity(nome=nome))
            return marca_modelo(entidade)

    def atualizar_marca(self, marca_id: UUID, nome: str) -> Marca:
        nome = self._nome(nome)
        with self.session_factory.begin() as session:
            repositorio = MarcaRepository(session)
            entidade = repositorio.obter(marca_id)
            if entidade is None:
                raise NaoEncontrado("Marca não encontrada.")
            if repositorio.esta_em_nota_importada(marca_id):
                raise Conflito("O cadastro pertence a uma nota importada e não pode ser alterado.")
            duplicada = repositorio.obter_por_nome(nome)
            if duplicada and duplicada.id != marca_id:
                raise Conflito("Já existe uma marca com esse nome.")
            entidade.nome = nome
            session.flush()
            return marca_modelo(entidade)

    def excluir_marca(self, marca_id: UUID) -> None:
        with self.session_factory.begin() as session:
            repositorio = MarcaRepository(session)
            entidade = repositorio.obter(marca_id)
            if entidade is None:
                raise NaoEncontrado("Marca não encontrada.")
            if repositorio.esta_em_nota_importada(marca_id):
                raise Conflito("O cadastro pertence a uma nota importada e não pode ser alterado.")
            if repositorio.possui_apresentacoes(marca_id):
                raise Conflito("A marca está vinculada a uma apresentação.")
            repositorio.excluir(entidade)

    def listar_produtos(
        self, busca: str | None = None, categoria_id: UUID | None = None
    ) -> list[Produto]:
        with self.session_factory() as session:
            entidades = ProdutoRepository(session).listar(
                limpar_nome(busca) if busca else None, categoria_id
            )
            return [produto_modelo(item) for item in entidades]

    def obter_produto(self, produto_id: UUID) -> Produto:
        with self.session_factory() as session:
            entidade = ProdutoRepository(session).obter(produto_id)
            if entidade is None:
                raise NaoEncontrado("Produto não encontrado.")
            return produto_modelo(entidade)

    def criar_produto(
        self,
        nome: str,
        categoria_id: UUID,
        nao_solicitar_marca: bool,
        tratar_apenas_como_unidades: bool,
        contem_variacoes: bool,
        unidade_medida: UnidadeMedida | None,
    ) -> Produto:
        self._validar_tipo_produto(
            tratar_apenas_como_unidades, contem_variacoes, unidade_medida
        )
        nome = self._nome(nome)
        with self.session_factory.begin() as session:
            categorias = CategoriaRepository(session)
            categoria = categorias.obter(categoria_id)
            if categoria is None:
                raise NaoEncontrado("Categoria não encontrada.")
            repositorio = ProdutoRepository(session)
            entidade = repositorio.obter_por_identidade(nome, categoria_id)
            if entidade is None:
                entidade = repositorio.adicionar(
                    ProdutoEntity(
                        nome=nome,
                        categoria=categoria,
                        nao_solicitar_marca=nao_solicitar_marca,
                        tratar_apenas_como_unidades=tratar_apenas_como_unidades,
                        contem_variacoes=contem_variacoes,
                        unidade_medida=unidade_medida,
                    )
                )
            return produto_modelo(entidade)

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
        self._validar_tipo_produto(
            tratar_apenas_como_unidades, contem_variacoes, unidade_medida
        )
        nome = self._nome(nome)
        with self.session_factory.begin() as session:
            repositorio = ProdutoRepository(session)
            entidade = repositorio.obter(produto_id)
            if entidade is None:
                raise NaoEncontrado("Produto não encontrado.")
            if repositorio.esta_em_nota_importada(produto_id):
                raise Conflito("O cadastro pertence a uma nota importada e não pode ser alterado.")
            categoria = CategoriaRepository(session).obter(categoria_id)
            if categoria is None:
                raise NaoEncontrado("Categoria não encontrada.")
            duplicado = repositorio.obter_por_identidade(nome, categoria_id)
            if duplicado and duplicado.id != produto_id:
                raise Conflito("Já existe esse produto na categoria e unidade informadas.")
            entidade.nome = nome
            entidade.categoria = categoria
            entidade.nao_solicitar_marca = nao_solicitar_marca
            entidade.tratar_apenas_como_unidades = tratar_apenas_como_unidades
            entidade.contem_variacoes = contem_variacoes
            entidade.unidade_medida = unidade_medida
            session.flush()
            return produto_modelo(entidade)

    def excluir_produto(self, produto_id: UUID) -> None:
        with self.session_factory.begin() as session:
            repositorio = ProdutoRepository(session)
            entidade = repositorio.obter(produto_id)
            if entidade is None:
                raise NaoEncontrado("Produto não encontrado.")
            if repositorio.esta_em_nota_importada(produto_id):
                raise Conflito("O cadastro pertence a uma nota importada e não pode ser alterado.")
            if repositorio.possui_apresentacoes(produto_id):
                raise Conflito("O produto está vinculado a uma apresentação.")
            repositorio.excluir(entidade)

    def listar_variacoes(self, produto_id: UUID) -> list[VariacaoProduto]:
        with self.session_factory() as session:
            if ProdutoRepository(session).obter(produto_id) is None:
                raise NaoEncontrado("Produto não encontrado.")
            return [
                variacao_modelo(item)
                for item in VariacaoProdutoRepository(session).listar_por_produto(produto_id)
            ]

    def obter_variacao(self, variacao_id: UUID) -> VariacaoProduto:
        with self.session_factory() as session:
            entidade = VariacaoProdutoRepository(session).obter(variacao_id)
            if entidade is None:
                raise NaoEncontrado("Variação não encontrada.")
            return variacao_modelo(entidade)

    def criar_variacao(
        self, produto_id: UUID, quantidade: Decimal,
        unidade_medida: UnidadeMedida, descricao: str | None,
    ) -> VariacaoProduto:
        with self.session_factory.begin() as session:
            produto = ProdutoRepository(session).obter(produto_id)
            if produto is None:
                raise NaoEncontrado("Produto não encontrado.")
            if not produto.contem_variacoes:
                raise Conflito("O produto não está configurado para possuir variações.")
            repositorio = VariacaoProdutoRepository(session)
            entidade = repositorio.obter_por_identidade(
                produto_id, quantidade, unidade_medida
            )
            if entidade is None:
                entidade = repositorio.adicionar(
                    VariacaoProdutoEntity(
                        produto=produto, quantidade=quantidade,
                        unidade_medida=unidade_medida,
                        descricao=self._descricao_opcional(descricao),
                    )
                )
            return variacao_modelo(entidade)

    def atualizar_variacao(
        self, variacao_id: UUID, quantidade: Decimal,
        unidade_medida: UnidadeMedida, descricao: str | None,
    ) -> VariacaoProduto:
        with self.session_factory.begin() as session:
            repositorio = VariacaoProdutoRepository(session)
            entidade = repositorio.obter(variacao_id)
            if entidade is None:
                raise NaoEncontrado("Variação não encontrada.")
            if repositorio.esta_em_nota_importada(variacao_id):
                raise Conflito("A variação pertence a uma nota importada e não pode ser alterada.")
            duplicada = repositorio.obter_por_identidade(
                entidade.produto_id, quantidade, unidade_medida
            )
            if duplicada and duplicada.id != variacao_id:
                raise Conflito("Já existe essa variação para o produto.")
            entidade.quantidade = quantidade
            entidade.unidade_medida = unidade_medida
            entidade.descricao = self._descricao_opcional(descricao)
            session.flush()
            return variacao_modelo(entidade)

    def listar_estabelecimentos(self, busca: str | None = None) -> list[Estabelecimento]:
        with self.session_factory() as session:
            entidades = EstabelecimentoRepository(session).listar(
                limpar_nome(busca) if busca else None
            )
            return [estabelecimento_modelo(item) for item in entidades]

    def obter_estabelecimento(self, estabelecimento_id: UUID) -> Estabelecimento:
        with self.session_factory() as session:
            entidade = EstabelecimentoRepository(session).obter(estabelecimento_id)
            if entidade is None:
                raise NaoEncontrado("Estabelecimento não encontrado.")
            return estabelecimento_modelo(entidade)

    def atualizar_apelido_estabelecimento(
        self, estabelecimento_id: UUID, apelido: str | None
    ) -> Estabelecimento:
        with self.session_factory.begin() as session:
            entidade = EstabelecimentoRepository(session).obter(estabelecimento_id)
            if entidade is None:
                raise NaoEncontrado("Estabelecimento não encontrado.")
            entidade.apelido = self._descricao_opcional(apelido)
            session.flush()
            return estabelecimento_modelo(entidade)

    @staticmethod
    def _descricao_opcional(valor: str | None) -> str | None:
        descricao = limpar_nome(valor) if valor else ""
        return descricao or None

    @staticmethod
    def _validar_tipo_produto(
        tratar_apenas_como_unidades: bool,
        contem_variacoes: bool,
        unidade_medida: UnidadeMedida | None,
    ) -> None:
        if tratar_apenas_como_unidades:
            if contem_variacoes or unidade_medida is not None:
                raise DadosInvalidos(
                    "Produtos tratados como unidades não aceitam variações ou unidade de medida."
                )
        elif unidade_medida is None:
            raise DadosInvalidos("A unidade de medida é obrigatória para este produto.")
