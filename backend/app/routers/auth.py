"""Auth endpoints — signup, login, refresh, logout, and (Task 3) /me.

Cookie contract (D-05): the refresh token is set as an httpOnly, SameSite=Lax
cookie scoped to `/auth` — never returned in a response BODY, never readable
by JS. The access token is the only thing that appears in `TokenResponse`,
and it lives only in-memory on the frontend.

Per RESEARCH Pitfall 1 — do NOT set an explicit `domain=` on the cookie
(causes `localhost` vs `127.0.0.1` mismatches between Vite/CORS/cookies).
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import (
    EmailAlreadyRegistered,
    InvalidLibrarianCode,
    RefreshTokenInvalid,
    RefreshTokenReused,
)
from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse
from app.schemas.user import UserRead
from app.services import auth_service

router = APIRouter()

REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/auth"

# D-03 exact copy — the librarian-signup reject string from the UI-SPEC
# Copywriting Contract. Centralized here so the router and the schema-level
# validator (schemas/auth.py) stay byte-identical.
INVALID_LIBRARIAN_CODE_MESSAGE = (
    "Invalid librarian code — check with your library administrator, "
    "or sign up as a student."
)

# UI-SPEC Copywriting Contract — duplicate-email signup rejection.
EMAIL_ALREADY_EXISTS_MESSAGE = (
    "An account with this email already exists. Log in instead, or use a different email."
)


def _set_refresh_cookie(response: Response, raw_refresh_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=raw_refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path=REFRESH_COOKIE_PATH,
        # No explicit `domain=` — Pitfall 1 (localhost vs 127.0.0.1 mismatch).
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    payload: SignupRequest,
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    try:
        access_token, raw_refresh, user = await auth_service.signup(
            db,
            email=payload.email,
            password=payload.password,
            role=payload.role,
            librarian_code=payload.librarian_code,
            user_agent=request.headers.get("user-agent"),
        )
    except InvalidLibrarianCode as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=INVALID_LIBRARIAN_CODE_MESSAGE
        ) from exc
    except EmailAlreadyRegistered as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=EMAIL_ALREADY_EXISTS_MESSAGE
        ) from exc

    _set_refresh_cookie(response, raw_refresh)
    return TokenResponse(access_token=access_token, user=UserRead.model_validate(user))


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    # `auth_service.authenticate` raises the single generic 401
    # (`invalid_credentials_exception`) for both bad-email and bad-password —
    # no enumeration. Let it propagate as-is.
    access_token, raw_refresh, user = await auth_service.login(
        db,
        email=payload.email,
        password=payload.password,
        user_agent=request.headers.get("user-agent"),
    )
    _set_refresh_cookie(response, raw_refresh)
    return TokenResponse(access_token=access_token, user=UserRead.model_validate(user))


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    raw_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if raw_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    try:
        access_token, new_raw_refresh, user = await auth_service.rotate_refresh_token(
            db, raw_token, user_agent=request.headers.get("user-agent")
        )
    except RefreshTokenReused as exc:
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token reuse detected — all sessions revoked",
        ) from exc
    except RefreshTokenInvalid as exc:
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        ) from exc

    _set_refresh_cookie(response, new_raw_refresh)
    return TokenResponse(access_token=access_token, user=UserRead.model_validate(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> Response:
    raw_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if raw_token is not None:
        # D-06: revoke ONLY this session's refresh token — other devices stay logged in.
        await auth_service.revoke_refresh_token(db, raw_token)
    _clear_refresh_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)
