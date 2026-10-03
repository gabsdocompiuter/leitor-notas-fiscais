from dataclasses import dataclass
from uuid import UUID


@dataclass
class TagDTO:
    id: UUID
    nome: str
