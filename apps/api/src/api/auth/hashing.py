from functools import lru_cache

from passlib.context import CryptContext

from api.settings import settings


@lru_cache(maxsize=1)
def _ctx() -> CryptContext:
    return CryptContext(
        schemes=["bcrypt"],
        deprecated="auto",
        bcrypt__rounds=settings.bcrypt_rounds,
    )


def hash_password(plain: str) -> str:
    return _ctx().hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _ctx().verify(plain, hashed)


def verify_and_update(plain: str, hashed: str) -> tuple[bool, str | None]:
    """Verify password and return a new hash if the stored one uses outdated settings."""
    ok, new_hash = _ctx().verify_and_update(plain, hashed)
    return ok, new_hash
