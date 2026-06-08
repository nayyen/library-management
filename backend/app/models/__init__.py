# Import every model module here so Base.metadata is populated before Alembic
# autogenerate runs (RESEARCH Pitfall 3 — "Empty Alembic autogenerate").
#
# Plan 02 adds:
#   from app.models import user        # noqa: F401
#   from app.models import refresh_token  # noqa: F401
