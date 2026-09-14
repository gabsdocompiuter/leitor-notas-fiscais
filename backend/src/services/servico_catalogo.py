from decimal import Decimal
from uuid import UUID

from ..core.exceptions import DadosInvalidos
from ..core.normalizacao import limpar_nome
from ..models.categoria import Categoria
from ..models.estabelecimento import Estabelecimento
from ..models.marca import Marca
from ..models.produto import Produto
from ..models.unidade_medida import UnidadeMedida
from ..models.variacao_produto import VariacaoProduto
from ..persistence.repositorio_catalogo import RepositorioCatalogo


class ServicoCatalogo:
    def __init__(self, repositorio: RepositorioCatalogo):
        self.repositorio = repositorio

    @staticmethod
    def _nome(valor: str) -> str:
        nome = limpar_nome(valor)
        if not nome:
            raise DadosInvalidos("O nome não pode ficar vazio.")
        return nome

    def listar_categorias(self, busca: str | None = None) -> list[Categoria]:
        return self.repositorio.listar_categorias(limpar_nome(busca) if busca else None)

    def obter_categoria(self, categoria_id: UUID) -> Categoria:
        return self.repositorio.obter_categoria(categoria_id)

    def criar_categoria(self, nome: str) -> Categoria:
        return self.repositorio.criar_categoria(Categoria(self._nome(nome)))

    def atualizar_categoria(self, categoria_id: UUID, nome: str) -> Categoria:
        return self.repositorio.atualizar_categoria(categoria_id, self._nome(nome))

    def excluir_categoria(self, categoria_id: UUID) -> None:
        self.repositorio.excluir_categoria(categoria_id)

    def listar_marcas(self, busca: str | None = None) -> list[Marca]:
        return self.repositorio.listar_marcas(limpar_nome(busca) if busca else None)

    def obter_marca(self, marca_id: UUID) -> Marca:
        return self.repositorio.obter_marca(marca_id)

    def criar_marca(self, nome: str) -> Marca:
        return self.repositorio.criar_marca(Marca(self._nome(nome)))

    def atualizar_marca(self, marca_id: UUID, nome: str) -> Marca:
        return self.repositorio.atualizar_marca(marca_id, self._nome(nome))

    def excluir_marca(self, marca_id: UUID) -> None:
        self.repositorio.excluir_marca(marca_id)

    def listar_produtos(
        self, busca: str | None = None, categoria_id: UUID | None = None
    ) -> list[Produto]:
        return self.repositorio.listar_produtos(
            limpar_nome(busca) if busca else None, categoria_id
        )

    def obter_produto(self, produto_id: UUID) -> Produto:
        return self.repositorio.obter_produto(produto_id)

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
        categoria = self.repositorio.obter_categoria(categoria_id)
        return self.repositorio.criar_produto(
            Produto(
                self._nome(nome),
                categoria,
                nao_solicitar_marca,
                tratar_apenas_como_unidades,
                contem_variacoes,
                unidade_medida,
            )
        )

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
        return self.repositorio.atualizar_produto(
            produto_id,
            self._nome(nome),
            categoria_id,
            nao_solicitar_marca,
            tratar_apenas_como_unidades,
            contem_variacoes,
            unidade_medida,
        )

    def excluir_produto(self, produto_id: UUID) -> None:
        self.repositorio.excluir_produto(produto_id)

    def listar_variacoes(self, produto_id: UUID) -> list[VariacaoProduto]:
        return self.repositorio.listar_variacoes(produto_id)

    def obter_variacao(self, variacao_id: UUID) -> VariacaoProduto:
        return self.repositorio.obter_variacao(variacao_id)

    def criar_variacao(
        self,
        produto_id: UUID,
        quantidade: Decimal,
        unidade_medida: UnidadeMedida,
        descricao: str | None,
    ) -> VariacaoProduto:
        produto = self.repositorio.obter_produto(produto_id)
        return self.repositorio.salvar_variacao(
            VariacaoProduto(
                produto,
                quantidade,
                unidade_medida,
                self._descricao_opcional(descricao),
            )
        )

    def atualizar_variacao(
        self,
        variacao_id: UUID,
        quantidade: Decimal,
        unidade_medida: UnidadeMedida,
        descricao: str | None,
    ) -> VariacaoProduto:
        return self.repositorio.atualizar_variacao(
            variacao_id,
            quantidade,
            unidade_medida,
            self._descricao_opcional(descricao),
        )

    def listar_estabelecimentos(self, busca: str | None = None) -> list[Estabelecimento]:
        return self.repositorio.listar_estabelecimentos(
            limpar_nome(busca) if busca else None
        )

    def atualizar_apelido_estabelecimento(
        self, estabelecimento_id: UUID, apelido: str | None
    ) -> Estabelecimento:
        return self.repositorio.atualizar_apelido_estabelecimento(
            estabelecimento_id, self._descricao_opcional(apelido)
        )

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
