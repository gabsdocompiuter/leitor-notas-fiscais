from decimal import Decimal

from sqlalchemy import Text
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator


class DecimalText(TypeDecorator[Decimal]):
    """Mantém decimais como texto no SQLite para não perder precisão."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Decimal | None, dialect: Dialect) -> str | None:
        return str(value) if value is not None else None

    def process_result_value(self, value: str | None, dialect: Dialect) -> Decimal | None:
        return Decimal(value) if value is not None else None
