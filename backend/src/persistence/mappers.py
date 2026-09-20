from datetime import timezone

from ..models.apresentacao_produto import ApresentacaoProduto
from ..models.categoria import Categoria
from ..models.estabelecimento import Estabelecimento
from ..models.item import Item
from ..models.leitura_nota import LeituraNota
from ..models.marca import Marca
from ..models.nota import Nota
from ..models.produto import Produto
from ..models.variacao_produto import VariacaoProduto
from .entities import (
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


def categoria_modelo(entidade: CategoriaEntity) -> Categoria:
    return Categoria(id=entidade.id, nome=entidade.nome)


def marca_modelo(entidade: MarcaEntity) -> Marca:
    return Marca(id=entidade.id, nome=entidade.nome)


def estabelecimento_modelo(entidade: EstabelecimentoEntity) -> Estabelecimento:
    return Estabelecimento(
        id=entidade.id,
        cnpj=entidade.cnpj,
        razao_social=entidade.razao_social,
        apelido=entidade.apelido,
    )


def produto_modelo(entidade: ProdutoEntity) -> Produto:
    return Produto(
        id=entidade.id,
        nome=entidade.nome,
        categoria=categoria_modelo(entidade.categoria),
        nao_solicitar_marca=entidade.nao_solicitar_marca,
        tratar_apenas_como_unidades=entidade.tratar_apenas_como_unidades,
        contem_variacoes=entidade.contem_variacoes,
        unidade_medida=entidade.unidade_medida,
    )


def variacao_modelo(entidade: VariacaoProdutoEntity) -> VariacaoProduto:
    return VariacaoProduto(
        id=entidade.id,
        produto=produto_modelo(entidade.produto),
        quantidade=entidade.quantidade,
        unidade_medida=entidade.unidade_medida,
        descricao=entidade.descricao,
    )


def apresentacao_modelo(entidade: ApresentacaoProdutoEntity) -> ApresentacaoProduto:
    return ApresentacaoProduto(
        id=entidade.id,
        produto=produto_modelo(entidade.produto),
        marca=marca_modelo(entidade.marca) if entidade.marca else None,
    )


def item_modelo(entidade: ItemEntity) -> Item:
    return Item(
        id=entidade.id,
        numero=entidade.numero,
        codigo=entidade.codigo,
        descricao_original=entidade.descricao_original,
        quantidade=entidade.quantidade,
        unidade_original=entidade.unidade_original,
        valor_unitario=entidade.valor_unitario,
        valor_total=entidade.valor_total,
        alertas=entidade.alertas,
        apresentacao=(apresentacao_modelo(entidade.apresentacao) if entidade.apresentacao else None),
        variacao=variacao_modelo(entidade.variacao) if entidade.variacao else None,
        quantidade_confirmada=entidade.quantidade_confirmada,
        revisado=entidade.revisado,
    )


def nota_modelo(entidade: NotaEntity) -> Nota:
    return Nota(
        id=entidade.id,
        chave=entidade.chave,
        numero=entidade.numero,
        serie=entidade.serie,
        estabelecimento=estabelecimento_modelo(entidade.estabelecimento),
        emissao=entidade.emissao,
        quantidade_itens=entidade.quantidade_itens,
        valor_total=entidade.valor_total,
        desconto=entidade.desconto,
        valor_a_pagar=entidade.valor_a_pagar,
        itens=[item_modelo(item) for item in entidade.itens],
        url_origem=entidade.url_origem,
        situacao=entidade.situacao,
        importada_em=entidade.importada_em,
    )


def leitura_modelo(entidade: LeituraNotaEntity) -> LeituraNota:
    criada_em = entidade.criada_em
    if criada_em.tzinfo is None:
        criada_em = criada_em.replace(tzinfo=timezone.utc)
    return LeituraNota(
        id=entidade.id,
        url=entidade.url,
        nota=nota_modelo(entidade.nota) if entidade.nota else None,
        erro_consulta=entidade.erro_consulta,
        criada_em=criada_em,
    )
