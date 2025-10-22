from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class Envelope(BaseModel, Generic[DataT]):
    """统一响应包装。"""

    code: int = Field(default=0, description="0 表示成功，非 0 表示错误码")
    data: DataT | None = Field(default=None, description="具体数据载荷")
    message: str = Field(default="", description="错误或提示信息")


class HealthData(BaseModel):
    """健康检查响应负载。"""

    status: str = Field(default="ok", description="服务状态")
