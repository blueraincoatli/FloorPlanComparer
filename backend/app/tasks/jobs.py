from __future__ import annotations

import json
import subprocess
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
from app.services import JobService, ParsedEntity, match_entities, normalize_entities_by_grid, parse_dxf
from app.worker import celery_app


def _service() -> JobService:
    settings = get_settings()
    return JobService(Path(settings.storage_dir))


def _storage_root() -> Path:
    settings = get_settings()
    return Path(settings.storage_dir)


def _converter_path() -> Path | None:
    settings = get_settings()
    value = settings.converter_path
    if not value:
        return None
    candidate = Path(value)
    return candidate if candidate.exists() else None


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
    """Converts DWG files to DXF using an external converter."""
    service = _service()
    job = service.load_job(job_id)

    start_logs = job.logs + [{"step": "convert", "status": "running", "timestamp": _timestamp()}]
    job = service.update_metadata(job_id, status="processing", progress=0.1, logs=start_logs)

    converter_executable = _converter_path()
    using_stub = converter_executable is None

    converted_files: list[StoredFile] = []
    all_entities = {}
    files_to_convert = [("original", job.original_files[0]), ("revised", job.revised_files[0])]

    for kind, file_to_convert in files_to_convert:
        input_path = Path(file_to_convert.path)
        output_dir = _job_dir(job_id) / "converted" / kind
        output_dir.mkdir(parents=True, exist_ok=True)

        output_dxf_path = output_dir / f"{input_path.stem}.dxf"

        try:
            if using_stub:
                _stub_convert(input_path, output_dxf_path)
                result_stdout = ""
                result_stderr = ""
            else:
                cmd = [
                    str(converter_executable),
                    str(input_path.parent),
                    str(output_dir),
                    "ACAD2018",
                    "DXF",
                    "0",
                    "1",
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True, shell=False)
                result_stdout = result.stdout
                result_stderr = result.stderr

            if not output_dxf_path.exists():
                raise FileNotFoundError(
                    f"Converter failed to produce output file: {output_dxf_path}\n"
                    f"stdout: {result_stdout}\nstderr: {result_stderr}"
                )

            stored_dxf = _build_stored_file(output_dxf_path, content_type="application/vnd.dxf", kind=f"converted_{kind}")
            converted_files.append(stored_dxf)

            entities = parse_dxf(output_dxf_path)
            all_entities[f"{kind}_entities"] = [asdict(entity) for entity in entities]

        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            error_output = exc.stderr if isinstance(exc, subprocess.CalledProcessError) else str(exc)
            fail_logs = job.logs + [
                {
                    "step": "convert",
                    "status": "failed",
                    "timestamp": _timestamp(),
                    "error": error_output,
                }
            ]
            service.update_metadata(job_id, status="failed", progress=0.2, logs=fail_logs)
            raise RuntimeError(f"Conversion failed for {input_path}: {error_output}") from exc

    # --- Update metadata and prepare for next step ---
    done_logs = job.logs + [
        {
            "step": "convert",
            "status": "done",
            "timestamp": _timestamp(),
            "mode": "stub" if using_stub else "external",
        }
    ]
    job = service.update_metadata(
        job_id,
        progress=0.35,
        logs=done_logs,
        converted_files=job.converted_files + converted_files,
    )

    return {
        "job_id": job_id,
        "original_entities": all_entities.get("original_entities", []),
        "revised_entities": all_entities.get("revised_entities", []),
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


def _stub_convert(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    data = source.read_bytes() if source.exists() else b""
    destination.write_bytes(data or b"stub-dxf")


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

    # --- Normalize revised entities to align with original ---
    job = service.update_metadata(job_id, logs=job.logs + [{"step": "normalize", "status": "running", "timestamp": _timestamp()}])
    normalized_revised_entities = normalize_entities_by_grid(revised_entities, original_entities)
    job = service.update_metadata(job_id, logs=job.logs + [{"step": "normalize", "status": "done", "timestamp": _timestamp()}])
    # --- End Normalization ---

    matches = match_entities(original_entities, normalized_revised_entities)

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
