from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app.core.settings import get_settings
from app.models import Envelope, JobCreatedPayload, JobDiffPayload, JobListPayload, JobStatusPayload, JobSummary
from app.services import JobService
from app.tasks import process_job_task


router = APIRouter()

SUPPORTED_CONTENT_TYPES = {
    "application/dwg",
    "application/octet-stream",
    "application/acad",
    "image/vnd.dwg",
}


def get_job_service() -> JobService:
    settings = get_settings()
    return JobService(Path(settings.storage_dir))


def _validate_upload(upload: UploadFile, field_name: str) -> None:
    if upload.content_type is None:
        return

    if upload.content_type.lower() not in SUPPORTED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"{field_name} has an unsupported content type")


@router.get(
    "",
    response_model=Envelope[JobListPayload],
    summary="List comparison jobs",
)
async def list_jobs(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip"),
    job_service: JobService = Depends(get_job_service),
) -> Envelope[JobListPayload]:
    """Return paginated comparison jobs sorted by last update time."""

    total, jobs = job_service.list_jobs(limit=limit, offset=offset)
    summaries = [
        JobSummary(
            job_id=job.job_id,
            status=job.status,
            progress=job.progress,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )
        for job in jobs
    ]
    payload = JobListPayload(total=total, limit=limit, offset=offset, jobs=summaries)
    return Envelope(data=payload)


@router.post(
    "",
    response_model=Envelope[JobCreatedPayload],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create a comparison job",
)
async def create_job(
    original_dwg: UploadFile = File(...),
    revised_dwg: UploadFile = File(...),
    job_service: JobService = Depends(get_job_service),
) -> Envelope[JobCreatedPayload]:
    """Accept two DWG files and enqueue a comparison job."""

    _validate_upload(original_dwg, "original_dwg")
    _validate_upload(revised_dwg, "revised_dwg")

    metadata = await job_service.create_job(original_dwg, revised_dwg)
    enqueue_logs = metadata.logs + [
        {
            "step": "enqueue",
            "status": "queued",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    ]
    metadata = job_service.update_metadata(metadata.job_id, logs=enqueue_logs)

    try:
        process_job_task.delay(metadata.job_id)
    except Exception as exc:  # pragma: no cover - Celery eager mode raises inline
        raise HTTPException(status_code=500, detail="Failed to enqueue job") from exc

    payload = JobCreatedPayload(job_id=metadata.job_id, status=metadata.status)
    return Envelope(data=payload)


@router.get(
    "/{job_id}",
    response_model=Envelope[JobStatusPayload],
    summary="Retrieve job status",
)
async def get_job_status(
    job_id: str,
    job_service: JobService = Depends(get_job_service),
) -> Envelope[JobStatusPayload]:
    """Return the current status for a comparison job."""

    try:
        status_payload = job_service.get_job_status(job_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc

    return Envelope(data=status_payload)


@router.get(
    "/{job_id}/diff",
    response_model=Envelope[JobDiffPayload],
    summary="Retrieve job diff payload",
)
async def get_job_diff(
    job_id: str,
    job_service: JobService = Depends(get_job_service),
) -> Envelope[JobDiffPayload]:
    """Return diff payload for a job."""

    try:
        diff_payload = job_service.get_job_diff(job_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Diff not found") from exc

    return Envelope(data=diff_payload)
