from pydantic import BaseModel, Field


class CategoriaRequest(BaseModel):
    nome: str = Field(min_length=1, max_length=100, examples=["Alimentação"])
