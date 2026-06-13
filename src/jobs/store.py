import asyncio
from enum import Enum
from typing import Any


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def create(self, job_id: str) -> None:
        async with self._lock:
            self._jobs[job_id] = {
                "status": JobStatus.PENDING,
                "total": None,
                "processed": 0,
                "result": None,
                "report": None,
                "error": None,
                "failed": 0,
            }

    async def update(self, job_id: str, **kwargs: Any) -> None:
        async with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].update(kwargs)

    async def get(self, job_id: str) -> dict[str, Any] | None:
        return self._jobs.get(job_id)


job_store = JobStore()
