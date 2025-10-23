# Floor Plan Comparer Frontend

基于 React、Vite 与 TypeScript 的前端工程，用于实现平面图差异比对的上传、任务管理与可视化界面。

## 快速开始

```bash
cd frontend
npm install
npm run dev
```

开发服务器默认运行在 <http://localhost:5173>，可在 `vite.config.ts` 中调整端口。

> 如果后端地址不是默认的 `http://localhost:8000/api`，请在前端根目录创建 `.env` 文件并设置
> `VITE_API_BASE_URL=http://your-api-host/api`。

## 常用脚本

- `npm run dev`：启动 Vite 开发服务器
- `npm run build`：执行生产环境构建
- `npm run preview`：本地预览构建产物

## 目录结构

```
frontend/
├── index.html
├── package.json
├── src/
│   ├── App.tsx
│   ├── main.tsx
│   └── styles.css
├── tsconfig.json
├── tsconfig.node.json
└── vite.config.ts
```

当前 `App.tsx` 包含任务概览示例，将后续扩展为上传向导、任务详情、矢量差异查看等模块。建议在 `src/` 下按领域划分组件与页面，例如 `pages/UploadPage`、`components/DiffViewer`。

## 与后端联调

- 默认从 `VITE_API_BASE_URL` 读取后端地址（默认值为 `http://localhost:8000/api`）。
- 上传表单会向 `/jobs` POST 提交 `original_dwg` 与 `revised_dwg` 两个文件。
- 任务概览通过 `/jobs` GET 获取最近任务列表，便于验证 Celery 异步处理结果。
