from pydantic import BaseModel, Field


class MarcaRequest(BaseModel):
    nome: str = Field(min_length=1, max_length=100, examples=["Tirol"])
