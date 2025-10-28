from __future__ import annotations

import json
import subprocess
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, Iterable, Literal, cast

from celery import Task, chain

from app.core.settings import get_settings
from app.models import (
    DiffEntity,
    DiffPolygon,
    DiffSummary,
    JobDiffPayload,
    JobMetadata,
    StoredFile,
)
from app.services import JobService, ParsedEntity, match_entities, normalize_entities_by_grid, parse_dxf, render_diff_pdf
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
    if value:
        candidate = Path(value)
        if candidate.exists():
            return candidate

    return None


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


def _log_event(
    job_id: str,
    step: str,
    status: str,
    *,
    job: JobMetadata | None = None,
    level: Literal["info", "warning", "error"] = "info",
    updates: Dict[str, Any] | None = None,
    **fields: Any,
) -> JobMetadata:
    service = _service()
    current_job = job or service.load_job(job_id)
    entry = {
        "step": step,
        "status": status,
        "level": level,
        "timestamp": _timestamp(),
        **fields,
    }
    payload: Dict[str, Any] = {"logs": current_job.logs + [entry]}
    if updates:
        payload.update(updates)
    return service.update_metadata(job_id, **payload)


def _handle_task_exception(
    task: Task,
    job_id: str,
    step: str,
    exc: Exception,
    *,
    progress: float | None = None,
    context: Dict[str, Any] | None = None,
) -> None:
    attempt = task.request.retries + 1
    max_attempts = (task.max_retries or 0) + 1
    log_status = "retrying" if attempt < max_attempts else "failed"
    log_level: Literal["info", "warning", "error"] = "warning" if attempt < max_attempts else "error"
    update_fields: Dict[str, Any] = {"status": "failed" if attempt >= max_attempts else "processing"}
    if progress is not None:
        update_fields["progress"] = progress
    details: Dict[str, Any] = {
        "attempt": attempt,
        "max_attempts": max_attempts,
        "error": str(exc),
    }
    if context:
        details.update(context)
    _log_event(job_id, step, log_status, level=log_level, updates=update_fields, **details)
    if attempt >= max_attempts:
        raise RuntimeError(f"{step} task failed after {attempt} attempts: {exc}") from exc
    raise task.retry(exc=exc)


@celery_app.task(name="jobs.convert", bind=True, max_retries=2, default_retry_delay=15)
def convert_job_task(self: Task, job_id: str) -> Dict[str, Any]:
    """Converts DWG files to DXF using an external converter."""
    service = _service()
    job = service.load_job(job_id)
    job = _log_event(job_id, "convert", "running", job=job, updates={"status": "processing", "progress": 0.1})

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
                if using_stub:
                    output_dxf_path.write_bytes(b"stub-dxf")
                else:
                    raise FileNotFoundError(
                        f"Converter failed to produce output file: {output_dxf_path}\n"
                        f"stdout: {result_stdout}\nstderr: {result_stderr}"
                    )

            stored_dxf = _build_stored_file(output_dxf_path, content_type="application/vnd.dxf", kind=f"converted_{kind}")
            converted_files.append(stored_dxf)

            entities = parse_dxf(output_dxf_path, source=cast(Literal["original", "revised"], kind))
            all_entities[f"{kind}_entities"] = [asdict(entity) for entity in entities]

        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            error_output = exc.stderr if isinstance(exc, subprocess.CalledProcessError) else str(exc)
            _handle_task_exception(
                self,
                job_id,
                "convert",
                exc,
                progress=0.2,
                context={"file": str(input_path), "details": error_output},
            )

    # --- Update metadata and prepare for next step ---
    latest_job = service.load_job(job_id)
    job = _log_event(
        job_id,
        "convert",
        "done",
        job=latest_job,
        updates={
            "progress": 0.35,
            "converted_files": latest_job.converted_files + converted_files,
            "status": "processing",
        },
        mode="stub" if using_stub else "external",
        converted_count=len(converted_files),
    )

    return {
        "job_id": job_id,
        "original_entities": all_entities.get("original_entities", []),
        "revised_entities": all_entities.get("revised_entities", []),
    }


@celery_app.task(name="jobs.extract", bind=True, max_retries=2, default_retry_delay=15)
def extract_job_task(self: Task, payload: Dict[str, Any]) -> Dict[str, Any]:
    job_id = payload["job_id"]
    original_entities = payload.get("original_entities", [])
    revised_entities = payload.get("revised_entities", [])

    service = _service()
    job = service.load_job(job_id)

    job = _log_event(job_id, "extract", "running", job=job, updates={"progress": 0.45, "status": "processing"})

    extract_dir = _job_dir(job_id) / "extracted"
    extracted_path = extract_dir / "entities.json"

    try:
        extract_dir.mkdir(parents=True, exist_ok=True)
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
    except Exception as exc:  # pragma: no cover - filesystem errors are environment-specific
        _handle_task_exception(
            self,
            job_id,
            "extract",
            exc,
            progress=0.5,
            context={"target": str(extracted_path)},
        )

    latest_job = service.load_job(job_id)
    job = _log_event(
        job_id,
        "extract",
        "done",
        job=latest_job,
        updates={"progress": 0.65, "status": "processing"},
        output=str(extracted_path),
    )

    payload.update({"extracted_path": str(extracted_path.resolve())})
    return payload


def _deserialize_entities(entities: Iterable[dict[str, Any]]) -> list[ParsedEntity]:
    parsed_entities: list[ParsedEntity] = []
    for item in entities:
        vertices = [tuple(vertex) for vertex in item.get("vertices", [])]
        parsed_entities.append(
            ParsedEntity(
                entity_id=item.get("entity_id", ""),
                entity_type=item.get("entity_type", "UNKNOWN"),
                vertices=vertices,
                layer=item.get("layer"),
                color=item.get("color"),
                linetype=item.get("linetype"),
                source=item.get("source"),
            )
        )
    return parsed_entities


def _stub_convert(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    data = source.read_bytes() if source.exists() else b""
    destination.write_bytes(data or b"stub-dxf")


@celery_app.task(name="jobs.match", bind=True, max_retries=2, default_retry_delay=15)
def match_job_task(self: Task, payload: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise TypeError(f"match_job_task expected dict payload, got {type(payload)}")
    job_id = payload["job_id"]
    extracted_path = payload.get("extracted_path")

    service = _service()
    job = service.load_job(job_id)
    job = _log_event(
        job_id,
        "match",
        "running",
        job=job,
        updates={"progress": 0.8, "status": "processing"},
        source=extracted_path,
    )

    report_dir = _job_dir(job_id) / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "diff.json"
    original_entities = _deserialize_entities(payload.get("original_entities", []))
    revised_entities = _deserialize_entities(payload.get("revised_entities", []))

    # --- Normalize revised entities to align with original ---
    normalized_revised_entities = revised_entities
    try:
        job = _log_event(job_id, "normalize", "running", job=service.load_job(job_id), updates={"status": "processing"})
        normalized_revised_entities = normalize_entities_by_grid(revised_entities, original_entities)
        _log_event(job_id, "normalize", "done", job=service.load_job(job_id), updates={"status": "processing"})
    except Exception as exc:  # pragma: no cover - normalization errors depend on CAD stack
        _handle_task_exception(self, job_id, "normalize", exc, progress=0.8)

    pdf_file: StoredFile | None = None
    report_file: StoredFile | None = None

    try:
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

        pdf_path = report_dir / "diff-overlay.pdf"
        try:
            used_rich_renderer = render_diff_pdf(
                job_id,
                original_entities=original_entities,
                revised_entities=normalized_revised_entities,
                diff_entities=diff_entities,
                output_path=pdf_path,
            )
            pdf_file = _build_stored_file(pdf_path, content_type="application/pdf", kind="pdf_overlay")
        except Exception as pdf_exc:  # pragma: no cover - renderer failures should not abort job
            _log_event(
                job_id,
                "report",
                "failed",
                updates={"status": "processing"},
                level="warning",
                error=str(pdf_exc),
            )
        else:
            renderer_mode = "rich" if used_rich_renderer else "stub"
            _log_event(
                job_id,
                "report",
                "done",
                updates={"status": "processing"},
                renderer=renderer_mode,
                path=str(pdf_path),
            )
    except Exception as exc:
        _handle_task_exception(
            self,
            job_id,
            "match",
            exc,
            progress=0.9,
            context={"report_path": str(report_path)},
        )

    latest_job = service.load_job(job_id)
    updated_reports = latest_job.reports + ([report_file] if report_file else [])
    if pdf_file is not None:
        updated_reports = updated_reports + [pdf_file]

    job = _log_event(
        job_id,
        "match",
        "done",
        job=latest_job,
        updates={
            "status": "completed",
            "progress": 1.0,
            "reports": updated_reports,
        },
        report=report_file.path if report_file else None,
    )

    if report_file:
        payload.update({"status": job.status, "report_path": report_file.path})
    else:
        payload.update({"status": job.status})
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
