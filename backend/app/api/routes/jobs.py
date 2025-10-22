from fastapi import APIRouter, HTTPException, UploadFile, status

from app.models.responses import Envelope

router = APIRouter()


@router.post(
    "",
    response_model=Envelope[dict],
    status_code=status.HTTP_202_ACCEPTED,
    summary="提交 DWG 对比任务",
)
async def create_job(original_dwg: UploadFile, revised_dwg: UploadFile) -> Envelope[dict]:
    """提交两份 DWG 文件并创建比对任务。

    目前为占位实现，后续将加入任务队列与持久化。
    """

    if original_dwg.content_type not in {"application/octet-stream", "application/dwg"}:
        raise HTTPException(status_code=400, detail="original_dwg 文件类型不正确")

    if revised_dwg.content_type not in {"application/octet-stream", "application/dwg"}:
        raise HTTPException(status_code=400, detail="revised_dwg 文件类型不正确")

    # TODO: 写入临时存储，推入任务队列
    job_id = "demo-job-id"
    return Envelope(data={"job_id": job_id, "status": "queued"})


@router.get(
    "/{job_id}",
    response_model=Envelope[dict],
    summary="查询任务状态",
)
async def get_job_status(job_id: str) -> Envelope[dict]:
    """根据 job_id 返回任务状态。

    当前返回模拟数据，后续将对接数据库或 JSON 存储。
    """

    if job_id != "demo-job-id":
        raise HTTPException(status_code=404, detail="任务不存在")

    return Envelope(data={"job_id": job_id, "status": "processing", "progress": 0.25})
