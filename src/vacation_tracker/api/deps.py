"""FastAPI dependencies: database session and Basic Auth."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session

from vacation_tracker.core.constants import UserRole
from vacation_tracker.db.models import Employee
from vacation_tracker.db.session import get_db
from vacation_tracker.services.auth_service import AuthService

security = HTTPBasic()

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
    db: DbSession,
) -> Employee:
    """Authenticate via HTTP Basic (username = email)."""
    user = AuthService(db).authenticate(credentials.username, credentials.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user


CurrentUser = Annotated[Employee, Depends(get_current_user)]


def require_admin(current_user: CurrentUser) -> Employee:
    """Require the authenticated user to have the admin role."""
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


AdminUser = Annotated[Employee, Depends(require_admin)]
