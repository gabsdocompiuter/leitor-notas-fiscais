from dataclasses import dataclass
from uuid import UUID


@dataclass
class SaborProdutoDTO:
    id: UUID
    produto_id: UUID
    nome: str
