from uuid import UUID

from ..core.exceptions import DadosInvalidos
from ..core.normalizacao import limpar_nome
from ..models.categoria import Categoria
from ..models.marca import Marca
from ..models.produto import Produto
from ..models.unidade_medida import UnidadeMedida
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
        self, nome: str, categoria_id: UUID, unidade_base: UnidadeMedida
    ) -> Produto:
        categoria = self.repositorio.obter_categoria(categoria_id)
        return self.repositorio.criar_produto(
            Produto(self._nome(nome), categoria, unidade_base)
        )

    def atualizar_produto(
        self, produto_id: UUID, nome: str, categoria_id: UUID, unidade_base: UnidadeMedida
    ) -> Produto:
        return self.repositorio.atualizar_produto(
            produto_id, self._nome(nome), categoria_id, unidade_base
        )

    def excluir_produto(self, produto_id: UUID) -> None:
        self.repositorio.excluir_produto(produto_id)
