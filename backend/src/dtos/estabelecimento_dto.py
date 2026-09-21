from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class EstabelecimentoDTO:
    id: UUID = field(default_factory=uuid4, kw_only=True)
    cnpj: str
    razao_social: str
    apelido: str | None = None

    @property
    def nome_exibicao(self) -> str:
        return (self.apelido or "").strip() or self.razao_social
