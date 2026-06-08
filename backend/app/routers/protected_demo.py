"""AUTH-04 proof surface — a real librarian-only protected route.

This is the concrete demonstration that `require_role` enforces
authorization SERVER-SIDE (a forged/tampered token claiming `role: librarian`
is re-checked against the DB-loaded user — see 01-VALIDATION.md "Manual-Only
Verifications": forge a student token, call this route, confirm 403
regardless of what the token claims). It also doubles as the data source the
frontend dashboard's role-differentiated stub renders against.
"""

from fastapi import APIRouter, Depends

from app.dependencies.auth import require_role
from app.models.user import User, UserRole

router = APIRouter()


@router.get("/librarian-only", dependencies=[Depends(require_role(UserRole.LIBRARIAN))])
async def librarian_only_demo() -> dict[str, str]:
    return {"message": "You have librarian access."}
