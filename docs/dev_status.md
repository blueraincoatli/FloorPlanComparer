# 开发状态跟进（2025-10-26）

下表针对上一轮 review 的跟进项在 2025-10-26 再次复查，标记当前代码已经修复的内容以及仍需处理的差距。

## 后端

- [x] Celery 流程依赖与几何工具：`backend/pyproject.toml:15-34` 新增 `cad` 可选依赖组，`app/services/parsing.py` 在检测到 `ezdxf/numpy/shapely/rtree` 不可用时降级为可预测的 stub，同时 `app/services/__init__.py:1-11` 输出 `normalize_entities_by_grid`，`app/tasks/jobs.py` 也引入了网格归一化步骤，流水线已可在无 CAD 组件时运行。
- [x] `/api/jobs` 状态流：`app/api/routes/jobs.py:24-123` 与 `app/services/jobs.py:37-115` 协同，创建任务时写入日志，Celery 任务在 `convert/extract/match` 阶段更新 `status/progress/logs`，查询接口可以返回实时状态，不再卡在 `processing`。
- [x] ODA 转换器路径与沙盒策略：`app/core/settings.py:6-36` 暴露 `converter_path`，`app/tasks/jobs.py:31-78` 通过 `_converter_path()` 读取配置并在缺省时走 `_stub_convert`，不再硬编码 Windows 路径，也具备“无转换器”占位行为。
- [x] 元数据持久化：`app/services/jobs.py` 现使用 `storage/meta/jobs.db`（SQLite）持久化 `JobMetadata`，提供自动迁移遗留 JSON、原子更新与分页查询能力，`JobService` API 保持不变。

## 前端

- [x] React + Vite 骨架：`frontend/package.json` + `frontend/vite.config.ts` 与 `frontend/src/App.tsx` 已实现“上传 → 列表 → Diff 预览”闭环，能直接对接现有 API。
- [x] 组件拆分与状态管理：`frontend/src/components/*` + `frontend/src/hooks/useJobs.ts` 拆分出 Upload/List/Diff 子模块并集中处理状态（列表刷新、任务切换、上传反馈），`App.tsx` 精简为布局与 orchestration。
- [x] 仓库洁净度：移除 `frontend/src/App.js`/`frontend/src/main.js`，`.gitignore` 新增 `frontend/node_modules/` 与 `frontend/dist/`，并在构建后清理产物，工作区保持整洁。

## 运维

- [x] docker-compose（`ops/compose/docker-compose.yml`）现包含可热更新的 `frontend` 服务（Node 运行 `vite` dev server）、共享 `frontend/` 代码卷以及默认的 `VITE_API_BASE_URL`，同时为 `api/worker` 注入 `FLOORPLAN_CONVERTER_PATH` 并挂载 `originFile` 目录，便于配置 ODA 转换器。
- [x] `scripts/convert.py` + `scripts/convert.bat` 统一读取 `FLOORPLAN_CONVERTER_PATH` 与输入/输出目录，支持跨平台调用及参数化（版本、格式、递归、审计），Windows wrapper 仅负责调用 Python 实现。

## 建议的后续优先级

1. 设计并实现元数据的数据库落地（可先 SQLite，后续 PostgreSQL），并补充迁移脚本。
2. 调整前端结构：拆分 Upload/List/Diff 组件，引入轻量状态容器（例如 Zustand）或自定义 hook，降低 `App.tsx` 复杂度。
3. 建立仓库忽略规则并删除编译产物：`.gitignore` 中添加 `frontend/node_modules/`、`frontend/dist/`，同时移除 `src/App.js`/`src/main.js`。
4. 完善 docker-compose：为前端提供构建/静态服务容器，给 ODA 转换器留出可配置挂载与资源限制。
5. 重写 `scripts/convert`（或新增跨平台脚本），统一读取 `FLOORPLAN_CONVERTER_PATH`，避免再次出现硬编码路径。
