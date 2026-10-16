from pydantic import BaseModel, Field, field_validator


class EstabelecimentoRequest(BaseModel):
    apelido: str | None = Field(default=None, max_length=100)


class CriarEstabelecimentoRequest(BaseModel):
    apelido: str = Field(min_length=1, max_length=100)

    @field_validator("apelido")
    @classmethod
    def validar_apelido(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("Informe o apelido do estabelecimento.")
        return valor.strip()
