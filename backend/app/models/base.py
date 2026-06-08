"""Declarative base for all ORM models.

`Base.metadata` is what Alembic's `env.py` references as `target_metadata` —
it is only populated once every model module has been imported (see Pitfall 3
in 01-RESEARCH.md: "Empty Alembic autogenerate / forgot to import models").
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
