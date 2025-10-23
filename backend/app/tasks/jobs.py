from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict

from celery import chain

from app.core.settings import get_settings
from app.models import StoredFile
from app.services import JobService
from app.worker import celery_app


def _service() -> JobService:
    settings = get_settings()
    return JobService(Path(settings.storage_dir))


def _storage_root() -> Path:
    settings = get_settings()
    return Path(settings.storage_dir)


def _job_dir(job_id: str) -> Path:
    return _storage_root() / "jobs" / job_id


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_stored_file(path: Path, content_type: str | None = None) -> StoredFile:
    data = path.read_bytes()
    return StoredFile(
        name=path.name,
        path=str(path.resolve()),
        size=len(data),
        checksum=sha256(data).hexdigest(),
        content_type=content_type,
    )


@celery_app.task(name="jobs.convert")
def convert_job_task(job_id: str) -> Dict[str, Any]:
    service = _service()
    job = service.load_job(job_id)

    start_logs = job.logs + [
        {"step": "convert", "status": "running", "timestamp": _timestamp()},
    ]
    job = service.update_metadata(
        job_id,
        status="processing",
        progress=0.2,
        logs=start_logs,
    )

    convert_dir = _job_dir(job_id) / "converted"
    convert_dir.mkdir(parents=True, exist_ok=True)
    converted_path = convert_dir / "combined.dxf"
    converted_path.write_text(f"DXF placeholder generated for job {job_id}\n", encoding="utf-8")

    done_logs = job.logs + [
        {"step": "convert", "status": "done", "timestamp": _timestamp(), "output": str(converted_path)},
    ]
    job = service.update_metadata(
        job_id,
        progress=0.35,
        logs=done_logs,
    )

    return {"job_id": job_id, "converted_paths": [str(converted_path.resolve())]}


@celery_app.task(name="jobs.extract")
def extract_job_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    job_id = payload["job_id"]
    converted_paths = payload.get("converted_paths", [])

    service = _service()
    job = service.load_job(job_id)

    start_logs = job.logs + [
        {"step": "extract", "status": "running", "timestamp": _timestamp(), "sources": converted_paths},
    ]
    job = service.update_metadata(
        job_id,
        progress=0.45,
        logs=start_logs,
    )

    extract_dir = _job_dir(job_id) / "extracted"
    extract_dir.mkdir(parents=True, exist_ok=True)
    extracted_path = extract_dir / "entities.json"
    extracted_path.write_text(
        "{\n  \"entities\": [],\n  \"source_count\": %d\n}\n" % len(converted_paths),
        encoding="utf-8",
    )

    done_logs = job.logs + [
        {"step": "extract", "status": "done", "timestamp": _timestamp(), "output": str(extracted_path)},
    ]
    job = service.update_metadata(
        job_id,
        progress=0.65,
        logs=done_logs,
    )

    payload.update({"extracted_path": str(extracted_path.resolve())})
    return payload


@celery_app.task(name="jobs.match")
def match_job_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    job_id = payload["job_id"]
    extracted_path = payload.get("extracted_path")

    service = _service()
    job = service.load_job(job_id)

    start_logs = job.logs + [
        {"step": "match", "status": "running", "timestamp": _timestamp(), "source": extracted_path},
    ]
    job = service.update_metadata(
        job_id,
        progress=0.8,
        logs=start_logs,
    )

    report_dir = _job_dir(job_id) / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "diff.json"
    report_path.write_text(
        "{\n  \"summary\": \"placeholder diff\",\n  \"job_id\": \"%s\"\n}\n" % job_id,
        encoding="utf-8",
    )
    report_file = _build_stored_file(report_path, content_type="application/json")

    done_logs = job.logs + [
        {"step": "match", "status": "done", "timestamp": _timestamp(), "report": report_file.path},
    ]
    job = service.update_metadata(
        job_id,
        status="completed",
        progress=1.0,
        logs=done_logs,
        reports=job.reports + [report_file],
    )

    payload.update({"status": job.status, "report_path": report_file.path})
    return payload


@celery_app.task(name="jobs.process_job")
def process_job_task(job_id: str) -> Dict[str, Any]:
    if celery_app.conf.task_always_eager:
        payload = convert_job_task.apply(args=(job_id,), throw=True).result
        payload = extract_job_task.apply(args=(payload,), throw=True).result
        payload = match_job_task.apply(args=(payload,), throw=True).result
        return payload

    workflow = chain(
        convert_job_task.s(job_id),
        extract_job_task.s(),
        match_job_task.s(),
    )
    result = workflow.apply_async()
    return {"job_id": job_id, "status": "queued", "result_id": result.id}
