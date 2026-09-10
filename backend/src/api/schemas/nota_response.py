from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from ...models.nota import Nota
from ...models.situacao_nota import SituacaoNota
from .estabelecimento_response import EstabelecimentoResponse
from .item_response import ItemResponse


class NotaResponse(BaseModel):
    id: UUID
    chave: str
    numero: str
    serie: str
    estabelecimento: EstabelecimentoResponse
    emissao: datetime
    quantidade_itens: int
    valor_total: str
    desconto: str
    valor_a_pagar: str
    itens: list[ItemResponse]
    url_origem: str
    situacao: SituacaoNota

    @classmethod
    def from_entity(cls, nota: Nota) -> "NotaResponse":
        return cls(
            id=nota.id,
            chave=nota.chave,
            numero=nota.numero,
            serie=nota.serie,
            estabelecimento=EstabelecimentoResponse.from_entity(nota.estabelecimento),
            emissao=nota.emissao,
            quantidade_itens=nota.quantidade_itens,
            valor_total=str(nota.valor_total),
            desconto=str(nota.desconto),
            valor_a_pagar=str(nota.valor_a_pagar),
            itens=[ItemResponse.from_entity(item) for item in nota.itens],
            url_origem=nota.url_origem,
            situacao=nota.situacao,
        )
