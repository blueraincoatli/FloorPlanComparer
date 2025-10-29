"""
Converter API routes for DWG to PDF conversion with natural language processing
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import uuid
import os
import json
from pathlib import Path
from typing import Dict, Any
from app.tasks.converter_tasks import process_dwg_conversion_with_params
from app.services.jobs import JobService
from app.models.jobs import JobCreate, JobStatus
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/converter", tags=["converter"])

class AnalysisRequest(BaseModel):
    """Request model for natural language analysis"""
    request: str

class AnalysisResponse(BaseModel):
    """Response model for natural language analysis"""
    params: Dict[str, Any]
    interpreted_requirements: str

def analyze_natural_language_request(user_request: str) -> Dict[str, Any]:
    """
    Analyze natural language request and convert to conversion parameters

    :param user_request: Natural language description of conversion requirements
    :return: Dictionary of conversion parameters
    """

    # Default parameters
    params = {
        "auto_fit": True,
        "center": True,
        "paper_size": None,
        "margin": None,
        "grayscale": False,
        "monochrome": False
    }

    # Convert to lowercase for easier matching
    request_lower = user_request.lower()

    # Paper size detection
    paper_sizes = {
        "a4": "A4",
        "a3": "A3",
        "a2": "A2",
        "a1": "A1",
        "a0": "A0",
        "letter": "Letter",
        "legal": "Legal"
    }

    for size_key, size_value in paper_sizes.items():
        if size_key in request_lower:
            params["paper_size"] = size_value
            break

    # Margin detection (look for numbers followed by 'mm' or 'cm')
    import re
    margin_patterns = [
        r'(\d+)\s*mm',  # e.g., "10mm", "10 mm"
        r'(\d+(?:\.\d+)?)\s*cm',  # e.g., "1.5cm", "1.5 cm"
        r'边距\s*(\d+)',  # Chinese pattern: "边距10"
    ]

    for pattern in margin_patterns:
        match = re.search(pattern, request_lower)
        if match:
            margin_value = float(match.group(1))
            if 'cm' in pattern:
                margin_value *= 10  # Convert cm to mm
            params["margin"] = margin_value
            break

    # Color/Grayscale/Monochrome detection
    if any(word in request_lower for word in ["黑白", "黑白色", "单色", "monochrome", "black and white"]):
        params["monochrome"] = True
        params["grayscale"] = False
    elif any(word in request_lower for word in ["灰度", "grayscale", "gray", "灰色"]):
        params["grayscale"] = True
        params["monochrome"] = False
    elif any(word in request_lower for word in ["彩色", "color", "彩色打印", "彩印"]):
        params["grayscale"] = False
        params["monochrome"] = False

    # Layout settings
    if any(word in request_lower for word in ["居中", "center", "中间对齐"]):
        params["center"] = True
    elif any(word in request_lower for word in ["左对齐", "left align", "左对齐"]):
        params["center"] = False

    if any(word in request_lower for word in ["自动适应", "auto fit", "自动调整", "自适应"]):
        params["auto_fit"] = True
    elif any(word in request_lower for word in ["不自动", "manual", "手动", "固定尺寸"]):
        params["auto_fit"] = False

    # Quality settings
    if any(word in request_lower for word in ["高清", "high quality", "高质量", "hq"]):
        # Could be used for future quality parameter
        pass

    return params

def generate_requirements_summary(params: Dict[str, Any], user_request: str) -> str:
    """
    Generate a human-readable summary of interpreted requirements

    :param params: Conversion parameters
    :param user_request: Original user request
    :return: Summary string
    """
    summaries = []

    if params.get("paper_size"):
        summaries.append(f"纸张大小: {params['paper_size']}")

    if params.get("margin"):
        summaries.append(f"边距: {params['margin']}mm")

    if params.get("monochrome"):
        summaries.append("输出模式: 黑白")
    elif params.get("grayscale"):
        summaries.append("输出模式: 灰度")
    else:
        summaries.append("输出模式: 彩色")

    if params.get("auto_fit"):
        summaries.append("布局: 自动适应页面")
    else:
        summaries.append("布局: 手动设置")

    if params.get("center"):
        summaries.append("对齐: 居中")

    return "，".join(summaries) if summaries else "使用默认设置"

@router.post("/analyze-request", response_model=AnalysisResponse)
async def analyze_request(request: AnalysisRequest):
    """
    Analyze natural language conversion request

    :param request: Analysis request containing user's natural language description
    :return: Analyzed parameters and requirements summary
    """
    try:
        logger.info(f"Analyzing request: {request.request}")

        # Analyze the natural language request
        params = analyze_natural_language_request(request.request)

        # Generate human-readable summary
        summary = generate_requirements_summary(params, request.request)

        logger.info(f"Analyzed parameters: {params}")

        return AnalysisResponse(
            params=params,
            interpreted_requirements=summary
        )

    except Exception as e:
        logger.error(f"Error analyzing request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

@router.post("/convert-dwg")
async def convert_dwg_file(
    dwg_file: UploadFile = File(..., description="DWG file to convert"),
    params: str = Form(..., description="JSON string of conversion parameters")
):
    """
    Convert DWG file to PDF with specified parameters

    :param dwg_file: DWG file to convert
    :param params: JSON string of conversion parameters
    :return: Job information
    """
    try:
        # Validate file type
        if not dwg_file.filename or not dwg_file.filename.lower().endswith('.dwg'):
            raise HTTPException(status_code=400, detail="请上传 DWG 文件")

        # Parse parameters
        try:
            conversion_params = json.loads(params)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="参数格式错误")

        # Generate job ID
        job_id = str(uuid.uuid4())

        # Create job directory
        job_dir = Path("storage") / "jobs" / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        # Save uploaded file
        dwg_path = job_dir / f"input_{dwg_file.filename}"

        with open(dwg_path, "wb") as f:
            f.write(await dwg_file.read())

        # Create job record
        job_data = JobCreate(
            id=job_id,
            origin_filename=dwg_file.filename,
            target_filename="output.pdf",
            status=JobStatus.PENDING
        )

        job_service = JobService(Path("storage"))
        job = job_service.create_job_from_data(job_data)

        # Start conversion task
        process_dwg_conversion_with_params.delay(job_id, str(dwg_path), conversion_params)

        logger.info(f"Started DWG conversion job {job_id} for file {dwg_file.filename}")

        return {
            "job_id": job_id,
            "status": "processing",
            "message": "转换任务已提交"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting DWG conversion: {str(e)}")
        raise HTTPException(status_code=500, detail=f"转换失败: {str(e)}")

@router.get("/job/{job_id}")
async def get_conversion_job_status(job_id: str):
    """
    Get conversion job status and results

    :param job_id: ID of the conversion job
    :return: Job status and results
    """
    try:
        job_service = JobService(Path("storage"))
        job = job_service.load_job(job_id)

        # Get task result if completed
        if job.status == "completed":
            return {
                "job_id": job_id,
                "status": job.status,
                "progress": job.progress,
                "created_at": job.created_at.isoformat(),
                "updated_at": job.updated_at.isoformat(),
                "reports": [report.dict() for report in job.reports],
                "logs": job.logs
            }

        return {
            "job_id": job_id,
            "status": job.status,
            "progress": job.progress,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat(),
            "logs": job.logs
        }

    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}")

@router.get("/job/{job_id}/download")
async def download_converted_file(job_id: str):
    """
    Download converted PDF file

    :param job_id: ID of the conversion job
    :return: PDF file download
    """
    try:
        job_service = JobService(Path("storage"))

        # Get the converted file
        try:
            report_file = job_service.get_report_file(job_id, "pdf")
        except Exception:
            raise HTTPException(status_code=404, detail="转换文件未找到")

        if not report_file.path or not Path(report_file.path).exists():
            raise HTTPException(status_code=404, detail="转换文件未找到")

        return FileResponse(
            path=report_file.path,
            filename=report_file.name,
            media_type="application/pdf"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading converted file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")