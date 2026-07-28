"""Admin CSV/Excel import endpoints."""

from collections.abc import Callable
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from vacation_tracker.api.deps import AdminUser, DbSession
from vacation_tracker.core.constants import (
    MAX_IMPORT_FILE_SIZE_BYTES,
    SUPPORTED_IMPORT_EXTENSIONS,
)
from vacation_tracker.core.exceptions import ImportStructureError
from vacation_tracker.schemas.imports import ImportSummaryResponse
from vacation_tracker.services.import_service import ImportService, ImportSummary

router = APIRouter(prefix="/admin/imports", tags=["admin-imports"])

ImportFn = Callable[[bytes, str], ImportSummary]
UploadImportFile = Annotated[UploadFile, File()]


def _validate_upload(file: UploadFile, content: bytes) -> str:
    """Return a safe filename after minimal upload checks."""
    filename = file.filename or ""
    if not filename.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_IMPORT_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_IMPORT_EXTENSIONS))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported file extension {extension!r}; "
                f"expected one of: {supported}"
            ),
        )

    if len(content) > MAX_IMPORT_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(f"File exceeds maximum size of {MAX_IMPORT_FILE_SIZE_BYTES} bytes"),
        )

    return filename


async def _run_import(
    file: UploadFile,
    import_fn: ImportFn,
) -> ImportSummaryResponse:
    content = await file.read()
    filename = _validate_upload(file, content)
    try:
        summary = import_fn(content, filename)
    except ImportStructureError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        ) from exc
    return ImportSummaryResponse.model_validate(summary)


@router.post("/employees", response_model=ImportSummaryResponse)
async def import_employees(
    db: DbSession,
    _admin: AdminUser,
    file: UploadImportFile,
) -> ImportSummaryResponse:
    return await _run_import(file, ImportService(db).import_employees)


@router.post("/allowances", response_model=ImportSummaryResponse)
async def import_allowances(
    db: DbSession,
    _admin: AdminUser,
    file: UploadImportFile,
) -> ImportSummaryResponse:
    return await _run_import(file, ImportService(db).import_allowances)


@router.post("/usages", response_model=ImportSummaryResponse)
async def import_usages(
    db: DbSession,
    _admin: AdminUser,
    file: UploadImportFile,
) -> ImportSummaryResponse:
    return await _run_import(file, ImportService(db).import_usages)
