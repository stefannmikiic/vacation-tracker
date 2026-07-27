"""Password hashing helpers."""

import bcrypt


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return bcrypt.hashpw(
        plain_password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")
