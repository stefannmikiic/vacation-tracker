"""Password hashing helpers."""

import bcrypt


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return bcrypt.hashpw(
        plain_password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Return True if plaintext matches the stored bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        password_hash.encode("utf-8"),
    )
