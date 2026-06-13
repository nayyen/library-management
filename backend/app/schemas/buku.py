"""Pydantic schemas for book catalog."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class BukuCreate(BaseModel):
    judul: str = Field(..., min_length=1, max_length=255)
    penulis: str = Field(..., min_length=1, max_length=255)
    isbn: str = Field(..., min_length=1, max_length=20)
    kategori: str = Field(..., min_length=1, max_length=100)
    tahun_terbit: int = Field(..., ge=1900)

    @field_validator("isbn")
    @classmethod
    def validate_isbn(cls, v: str) -> str:
        digits = v.replace("-", "")
        if not digits.isdigit():
            raise ValueError("ISBN harus berupa angka (boleh mengandung tanda hubung).")
        if len(digits) not in (10, 13):
            raise ValueError("ISBN harus berupa 10 atau 13 digit angka (boleh mengandung tanda hubung).")
        return v

    @field_validator("tahun_terbit")
    @classmethod
    def validate_tahun(cls, v: int) -> int:
        current_year = datetime.now().year
        if v < 1900 or v > current_year:
            raise ValueError(f"Tahun terbit harus antara 1900 dan {current_year}.")
        return v


class BukuUpdate(BaseModel):
    judul: str | None = Field(default=None, min_length=1, max_length=255)
    penulis: str | None = Field(default=None, min_length=1, max_length=255)
    isbn: str | None = Field(default=None, min_length=1, max_length=20)
    kategori: str | None = Field(default=None, min_length=1, max_length=100)
    tahun_terbit: int | None = Field(default=None, ge=1900)

    @field_validator("isbn")
    @classmethod
    def validate_isbn(cls, v: str | None) -> str | None:
        if v is None:
            return v
        digits = v.replace("-", "")
        if not digits.isdigit():
            raise ValueError("ISBN harus berupa angka (boleh mengandung tanda hubung).")
        if len(digits) not in (10, 13):
            raise ValueError("ISBN harus berupa 10 atau 13 digit angka (boleh mengandung tanda hubung).")
        return v

    @field_validator("tahun_terbit")
    @classmethod
    def validate_tahun(cls, v: int | None) -> int | None:
        if v is None:
            return v
        current_year = datetime.now().year
        if v < 1900 or v > current_year:
            raise ValueError(f"Tahun terbit harus antara 1900 dan {current_year}.")
        return v


class SalinanBukuCreate(BaseModel):
    lokasi_rak: str = Field(..., min_length=1, max_length=50)
    kondisi: str = "bagus"
    status_ketersediaan: str = "tersedia"


class SalinanBukuOut(BaseModel):
    id: str
    lokasi_rak: str
    kondisi: str
    status_ketersediaan: str

    model_config = {"from_attributes": True}


class BukuOut(BaseModel):
    id: str
    judul: str
    penulis: str
    isbn: str
    kategori: str
    tahun_terbit: int

    model_config = {"from_attributes": True}


class BukuListItem(BukuOut):
    tersedia: bool


class BukuListOut(BaseModel):
    items: list[BukuListItem]
    total: int


class BukuDetailOut(BukuOut):
    tersedia: bool
    salinan: list[SalinanBukuOut]
