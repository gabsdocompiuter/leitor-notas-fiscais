import json

from sqlalchemy import Text
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator


class StringList(TypeDecorator[list[str]]):
    """Serializa listas pequenas de mensagens em JSON."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: list[str] | None, dialect: Dialect) -> str:
        return json.dumps(value or [], ensure_ascii=False)

    def process_result_value(self, value: str | None, dialect: Dialect) -> list[str]:
        return json.loads(value) if value else []
