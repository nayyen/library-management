"""Auth request/response schemas.

`SignupRequest` enforces D-01 at the validation layer: choosing
`role=librarian` REQUIRES a `librarian_code` to be present in the payload —
the model_validator below rejects a missing code before the service layer
ever runs (the service layer then re-checks the code's *value* against
`settings.LIBRARIAN_SIGNUP_CODE`, per D-03 "no silent fallback").
"""

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.models.user import UserRole
from app.schemas.user import UserRead


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole
    librarian_code: str | None = None

    @model_validator(mode="after")
    def _require_code_for_librarian(self) -> "SignupRequest":
        if self.role == UserRole.LIBRARIAN and not self.librarian_code:
            raise ValueError(
                "Invalid librarian code — check with your library administrator, "
                "or sign up as a student."
            )
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)
