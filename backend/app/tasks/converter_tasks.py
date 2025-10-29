"""
Converter tasks for DWG to PDF conversion with custom parameters
"""
import os
import tempfile
from pathlib import Path
from typing import Dict, Any
from celery import current_task
from app.modules.dwg_to_pdf.converter import convert_dwg_to_pdf
import logging

logger = logging.getLogger(__name__)

def process_dwg_conversion_with_params(job_id: str, dwg_path: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process DWG file conversion with custom parameters

    :param job_id: ID of the job
    :param dwg_path: Path to DWG file
    :param params: Conversion parameters
    :return: Processing results
    """
    try:
        # Update task state
        current_task.update_state(state='PROGRESS', meta={'status': '正在转换 DWG 文件'})

        # Create output path
        dwg_file = Path(dwg_path)
        output_path = dwg_file.parent / "output.pdf"

        # Extract conversion parameters with defaults
        conversion_params = {
            'auto_fit': params.get('auto_fit', True),
            'center': params.get('center', True),
            'paper_size': params.get('paper_size'),
            'margin': params.get('margin'),
            'grayscale': params.get('grayscale', False),
            'monochrome': params.get('monochrome', False)
        }

        # Log conversion parameters
        logger.info(f"Converting {dwg_path} with params: {conversion_params}")

        # Convert DWG to PDF
        success = convert_dwg_to_pdf(dwg_path, str(output_path), **conversion_params)

        if not success:
            raise Exception("DWG 转 PDF 失败")

        # Update task state
        current_task.update_state(state='PROGRESS', meta={'status': '正在保存结果'})

        # Prepare results
        result = {
            "job_id": job_id,
            "status": "completed",
            "input_file": dwg_path,
            "output_file": str(output_path),
            "conversion_params": conversion_params,
            "output_exists": output_path.exists(),
            "output_size": output_path.stat().st_size if output_path.exists() else 0
        }

        logger.info(f"Job {job_id} completed successfully. Output: {output_path}")
        return result

    except Exception as e:
        logger.error(f"Error processing DWG conversion: {str(e)}")
        return {
            "job_id": job_id,
            "status": "failed",
            "error": str(e),
            "input_file": dwg_path
        }