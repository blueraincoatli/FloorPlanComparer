# 开发状态概览（2025-10-23）

## 后端
- ✅ Celery 异步任务队列已接入，`convert → extract → match` 任务链在同步/异步两种模式下均可运行。
- ✅ 新增 `/api/jobs` 列表接口，支持分页返回任务摘要；任务元数据读写使用文件锁与原子写入，避免并发冲突。
- ✅ 维护 `backend/Dockerfile` 与 `ops/compose/docker-compose.yml`，可一键启动 `api + worker + redis`。
- 🔜 抽象元数据存储层并迁移至 SQLite/PostgreSQL，增强查询能力与可靠性。

## 前端
- ✅ React + Vite + TypeScript 脚手架已搭建，并通过 `npm run build` 验证。
- ✅ 首页展示 Celery 任务概览，支持从 `VITE_API_BASE_URL` 读取 API 地址并刷新列表。
- 🔜 集成文件上传流程、任务详情视图及 Paper.js 差异可视化组件，完成端到端联调。

## 运维与环境
- ✅ 新增 `.dockerignore`、更新 `scripts/setup_env.(ps1|sh)`，统一使用 `uv sync` 管理依赖。
- ✅ docker-compose 可并行启动 Redis、API、Worker；后续将补充前端与监控服务（Flower/Prometheus）。
- 🔜 在 CI/CD 中构建与推送后端/前端镜像，增加自动化测试与部署脚本。

> 下一步建议：在真实环境中关闭 `task_always_eager` 并部署 Redis，完成数据库迁移设计，同时推进前端上传与任务详情功能的实现。 
