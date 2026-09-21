from sqlalchemy.orm import DeclarativeBase


class BaseEntity(DeclarativeBase):
    """Base declarativa compartilhada por todas as entidades persistentes."""
