"""Employee self-service vacation endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/me/vacations", tags=["employee-vacations"])
