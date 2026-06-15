import json
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File
from fastapi.responses import Response

from src.api.schemas import JobResponse, UploadResponse
from src.jobs.store import job_store
from src.processor.pipeline import process_csv

router = APIRouter(prefix="/api", tags=["jobs"])


@router.post("/upload", response_model=UploadResponse, status_code=202)
async def upload_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
) -> UploadResponse:
    if not (file.filename or "").endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10 MB hard limit
        raise HTTPException(status_code=413, detail="File too large (max 10 MB)")

    job_id = str(uuid.uuid4())
    await job_store.create(job_id)
    background_tasks.add_task(process_csv, job_id, content)

    return UploadResponse(job_id=job_id, status="pending")


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str) -> JobResponse:
    job = await job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse(job_id=job_id, **job)


@router.get("/jobs/{job_id}/output.json")
async def download_output(job_id: str) -> Response:
    job = await job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "done":
        raise HTTPException(status_code=409, detail="Job is not done yet")

    payload = json.dumps(job["result"], ensure_ascii=False, indent=2)
    return Response(
        content=payload,
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="output.json"'},
    )


@router.get("/jobs/{job_id}/report.md")
async def download_report(job_id: str) -> Response:
    job = await job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "done":
        raise HTTPException(status_code=409, detail="Job is not done yet")

    return Response(
        content=job["report"],
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="report.md"'},
    )
