"""Pydantic schemas for authentication."""

from pydantic import BaseModel, EmailStr, Field


class RegistrasiRequest(BaseModel):
    nama: str = Field(..., min_length=1, max_length=150)
    email: EmailStr
    kata_sandi: str = Field(..., min_length=8)


class MasukRequest(BaseModel):
    email: EmailStr
    kata_sandi: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    nama: str
    email: str
    peran: str

    model_config = {"from_attributes": True}
