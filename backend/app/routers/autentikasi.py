"""Authentication router — registrasi, masuk, saya."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.dependencies.auth import get_current_user
from app.models.enums import PeranPengguna
from app.models.pengguna import Pengguna
from app.schemas.auth import (
    RegistrasiRequest,
    MasukRequest,
    TokenResponse,
    UserOut,
)

router = APIRouter(prefix="/api/autentikasi", tags=["autentikasi"])


@router.post("/registrasi", response_model=TokenResponse, status_code=201)
def registrasi(body: RegistrasiRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Register a new mahasiswa account.

    Password must be at least 8 characters.
    Role is always hardcoded to 'mahasiswa' (pustakawan are seeded only).
    Returns a JWT on success (auto-login per D-04).
    """
    existing = (
        db.query(Pengguna)
        .filter(Pengguna.email == body.email)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email sudah terdaftar.",
        )

    pengguna = Pengguna(
        nama=body.nama,
        email=body.email,
        kata_sandi=hash_password(body.kata_sandi),
        peran=PeranPengguna.mahasiswa,
    )
    db.add(pengguna)
    try:
        db.commit()
        db.refresh(pengguna)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email sudah terdaftar.",
        )

    token = create_access_token(
        {
            "sub": str(pengguna.id),
            "peran": pengguna.peran.value,
            "nama": pengguna.nama,
        }
    )
    return TokenResponse(access_token=token)


@router.post("/masuk", response_model=TokenResponse)
def masuk(body: MasukRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Authenticate a user and return a JWT.

    Returns 401 for invalid credentials.
    """
    pengguna = (
        db.query(Pengguna)
        .filter(Pengguna.email == body.email)
        .first()
    )
    if not pengguna or not verify_password(body.kata_sandi, pengguna.kata_sandi):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau kata sandi salah.",
        )

    token = create_access_token(
        {
            "sub": str(pengguna.id),
            "peran": pengguna.peran.value,
            "nama": pengguna.nama,
        }
    )
    return TokenResponse(access_token=token)


@router.get("/saya", response_model=UserOut)
def saya(user: Pengguna = Depends(get_current_user)) -> UserOut:
    """Return the currently authenticated user's profile."""
    return UserOut(
        id=str(user.id),
        nama=user.nama,
        email=user.email,
        peran=user.peran.value,
    )
