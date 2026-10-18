from uuid import UUID
from pydantic import BaseModel, ConfigDict


class SaborProdutoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    produto_id: UUID
    nome: str
