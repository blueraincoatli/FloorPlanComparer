"""
Enhanced job tasks with AutoCAD integration
"""
import os
import tempfile
from pathlib import Path
from typing import Dict, Any
from celery import current_task
from app.modules.dwg_to_pdf.converter import convert_dwg_to_pdf
from app.services.pdf_comparison import compare_floor_plans
from app.models.jobs import JobStatus
import logging

logger = logging.getLogger(__name__)

def process_dwg_files_with_autocad(job_id: str, origin_path: str, target_path: str) -> Dict[str, Any]:
    """
    Process DWG files using AutoCAD for conversion and comparison
    
    :param job_id: ID of the job
    :param origin_path: Path to original DWG file
    :param target_path: Path to target DWG file
    :return: Processing results
    """
    try:
        # Update task state
        current_task.update_state(state='PROGRESS', meta={'status': 'Converting original DWG to PDF'})
        
        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Define output paths
            origin_pdf = temp_path / "origin.pdf"
            target_pdf = temp_path / "target.pdf"
            diff_image = temp_path / "diff.png"
            diff_json = temp_path / "diff.json"
            
            # Convert original DWG to PDF
            logger.info(f"Converting original DWG: {origin_path}")
            success1 = convert_dwg_to_pdf(origin_path, str(origin_pdf))
            
            if not success1:
                raise Exception("Failed to convert original DWG to PDF")
            
            # Update task state
            current_task.update_state(state='PROGRESS', meta={'status': 'Converting target DWG to PDF'})
            
            # Convert target DWG to PDF
            logger.info(f"Converting target DWG: {target_path}")
            success2 = convert_dwg_to_pdf(target_path, str(target_pdf))
            
            if not success2:
                raise Exception("Failed to convert target DWG to PDF")
            
            # Update task state
            current_task.update_state(state='PROGRESS', meta={'status': 'Comparing PDFs'})
            
            # Compare PDFs
            logger.info("Comparing PDFs")
            comparison_result = compare_floor_plans(
                str(origin_pdf), 
                str(target_pdf),
                output_image_path=str(diff_image),
                output_json_path=str(diff_json)
            )
            
            # Update task state
            current_task.update_state(state='PROGRESS', meta={'status': 'Preparing results'})
            
            # Prepare results
            result = {
                "job_id": job_id,
                "status": JobStatus.COMPLETED,
                "origin_pdf": str(origin_pdf),
                "target_pdf": str(target_pdf),
                "diff_image": str(diff_image),
                "diff_json": str(diff_json),
                "comparison": comparison_result
            }
            
            logger.info(f"Job {job_id} completed successfully")
            return result
            
    except Exception as e:
        logger.error(f"Error processing DWG files: {str(e)}")
        return {
            "job_id": job_id,
            "status": JobStatus.FAILED,
            "error": str(e)
        }