"""
Enhanced API routes for AutoCAD integration
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional
import uuid
import os
from pathlib import Path
from app.tasks.enhanced_jobs import process_dwg_files_with_autocad
from app.services.jobs import JobService
from app.models.jobs import JobCreate, JobStatus
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/enhanced", tags=["enhanced"])

@router.post("/process-dwg")
async def process_dwg_files(
    origin_file: UploadFile = File(...),
    target_file: UploadFile = File(...),
    auto_fit: bool = Form(True),
    center: bool = Form(True),
    paper_size: Optional[str] = Form(None),
    margin: Optional[float] = Form(None),
    grayscale: bool = Form(False),
    monochrome: bool = Form(False)
):
    """
    Process DWG files using AutoCAD integration
    
    :param origin_file: Original DWG file
    :param target_file: Target DWG file
    :param auto_fit: Auto fit content to page
    :param center: Center content on page
    :param paper_size: Paper size for output
    :param margin: Paper margin in mm
    :param grayscale: Convert to grayscale
    :param monochrome: Convert to monochrome (black/white)
    :return: Job information
    """
    try:
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Create job directory
        job_dir = Path("storage") / "jobs" / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        
        # Save uploaded files
        origin_path = job_dir / f"origin_{origin_file.filename}"
        target_path = job_dir / f"target_{target_file.filename}"
        
        with open(origin_path, "wb") as f:
            f.write(await origin_file.read())
        
        with open(target_path, "wb") as f:
            f.write(await target_file.read())
        
        # Create job record
        job_data = JobCreate(
            id=job_id,
            origin_filename=origin_file.filename,
            target_filename=target_file.filename,
            status=JobStatus.PENDING
        )
        
        job_service = JobService()
        job = job_service.create_job(job_data)
        
        # Start processing task
        process_dwg_files_with_autocad.delay(job_id, str(origin_path), str(target_path))
        
        return {"job_id": job_id, "status": "processing"}
        
    except Exception as e:
        logger.error(f"Error processing DWG files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/job/{job_id}")
async def get_enhanced_job_status(job_id: str):
    """
    Get enhanced job status
    
    :param job_id: ID of the job
    :return: Job status and results
    """
    try:
        job_service = JobService()
        job = job_service.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Get task result if completed
        if job.status == JobStatus.COMPLETED:
            # Return job details with results
            return job
            
        return {"job_id": job_id, "status": job.status}
        
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))