from uuid import UUID

from pydantic import BaseModel

from ...models.estabelecimento import Estabelecimento


class EstabelecimentoResponse(BaseModel):
    id: UUID
    cnpj: str
    razao_social: str
    apelido: str | None
    nome_exibicao: str

    @classmethod
    def from_entity(cls, estabelecimento: Estabelecimento) -> "EstabelecimentoResponse":
        return cls(
            id=estabelecimento.id,
            cnpj=estabelecimento.cnpj,
            razao_social=estabelecimento.razao_social,
            apelido=estabelecimento.apelido,
            nome_exibicao=estabelecimento.nome_exibicao,
        )
