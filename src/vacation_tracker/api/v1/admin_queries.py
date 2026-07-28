"""Admin query endpoints for employees, allowances, and usages."""

from fastapi import APIRouter

router = APIRouter(prefix="/admin", tags=["admin-queries"])
