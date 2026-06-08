"""User read schema — the safe, public-facing projection of `User`.

Never includes `hashed_password`. This is what `TokenResponse.user` and
`GET /auth/me` return.
"""

from pydantic import BaseModel, ConfigDict

from app.models.user import UserRole


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: UserRole
