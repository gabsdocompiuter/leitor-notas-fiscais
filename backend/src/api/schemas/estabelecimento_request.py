from pydantic import BaseModel, Field


class EstabelecimentoRequest(BaseModel):
    apelido: str | None = Field(default=None, max_length=150)
