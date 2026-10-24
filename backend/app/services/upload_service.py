"""
TrendPulse File Upload & Storage Service.
"""

from __future__ import annotations

import os
from pathlib import Path
import time
import uuid
from fastapi import HTTPException, UploadFile, status

from backend.app.core.config import settings


def save_upload_file(upload_file: UploadFile) -> tuple[Path, int, str]:
    """
    Validate and save uploaded file to local disk storage.
    Returns: (saved_file_path, file_size_bytes, file_extension)
    """
    if not upload_file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file has no filename.",
        )

    ext = Path(upload_file.filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed formats: {', '.join(settings.ALLOWED_EXTENSIONS)}",
        )

    # Unique storage filename
    unique_name = f"{int(time.time())}_{uuid.uuid4().hex[:8]}{ext}"
    destination = settings.UPLOAD_DIR / unique_name

    # Write file content
    bytes_written = 0
    try:
        with open(destination, "wb") as buffer:
            while chunk := upload_file.file.read(1024 * 1024):  # 1MB chunks
                bytes_written += len(chunk)
                if bytes_written > settings.MAX_UPLOAD_SIZE_BYTES:
                    destination.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES // (1024*1024)}MB.",
                    )
                buffer.write(chunk)
    finally:
        upload_file.file.close()

    return destination, bytes_written, ext
