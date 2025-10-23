from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, Iterable, Literal, cast

from celery import chain

from app.core.settings import get_settings
from app.models import (
    DiffEntity,
    DiffPolygon,
    DiffSummary,
    JobDiffPayload,
    StoredFile,
)
from app.services import JobService, ParsedEntity, match_entities, parse_dxf
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


def _build_stored_file(path: Path, content_type: str | None = None, *, kind: str | None = None) -> StoredFile:
    data = path.read_bytes()
    return StoredFile(
        name=path.name,
        path=str(path.resolve()),
        size=len(data),
        checksum=sha256(data).hexdigest(),
        content_type=content_type,
        kind=kind,
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

    original_file = job.original_files[0]
    revised_file = job.revised_files[0]

    original_entities = parse_dxf(Path(original_file.path))
    revised_entities = parse_dxf(Path(revised_file.path))

    converted_path = convert_dir / "entities.json"
    serialized_original = [asdict(entity) for entity in original_entities]
    serialized_revised = [asdict(entity) for entity in revised_entities]
    converted_path.write_text(
        json.dumps(
            {
                "original": serialized_original,
                "revised": serialized_revised,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    done_logs = job.logs + [
        {"step": "convert", "status": "done", "timestamp": _timestamp(), "output": str(converted_path)},
    ]
    job = service.update_metadata(
        job_id,
        progress=0.35,
        logs=done_logs,
    )

    return {
        "job_id": job_id,
        "original_entities": serialized_original,
        "revised_entities": serialized_revised,
    }


@celery_app.task(name="jobs.extract")
def extract_job_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    job_id = payload["job_id"]
    original_entities = payload.get("original_entities", [])
    revised_entities = payload.get("revised_entities", [])

    service = _service()
    job = service.load_job(job_id)

    start_logs = job.logs + [
        {"step": "extract", "status": "running", "timestamp": _timestamp()},
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
        json.dumps(
            {
                "original": original_entities,
                "revised": revised_entities,
            },
            ensure_ascii=False,
            indent=2,
        ),
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


def _deserialize_entities(entities: Iterable[dict[str, Any]]) -> list[ParsedEntity]:
    return [
        ParsedEntity(
            entity_id=item["entity_id"],
            entity_type=item["entity_type"],
            vertices=[tuple(vertex) for vertex in item.get("vertices", [])],
        )
        for item in entities
    ]


@celery_app.task(name="jobs.match")
def match_job_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise TypeError(f"match_job_task expected dict payload, got {type(payload)}")
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
    original_entities = _deserialize_entities(payload.get("original_entities", []))
    revised_entities = _deserialize_entities(payload.get("revised_entities", []))
    matches = match_entities(original_entities, revised_entities)

    diff_entities: list[DiffEntity] = []

    for change_type, entities in matches.items():
        for entity in entities:
            diff_entities.append(
                DiffEntity(
                    entity_id=entity.entity_id,
                    entity_type=entity.entity_type,
                    change_type=cast(Literal["added", "removed", "modified"], change_type),
                    label=f"{entity.entity_type}-{entity.entity_id}",
                    polygon=DiffPolygon(points=[tuple(point) for point in entity.vertices]),
                )
            )

    diff_payload = JobDiffPayload(
        job_id=job_id,
        summary=DiffSummary(
            added=len(matches["added"]),
            removed=len(matches["removed"]),
            modified=len(matches["modified"]),
        ),
        entities=diff_entities,
    )
    report_path.write_text(diff_payload.model_dump_json(indent=2, ensure_ascii=False), encoding="utf-8")
    report_file = _build_stored_file(report_path, content_type="application/json", kind="diff")

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
        payload = convert_job_task.run(job_id)
        payload = extract_job_task.run(payload)
        payload = match_job_task.run(payload)
        return payload

    workflow = chain(
        convert_job_task.s(job_id),
        extract_job_task.s(),
        match_job_task.s(),
    )
    result = workflow.apply_async()
    return {"job_id": job_id, "status": "queued", "result_id": result.id}
