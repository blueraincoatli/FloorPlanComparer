# Floor Plan Comparison Backend

基于 FastAPI 构建的后端服务，负责文件上传、任务调度、几何解析与差异计算。

## 本地开发

```powershell
pwsh scripts/setup_env.ps1
. backend\.venv\Scripts\Activate.ps1
uv run --project backend uvicorn app.main:app --reload
```

## 运行测试

```powershell
uv run --project backend pytest
```

## 启动 Celery Worker

默认情况下（`FLOORPLAN_CELERY_TASK_ALWAYS_EAGER=true`）任务会同步执行，无需独立 worker。
若要启用真实异步队列并连接 Redis：

```powershell
$env:FLOORPLAN_CELERY_BROKER_URL = "redis://localhost:6379/0"
$env:FLOORPLAN_CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
$env:FLOORPLAN_CELERY_TASK_ALWAYS_EAGER = "false"
celery -A app.worker.celery_app worker --loglevel=info
```

## 容器化运行

项目提供 `backend/Dockerfile` 与 `ops/compose/docker-compose.yml`：

```bash
docker compose -f ops/compose/docker-compose.yml up --build
```

该命令会同时启动 FastAPI `api` 服务、Celery `worker`、以及 Redis broker（默认监听 `8000` 端口）。

更多细节请参考根目录 `PLAN.md`。
