from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://user:password@db:5432/biblio"
    jwt_secret: str = "changeme_use_openssl_rand_hex_32"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
