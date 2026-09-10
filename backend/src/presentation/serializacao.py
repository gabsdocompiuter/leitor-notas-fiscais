import json
from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from ..models.nota import Nota


def converter_valor(valor: object) -> str:
    if isinstance(valor, datetime):
        return valor.isoformat()
    if isinstance(valor, (Decimal, UUID)):
        return str(valor)
    if isinstance(valor, Enum):
        return valor.value
    raise TypeError(f"Tipo não suportado no JSON: {type(valor).__name__}")


def serializar(nota: Nota) -> str:
    # Decimais viram strings: o JSON conserva a precisão de valores e quantidades.
    return json.dumps(asdict(nota), ensure_ascii=False, indent=2, default=converter_valor) + "\n"
