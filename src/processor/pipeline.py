import asyncio
import logging

import httpx

from src.jobs.store import JobStatus, job_store
from src.processor.csv_reader import read_csv
from src.processor.llm_client import analyze_request
from src.processor.reporter import build_output, build_report

logger = logging.getLogger(__name__)

# One request in-flight at a time — matches llama.cpp --parallel 1
_SEM = asyncio.Semaphore(1)


async def process_csv(job_id: str, csv_content: bytes) -> None:
    await job_store.update(job_id, status=JobStatus.PROCESSING)
    logger.info("Job %s started", job_id)

    try:
        rows = read_csv(csv_content)
    except ValueError as exc:
        await job_store.update(job_id, status=JobStatus.FAILED, error=str(exc))
        logger.error("Job %s failed at CSV parsing: %s", job_id, exc)
        return

    total = len(rows)
    await job_store.update(job_id, total=total, processed=0)

    results: list[dict] = []

    async with httpx.AsyncClient() as client:
        for i, row in enumerate(rows, 1):
            async with _SEM:
                try:
                    analysis = await analyze_request(row, client)
                    results.append({**row, "analysis": analysis.model_dump()})
                    logger.info("Job %s: row %d/%d OK (%s)", job_id, i, total, row.get("id"))
                except Exception as exc:
                    results.append({**row, "error": str(exc), "analysis": None})
                    logger.warning("Job %s: row %d/%d FAILED (%s): %s", job_id, i, total, row.get("id"), exc)

            await job_store.update(job_id, processed=i)

    output = build_output(results)
    report = build_report(results)

    failed_count = sum(1 for r in results if r.get("error"))
    await job_store.update(
        job_id,
        status=JobStatus.DONE,
        result=output,
        report=report,
        failed=failed_count,
    )
    logger.info("Job %s done — %d/%d rows OK", job_id, total - failed_count, total)
