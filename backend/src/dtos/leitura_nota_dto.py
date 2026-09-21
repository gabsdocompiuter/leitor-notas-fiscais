from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from .nota_dto import NotaDTO


@dataclass
class LeituraNotaDTO:
    """Captura do QR Code, que pode existir antes de obter os dados da nota."""

    id: UUID = field(default_factory=uuid4, kw_only=True)
    url: str
    nota: NotaDTO | None = None
    erro_consulta: str | None = None
    criada_em: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
