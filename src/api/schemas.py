from typing import Any, Optional

from pydantic import BaseModel

from src.jobs.store import JobStatus


class UploadResponse(BaseModel):
    job_id: str
    status: JobStatus


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    total: Optional[int] = None
    processed: int = 0
    failed: int = 0
    error: Optional[str] = None
    result: Optional[list[Any]] = None
    report: Optional[str] = None
