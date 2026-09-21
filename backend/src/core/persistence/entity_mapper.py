from datetime import timezone

from ...dtos.apresentacao_produto_dto import ApresentacaoProdutoDTO
from ...dtos.categoria_dto import CategoriaDTO
from ...dtos.estabelecimento_dto import EstabelecimentoDTO
from ...dtos.item_dto import ItemDTO
from ...dtos.leitura_nota_dto import LeituraNotaDTO
from ...dtos.marca_dto import MarcaDTO
from ...dtos.nota_dto import NotaDTO
from ...dtos.produto_dto import ProdutoDTO
from ...dtos.variacao_produto_dto import VariacaoProdutoDTO
from ...entities import (
    ApresentacaoProdutoEntity,
    CategoriaEntity,
    EstabelecimentoEntity,
    ItemEntity,
    LeituraNotaEntity,
    MarcaEntity,
    NotaEntity,
    ProdutoEntity,
    VariacaoProdutoEntity,
)


class EntityMapper:
    """Converte entidades persistentes em DTOs sem expor sessões ORM."""

    @staticmethod
    def categoria(entidade: CategoriaEntity) -> CategoriaDTO:
        return CategoriaDTO(id=entidade.id, nome=entidade.nome)

    @staticmethod
    def marca(entidade: MarcaEntity) -> MarcaDTO:
        return MarcaDTO(id=entidade.id, nome=entidade.nome)

    @staticmethod
    def estabelecimento(entidade: EstabelecimentoEntity) -> EstabelecimentoDTO:
        return EstabelecimentoDTO(
            id=entidade.id,
            cnpj=entidade.cnpj,
            razao_social=entidade.razao_social,
            apelido=entidade.apelido,
        )

    @classmethod
    def produto(cls, entidade: ProdutoEntity) -> ProdutoDTO:
        return ProdutoDTO(
            id=entidade.id,
            nome=entidade.nome,
            categoria=cls.categoria(entidade.categoria),
            nao_solicitar_marca=entidade.nao_solicitar_marca,
            tratar_apenas_como_unidades=entidade.tratar_apenas_como_unidades,
            contem_variacoes=entidade.contem_variacoes,
            unidade_medida=entidade.unidade_medida,
        )

    @classmethod
    def variacao(cls, entidade: VariacaoProdutoEntity) -> VariacaoProdutoDTO:
        return VariacaoProdutoDTO(
            id=entidade.id,
            produto=cls.produto(entidade.produto),
            quantidade=entidade.quantidade,
            unidade_medida=entidade.unidade_medida,
            descricao=entidade.descricao,
        )

    @classmethod
    def apresentacao(
        cls, entidade: ApresentacaoProdutoEntity
    ) -> ApresentacaoProdutoDTO:
        return ApresentacaoProdutoDTO(
            id=entidade.id,
            produto=cls.produto(entidade.produto),
            marca=cls.marca(entidade.marca) if entidade.marca else None,
        )

    @classmethod
    def item(cls, entidade: ItemEntity) -> ItemDTO:
        return ItemDTO(
            id=entidade.id,
            numero=entidade.numero,
            codigo=entidade.codigo,
            descricao_original=entidade.descricao_original,
            quantidade=entidade.quantidade,
            unidade_original=entidade.unidade_original,
            valor_unitario=entidade.valor_unitario,
            valor_total=entidade.valor_total,
            alertas=entidade.alertas,
            apresentacao=(
                cls.apresentacao(entidade.apresentacao)
                if entidade.apresentacao
                else None
            ),
            variacao=cls.variacao(entidade.variacao) if entidade.variacao else None,
            quantidade_confirmada=entidade.quantidade_confirmada,
            revisado=entidade.revisado,
        )

    @classmethod
    def nota(cls, entidade: NotaEntity) -> NotaDTO:
        return NotaDTO(
            id=entidade.id,
            chave=entidade.chave,
            numero=entidade.numero,
            serie=entidade.serie,
            estabelecimento=cls.estabelecimento(entidade.estabelecimento),
            emissao=entidade.emissao,
            quantidade_itens=entidade.quantidade_itens,
            valor_total=entidade.valor_total,
            desconto=entidade.desconto,
            valor_a_pagar=entidade.valor_a_pagar,
            itens=[cls.item(item) for item in entidade.itens],
            url_origem=entidade.url_origem,
            situacao=entidade.situacao,
            importada_em=entidade.importada_em,
        )

    @classmethod
    def leitura(cls, entidade: LeituraNotaEntity) -> LeituraNotaDTO:
        criada_em = entidade.criada_em
        if criada_em.tzinfo is None:
            criada_em = criada_em.replace(tzinfo=timezone.utc)
        return LeituraNotaDTO(
            id=entidade.id,
            url=entidade.url,
            nota=cls.nota(entidade.nota) if entidade.nota else None,
            erro_consulta=entidade.erro_consulta,
            criada_em=criada_em,
        )
