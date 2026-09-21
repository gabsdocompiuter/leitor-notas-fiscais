from uuid import UUID

from pydantic import BaseModel

from ...dtos.estabelecimento_dto import EstabelecimentoDTO


class EstabelecimentoResponse(BaseModel):
    id: UUID
    cnpj: str
    razao_social: str
    apelido: str | None
    nome_exibicao: str

    @classmethod
    def from_entity(cls, estabelecimento: EstabelecimentoDTO) -> "EstabelecimentoResponse":
        return cls(
            id=estabelecimento.id,
            cnpj=estabelecimento.cnpj,
            razao_social=estabelecimento.razao_social,
            apelido=estabelecimento.apelido,
            nome_exibicao=estabelecimento.nome_exibicao,
        )
