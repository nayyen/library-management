"""Re-export of the `get_db` dependency for use in routers.

Kept as a thin re-export so route modules import dependencies from a single
`app.dependencies.*` namespace (RESEARCH "Recommended Project Structure"),
while `app.database` remains the source of truth for engine/session wiring.
"""

from app.database import get_db

__all__ = ["get_db"]
