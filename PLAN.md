# Floor Plan Comparison 项目计划

## 1. 项目目标与约束
- 自动化比对事务所初稿与施工图的平面图差异，输出精确的矢量级变更结果。
- 全流程仅使用免费或开源工具链；禁止依赖 AutoCAD、ODA 付费 SDK。
- 所有 Python 相关任务必须在项目专属的 `uv` 管理虚拟环境中执行，禁止使用系统全局解释器。
- 交付成果需既具备数据精度，也要通过 Web 端提供友好、直观的差异可视化。
- 架构需可扩展，方便后续接入 AutoCAD 插件或 BIM 场景。


---

## 2. System Architecture（系统架构）

### 2.1 Architecture Overview
- **Frontend**: React + TypeScript SPA handles uploads, diff visualisation, tolerance configuration and report download.
- **API Layer**: FastAPI exposes upload/status/result REST endpoints; deployments may guard them with a shared API key and simple rate limiting via Nginx.
- **Orchestration**: Celery (or a lightweight background worker) processes convert/extract/match/report stages asynchronously while reading/writing job metadata files atomically.
- **Conversion Service**: ODA File Converter CLI runs inside job-scoped Docker sandboxes with CPU/RAM/IO quotas and wall-clock limits to isolate untrusted DWG files.
- **Metadata Store**: job state is persisted as JSON (or an embedded SQLite DB) under `storage/meta/`, keeping the footprint small while enabling retries and auditing.
- **Artefact Storage**: the local filesystem under `storage/jobs/<job_id>/` retains original DWG, converted DXF and generated artefacts until cleanup; MinIO/S3 support remains an optional future step.
- **Observability**: structured logs plus lightweight Prometheus exporters capture CLI runtimes, queue depth and API latency for troubleshooting.
- **Security Controls**: API gateway/WAF (when deployed), AV scanning, MIME sniffing, checksum validation, TLS termination and audit logs reduce the attack surface of file ingestion.

### 2.2 Processing Pipeline
1. Frontend uploads DWG files via the gateway; file size/type is validated and a job metadata record (`storage/meta/<job_id>.json`) is created.
2. API enqueues a `convert` task and stores original files under `storage/jobs/<job_id>/original/`; AV scanning + SHA256 hashing run before queueing.
3. Convert worker executes ODA CLI in a sandbox container, writes DXF into `storage/jobs/<job_id>/converted/`, records runtime stats and removes temporary files.
4. Extract worker uses `ezdxf` to normalise coordinates/units and stores parsed entities as JSON fragments alongside the job metadata.
5. Match worker applies `shapely` + `rtree` with the selected tolerance profile, persisting diff summaries/diagnostics into the metadata file and exporting lightweight JSON artefacts.
6. Report worker produces JSON/Excel/PDF/SVG overlays, deposits files in `storage/jobs/<job_id>/reports/` and updates job status timestamps.
7. API streams progress to the frontend via SSE/WebSocket/polling until artefacts are ready; once downloaded, cleanup policies may delete the entire job directory.

### 2.3 Workflow Code Example
Workflow Code Example
 核心代码示例（任务流程骨架）
```python
# backend/app/workflow.py
from pathlib import Path
from typing import Iterable

from app.converters import convert_dwg_to_dxf
from app.geometry import extract_entities, classify_entities
from app.matcher import match_entities
from app.report import build_reports


def run_comparison_job(job_id: str, source_a: Path, source_b: Path) -> dict:
    """核心流程：转换→解析→匹配→报告。"""
    dxf_a, dxf_b = convert_dwg_to_dxf(source_a), convert_dwg_to_dxf(source_b)

    entities_a = classify_entities(extract_entities(dxf_a))
    entities_b = classify_entities(extract_entities(dxf_b))

    diff_result = match_entities(entities_a, entities_b)

    artefacts: Iterable[Path] = build_reports(job_id, diff_result)
    return {
        "job_id": job_id,
        "status": "completed",
        "diff_summary": diff_result.summary(),
        "artefacts": [str(path) for path in artefacts],
    }
```

### 2.4 Risk & Operational Controls
- Sandbox the ODA CLI container per job and destroy it after completion to remove untrusted DWG files.
- Maintain task budgets (CPU/memory/runtime) with circuit breakers and alerting on repeated failures.
- Track API latency, queue depth and conversion duration through structured logs or lightweight metrics endpoints.
- Use Context7-backed version pinning to monitor breaking changes in geometry/CLI dependencies even without a central DB.
- Enforce retention policies (e.g., delete job folders after N days) via background cleanup jobs and checksum verification before removal.

---


## 3. API_design_guide（API 设计指南）

### 3.1 Principles
- RESTful routes follow `/jobs`, `/jobs/{job_id}`, `/jobs/{job_id}/artefacts` resources.
- Upload calls are asynchronous; clients poll or stream job states.
- Responses use the unified envelope `{"code": 0, "data": {...}, "message": ""}`.
- Internationalisation (zh/en) is supported via Accept-Language negotiation.
- Endpoints can be protected with a shared API key when needed; in single-team deployments this may be optional.
- Basic Nginx rate limits (or Cloudflare rules) protect the upload/status APIs from abuse without heavy infrastructure.

### 3.2 Core Endpoints
1. `POST /jobs`: accepts DWG pair uploads (size capped, AV scanned), persists metadata, returns `job_id` and presigned upload references when using multipart offload.
2. `GET /jobs/{job_id}`: returns job status timeline, progress percentages and recent task logs.
3. `GET /jobs/{job_id}/diff`: streams structured diff JSON (paginated) subject to tenant access rules.
4. `GET /jobs/{job_id}/artefacts/{type}`: streams files from `storage/jobs/<job_id>/reports/` (optionally issuing short-lived tokens when exposed over HTTP).
5. `DELETE /jobs/{job_id}`: removes the job directory/metadata after verifying no downloads are in progress.

### 3.3 Request/Response Constraints
- Upload requests use `multipart/form-data` (fields `original_dwg`, `revised_dwg`, optional `tolerance_profile`) or presigned S3 uploads for large files.
- DWG size is capped (e.g., 200 MB) with a global limit defined in config; rejected files return `413 Payload Too Large`.
- All uploads pass MIME sniffing and AV scanning before queuing; SHA256 checksums are stored for dedup and tamper detection.
- Artefact downloads use short-lived tokens or direct file responses; at-rest storage relies on filesystem permissions (or disk encryption when available).
- Error payloads follow the same envelope but include `error_code` and trace correlation IDs.

### 3.4 FastAPI 核心代码示例
```python
# backend/app/api/routes/jobs.py
from pathlib import Path
import json
from fastapi import APIRouter, BackgroundTasks, UploadFile, File, HTTPException
from ..tasks import enqueue_job

META_DIR = Path("storage/meta")
router = APIRouter(prefix="/jobs", tags=["jobs"])


def load_job(job_id: str) -> dict:
    meta_path = META_DIR / f"{job_id}.json"
    if not meta_path.exists():
        raise HTTPException(status_code=404, detail="Job not found")
    return json.loads(meta_path.read_text(encoding="utf-8"))


@router.post("", summary="Create comparison job")
async def create_job(
    background_tasks: BackgroundTasks,
    original_dwg: UploadFile = File(...),
    revised_dwg: UploadFile = File(...),
):
    job_id = await enqueue_job(background_tasks, original_dwg, revised_dwg)
    return {"code": 0, "data": {"job_id": job_id}, "message": ""}


@router.get("/{job_id}", summary="Get job status")
async def get_job_status(job_id: str):
    job = load_job(job_id)
    return {"code": 0, "data": job, "message": ""}
```


---

## 4. Storage_Layout

### 4.1 Directory Structure
- `storage/meta/<job_id>.json`: metadata describing job status, timestamps, tolerance profile, and pointers to artefacts.
- `storage/jobs/<job_id>/original/`: uploaded DWG files plus checksum/scan results.
- `storage/jobs/<job_id>/converted/`: DXF outputs and intermediate geometry JSON fragments.
- `storage/jobs/<job_id>/reports/`: generated JSON/Excel/PDF/SVG artefacts.
- `storage/temp/`: short-lived scratch space wiped after each task.

### 4.2 Metadata Schema Example
```json
{
  "job_id": "20241022-0915-XYZ",
  "created_at": "2024-10-22T09:15:00Z",
  "status": "processing",
  "progress": 0.45,
  "tolerance_profile": "default",
  "files": {
    "original": ["storage/jobs/.../original/a.dwg", "storage/jobs/.../original/b.dwg"],
    "converted": ["storage/jobs/.../converted/a.dxf", "storage/jobs/.../converted/b.dxf"]
  },
  "logs": [
    {"step": "convert", "status": "done", "duration_sec": 32},
    {"step": "extract", "status": "running"}
  ],
  "reports": [
    {"type": "overlay_pdf", "path": "storage/jobs/.../reports/diff.pdf", "checksum": "..."}
  ]
}
```

### 4.3 Cleanup & Retention
- Default retention deletes job directories and metadata 30 days after completion (configurable).
- Manual purge command `scripts/cleanup_jobs.py --older-than 30d` removes orphaned folders and verifies checksums.
- Optional offloading hooks can archive completed artefacts to cloud storage before deletion.

## 5. Development_workflow��������������
 Development_workflow（开发工作流）

### 5.1 环境准备
1. 安装 `uv`（参考官方文档）。
2. 初始化虚拟环境：`uv venv .venv`。
3. 激活环境：Windows `uv pip activate .venv`，Linux/macOS `source .venv/bin/activate`。
4. 使用 `uv pip install -r requirements.txt` 或 `uv pip install -r pyproject.toml` 统一安装依赖。

### 5.2 Collaboration & Delivery
- Reference Context7 MCP for up-to-date CAD/geometry docs before implementing converters or matchers.
- Use feature branches (`feature/<topic>`) and keep Celery/worker changes isolated for easy rollback.
- Sync dependencies via `uv pip sync` and pin ODA/geometry library versions in `pyproject.toml`.
- For every PR, run `uv run pytest`, `uv run mypy`, and the lint suite; attach Celery task logs when fixing pipeline issues.
- Record architecture decisions (ADR) whenever conversion quotas, tolerance policies, or storage retention values change.
- When testing locally, use sample DWGs from `samples/` and observe pipeline traces in OpenTelemetry collector.

### 5.3 自动化
- `pre-commit` 配置 `black`, `isort`, `flake8`, `mypy`, `ruff`。
- `pytest` 覆盖率目标 80% 以上。
- GitHub Actions CI 基于 `uv` 搭建缓存，执行 lint + test。

### 5.4 核心命令示例
```bash
# 新同事克隆仓库后
uv venv .venv
uv pip install poetry
uv pip install -r requirements.lock
uv run poetry install

# 运行本地服务
uv run uvicorn app.main:app --reload

# 执行测试
uv run pytest -m "not slow"
```

---

## 6. Deployment_guide（部署指引）

### 6.1 架构选项
- **开发/测试环境**：Docker Compose 默认包含 `api`、`worker`、`frontend`、`redis`；`postgres` 与 `minio` 仅在后续扩展数据持久化或对象存储时启用。
> Optional services (Postgres/MinIO) stay disabled for the file-based MVP; enable them only when persistence/remote storage is required.
- **正式部署**：Kubernetes (k3s/EKS) 或 Docker Swarm + CDN/Nginx；若启用外部数据库/对象存储，再追加相应的 Stateful 服务。
- **存储备份**：使用对象存储（S3/MinIO）并启用版本化，防止误删。

### 6.2 Docker Compose 示例
```yaml
# ops/compose/docker-compose.yml
services:
  api:
    build: ../..
    command: uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
    environment:
      - JOB_STORAGE_PATH=/app/storage
    volumes:
      - ../../storage:/app/storage
    depends_on: [redis]

  worker:
    build: ../..
    command: uv run celery -A app.worker worker --loglevel=info
    depends_on: [api]

  frontend:
    build:
      context: ../../frontend
      target: production
    ports:
      - "3000:80"

  redis:
    image: redis:7-alpine

  # Optional services for future scaling:
  # db:
  #   image: postgis/postgis:16-3.4
  #   environment:
  #     - POSTGRES_DB=floorplan
  #     - POSTGRES_USER=floorplan
  #     - POSTGRES_PASSWORD=floorplan

  # minio:
  #   image: minio/minio:RELEASE.2024-01-29T03-56-32Z
  #   command: server /data
  #   ports:
  #     - "9000:9000"
  #   environment:
  #     - MINIO_ROOT_USER=admin
  #     - MINIO_ROOT_PASSWORD=admin123
```


### 6.3 部署步骤
1. 服务器安装 Docker, Docker Compose。
2. Copy `.env.example` to `.env` and fill Celery/Redis/API settings; add PostgreSQL/MinIO variables only if enabling those optional services.
3. 运行 `docker compose up -d --build`。
4. (Optional) Run Alembic migrations only when a database backend is enabled; skip for the metadata-file MVP.
5. 配置反向代理（Nginx/Caddy），启用 HTTPS。
6. 配置定时任务清理历史任务与临时文件。

### 6.4 监控与告警
- 收集 API/Worker 日志到 ELK 或 Loki。
- Prometheus tracks `uvicorn`, `celery`, `redis`; enable PostgreSQL/MinIO exporters only when those optional components are deployed.
- 告警渠道：邮件、Slack、企业微信。

---

## 7. UI_design_guide（UI 设计指南）

### 7.1 前端信息架构
- **导航区**：logo、任务列表入口、容差设置、语言切换。
- **主视图**：左右分屏（原图/施工图）或叠加视图，支持单独/叠加切换。
- **差异图层控制**：新增/删除/移动/属性修改四类开关。
- **差异列表面板**：按楼层、构件类型、严重程度排序；可定位到具体区域。
- **报告与导出**：提供 Excel、PDF、DXF overlay 下载按钮。
- **状态反馈**：任务上传、排队、解析、匹配阶段的进度条与状态提示。

### 7.2 交互规范
- 支持鼠标/触控双操作：滚轮缩放、右键拖拽、双指缩放。
- 差异提示遵循颜色规范：新增=绿色、删除=红色、移动=黄色、属性修改=蓝色。
- 悬浮提示显示详细属性对比（尺寸、文本、块属性等）。
- 提供键盘快捷键（例如 `1-4` 切换差异层，`F` 聚焦选中差异）。

### 7.3 React 组件结构
- `pages/UploadPage`：上传和任务历史。
- `pages/ReviewPage`：主审查界面。
  - `components/ViewerCanvas`：基于 `Paper.js`/`Two.js` 渲染矢量图。
  - `components/DiffLayerToggle`：图层开关。
  - `components/DiffListPanel`：差异列表。
  - `components/ReportActions`：导出操作。

### 7.4 核心组件示例
```tsx
// frontend/src/components/viewer/ViewerCanvas.tsx
import { useEffect, useRef } from "react";
import { DiffEntity } from "@/types";

type Props = {
  originalGeometry: DiffEntity[];
  revisedGeometry: DiffEntity[];
  activeFilters: Set<string>;
  onSelect: (entity: DiffEntity) => void;
};

export function ViewerCanvas({ originalGeometry, revisedGeometry, activeFilters, onSelect }: Props) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    if (!canvasRef.current) return;
    // 初始化 Paper.js 场景
    const paper = initPaperScene(canvasRef.current);
    const layers = buildDiffLayers(paper, originalGeometry, revisedGeometry);
    applyFilters(layers, activeFilters);
    return () => paper?.remove();
  }, [originalGeometry, revisedGeometry, activeFilters]);

  return <canvas ref={canvasRef} className="h-full w-full bg-neutral-900" onClickCapture={handleClick(onSelect)} />;
}
```

### 7.5 设计交付物
- 低保真线框：Figma / Penpot。
- UI 组件规范：颜色、间距、字体、图标库（支持深色模式）。
- 动效指引：差异图层切换需 150ms 淡入淡出。

---

## 8. 时间规划（建议）

| 阶段 | 时间 | 主要成果 |
|------|------|----------|
| Phase 0 | 第 1 周 | 代码仓库结构、`uv` 环境脚本、转换工具封装 |
| Phase 1 | 第 2-3 周 | 上传/任务 API、转换与归一化模块、单元测试 |
| Phase 2 | 第 4-6 周 | 几何分类、匹配引擎、差异 JSON |
| Phase 3 | 第 7 周 | Excel/PDF/DXF 报告、容差配置 |
| Phase 4 | 第 8-9 周 | Web UI、矢量可视化、交互优化 |
| Phase 5 | 第 10 周 | 性能优化、试点上线、文档与培训 |

---

## 9. 后续扩展方向
- AutoCAD/BricsCAD 插件调用 REST API，实现 CAD 内部差异高亮。
- 引入机器学习识别块类型，减少手动配置。
- 集成版本历史与审批流，支撑多版本变更追踪。
- 支持 IFC/BIM 模型对比，扩展到三维场景。

> 本计划文档为内部指导文件，后续迭代请保持 `uv` 虚拟环境约束与免费工具原则不变，并在变更后更新相应章节。












## 10. 2025-10-23 Audit Follow-ups
1. Restore a runnable pipeline: keep the mock CAD flow until the `ezdxf`/`shapely`/`rtree` stack is packaged and optional, so tests can pass before heavy deps land.
2. Extend `backend/pyproject.toml` with CAD extras, export `normalize_entities_by_grid`, and document configuration knobs (ODA path, task toggles) via settings.
3. Wrap the ODA converter behind a configurable adapter (e.g., `FLOORPLAN_CONVERTER_PATH`) and plan container sandboxing for cross-platform execution.
4. Improve Celery error reporting and retries so the API can expose failed/terminal states with meaningful messages instead of stuck `processing` jobs.
5. Clean the repo: remove `node_modules`, `dist`, `.venv`, and installer binaries from version control and tighten `.gitignore` plus contributor docs.
6. Split the React UI into Upload/List/Diff/Summary components and define an async status contract (polling or WebSocket) with the backend.

## 11. 2025-10-26 PDF 叠加差异方案计划
### 目标
为每个比对任务生成一份矢量 PDF，叠加原图、改图及差异高亮层，并在前端提供预览/下载入口，以解决 SVG 渲染大量 CAD 实体的可视化问题。

### 阶段一：后端数据扩展
1. 扫描已有 DXF 实体，定义图层/对象过滤策略（优先保留主要建筑轮廓、墙体、门窗等），并确定对齐基准（坐标或特定图层）。
2. 在 `parse_dxf` 输出结构内保留原始实体的坐标、图层、颜色等元数据；diff 结果额外携带实体来源（original/revised）。
3. 若 `normalize_entities_by_grid` 成功识别参考网格，则统一应用缩放/平移，确保原图与改图坐标可直接叠加。

### 阶段二：PDF 渲染服务
1. 评估 ODA File Converter 的 PDF 输出能力；若支持则组合成批处理命令生成单独的原图/改图 PDF。
2. 若 ODA 无法满足叠图需求，使用 cairo/PyMuPDF/ReportLab 等库手工绘制多边形；实现：
   - 背景层（原图）使用浅灰描边；改图使用浅蓝；新增实体绿色填充；删除实体红色填充；
   - 支持多页（原图、改图、叠加）或单页合成。
3. 将 PDF 输出写入 `reports/`，在 Job metadata 中登记，并记录生成日志。

### 阶段三：前端集成
1. 在 `DiffViewer` 中新增“打开 PDF 差异报告”按钮，优先尝试内嵌 `<iframe>` 预览，不支持时提供下载。
2. 在全屏视图添加同样入口，并展示生成时间、文件大小等信息。
3. 若 PDF 暂未生成（例如任务旧数据），界面提示“差异报告生成中/不可用”，可触发后台补算。

### 阶段四：验证与优化
1. 使用 `originFile` 中的样例 DWG 生成 PDF，并人工检查叠图是否对齐、颜色是否清晰。
2. 记录耗时与输出体积，评估是否需要对实体过滤、抽稀或分页。
3. 编写最小化集成测试（至少覆盖任务完成后 PDF 是否存在、API 是否返回下载链接）。

---

## 12. 2025-10-27 DWG → DXF → PDF 差异叠加方案规划

### 目标
仅要求用户上传 DWG，即可自动输出一份叠加原图、改图及差异高亮的矢量 PDF；同时保留现有差异 JSON 供前端或其他系统使用。

### 流程概览
1. DWG → DXF：使用现有 ODA Converter 脚本，确保统一版本（如 ACAD2018）。
2. DXF → 中间几何模型：调用 `parse_dxf`，获取实体坐标、图层、颜色、来源（original/revised）。
3. 对齐：利用 `normalize_entities_by_grid` 或图层/图框信息，对 revised 坐标进行仿射变换，使两版图纸在同一坐标系下重合。
4. 差异标注：沿用 `match_entities` 结果，把新增、删除实体分组；记录其顶点信息和风格。
5. PDF 绘制：使用 `reportlab`（或 cairo）渲染背景图层和差异层，按页输出。
6. 报告注册：写入 `storage/jobs/<job_id>/reports/diff-overlay.pdf`，并在 job metadata 中登记；前端露出“查看 PDF 差异报告”。

### 详细任务拆分

#### 阶段 1：对齐与数据准备
1. **归一化改进**：增强 `_find_grid_axes`，如果识别轴网失败，则回退到基于主体包围盒的平移/缩放对齐。
2. **图层过滤策略**：
   - 定义默认保留图层（如 `WALL`, `AXIS`, `DIM`, `TEXT` 等），提供配置项；
   - 支持“强制包含差异实体”确保 diff 输出必然可见；
   - 可选：统计图层数量，生成调试日志供调优。
3. **实体标准化**：新增工具函数，将 DXF 的坐标单位换算成 PDF 坐标（例如 mm 或 inch），统一变换矩阵（translation + rotation + scaling）。
4. **色彩与风格表**：预设背景线条和差异高亮颜色，使用 RGBA 或透明度参数存储于配置。

#### 阶段 2：PDF 渲染引擎
1. **基础绘制**：实现 `render_pdf(job, entities)`：
   - 初始化 `reportlab.pdfgen.canvas.Canvas`；
   - 根据实体包围盒设置页面尺寸与坐标系（翻转 y 轴以符合图纸方向）；
   - 绘制背景层（原图浅灰）；
   - 绘制改图（浅蓝或其他颜色）；
   - 对于差异实体，使用绿色（新增）/红色（删除）填充或描边；
   - 文字/尺寸可用灰色，以免遮挡差异。
2. **分页策略**：可输出三页：
   - 页 1：原图（浅灰）；
   - 页 2：改图；
   - 页 3：叠加 + 差异高亮；
   或者单页叠加（根据需求配置）。
3. **性能优化**：
   - 批量绘制线段/多段线，提前缓存 Path 对象；
   - 对大量实体可进行抽稀（例如对很多短线段的图层降低渲染细粒度）。

#### 阶段 3：管线集成
1. 在后端任务 (`convert_job_task`) 完成 DXF 解析后，调用 `render_diff_pdf` 生成 PDF，写入 `reports`。
2. 补充 metadata 字段 `reports`: 包含 PDF 的路径、大小、生成时间。
3. 若渲染失败（如 ReportLab 缺失字体），记录日志并允许任务完成但标明 PDF 不可用。

#### 阶段 4：前端支持
1. `DiffViewer` / `FullScreenView` 增加“打开 PDF 差异报告”按钮，优先 iframe 内嵌，兼容下载。
2. 若 PDF 尚未生成，展示“暂未生成”提示并支持人工触发重算（可调用后台补算接口）。

#### 阶段 5：验证与调优
1. 使用 `originFile` 内 DWG 验证输出 PDF 的对齐与颜色，比如墙体重合度、差异高亮是否直观。
2. 收集 PDF 大小与生成时长；如果太大，考虑压缩、抽稀或分块渲染。
3. 编写单元测试/集成测试：
   - DXF 解析后实体数据结构完整；
   - PDF 文件成功生成且被记录在 job metadata 中；
   - 前端接口可访问生成的 PDF。

### 可选增强
- 对外提供 JSON 配置项：允许自定义图层颜色、透明度、是否显示文字等。
- 为 PDF 增加差异图例（在页脚列出颜色说明）。
- 如果需要交互，可额外生成 SVG 叠加层，但仍以 PDF 作为主报告。

---
