"""Aggregate all version-1 API routers."""

from fastapi import APIRouter

from vacation_tracker.api.v1 import admin_imports, admin_queries, employee_vacations

api_router = APIRouter()
api_router.include_router(admin_imports.router)
api_router.include_router(admin_queries.router)
api_router.include_router(employee_vacations.router)
