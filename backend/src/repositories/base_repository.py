from typing import Generic, TypeVar

from sqlalchemy.orm import Session

Entidade = TypeVar("Entidade")


class BaseRepository(Generic[Entidade]):
    """Base de repositories; transações pertencem à camada de serviço."""

    def __init__(self, session: Session):
        self.session = session
