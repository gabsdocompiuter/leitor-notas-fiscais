from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from ...models.leitura_nota import LeituraNota
from .nota_response import NotaResponse


class LeituraResponse(BaseModel):
    id: UUID
    url: str
    nota: NotaResponse | None
    erro_consulta: str | None
    criada_em: datetime

    @classmethod
    def from_entity(cls, leitura: LeituraNota) -> "LeituraResponse":
        return cls(
            id=leitura.id,
            url=leitura.url,
            nota=NotaResponse.from_entity(leitura.nota) if leitura.nota else None,
            erro_consulta=leitura.erro_consulta,
            criada_em=leitura.criada_em,
        )
