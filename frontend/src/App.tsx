import { useCallback, useEffect, useMemo, useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

type UploadHint = {
  title: string;
  description: string;
};

type ApiJobSummary = {
  job_id: string;
  status: string;
  progress: number;
  created_at: string;
  updated_at: string;
};

type JobSummary = {
  jobId: string;
  status: string;
  progress: number;
  createdAt: string;
  updatedAt: string;
};

const hints: UploadHint[] = [
  {
    title: "上传原始图纸",
    description: "选择事务所初稿 DWG，并通过 /jobs 接口提交。",
  },
  {
    title: "上传施工图",
    description: "选择施工图 DWG，系统会自动执行转换、解析与匹配。",
  },
  {
    title: "查看比对结果",
    description: "在审核界面浏览差异图层，并导出报告。",
  },
];

const statusText: Record<string, string> = {
  queued: "排队中",
  processing: "处理中",
  completed: "已完成",
  failed: "失败",
};

function formatTimestamp(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "-" : date.toLocaleString();
}

function formatProgress(progress: number) {
  return `${Math.round(progress * 100)}%`;
}

export default function App() {
  const [activeIndex, setActiveIndex] = useState(0);
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadJobs = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/jobs?limit=10&offset=0`);
      if (!response.ok) {
        throw new Error(`请求失败：${response.status}`);
      }

      const body = await response.json();
      const entries: ApiJobSummary[] = body?.data?.jobs ?? [];
      const mapped = entries.map<JobSummary>((item) => ({
        jobId: item.job_id,
        status: item.status,
        progress: item.progress,
        createdAt: item.created_at,
        updatedAt: item.updated_at,
      }));
      setJobs(mapped);
    } catch (err) {
      const message = err instanceof Error ? err.message : "无法获取任务列表";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadJobs();
  }, [loadJobs]);

  const hasJobs = useMemo(() => jobs.length > 0, [jobs]);

  return (
    <div className="layout">
      <header className="header">
        <h1>Floor Plan Comparer</h1>
        <p>平面图差异比对的端到端工具。</p>
      </header>

      <main className="content">
        <section className="panel">
          <h2>核心流程</h2>
          <ul>
            {hints.map((hint, index) => (
              <li key={hint.title}>
                <button
                  className={index === activeIndex ? "step active" : "step"}
                  type="button"
                  onClick={() => setActiveIndex(index)}
                >
                  <span className="step-index">{index + 1}</span>
                  <span>
                    <strong>{hint.title}</strong>
                    <br />
                    <small>{hint.description}</small>
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </section>

        <section className="panel">
          <div className="panel-header">
            <h2>任务概览</h2>
            <button className="ghost-button" type="button" onClick={() => void loadJobs()} disabled={isLoading}>
              {isLoading ? "刷新中..." : "刷新"}
            </button>
          </div>

          {error ? (
            <p className="error">{error}</p>
          ) : hasJobs ? (
            <div className="table-wrapper">
              <table className="table">
                <thead>
                  <tr>
                    <th>任务 ID</th>
                    <th>状态</th>
                    <th>进度</th>
                    <th>最近更新时间</th>
                  </tr>
                </thead>
                <tbody>
                  {jobs.map((job) => (
                    <tr key={job.jobId}>
                      <td>{job.jobId}</td>
                      <td>
                        <span className={`badge status-${job.status}`}>{statusText[job.status] ?? job.status}</span>
                      </td>
                      <td>{formatProgress(job.progress)}</td>
                      <td>{formatTimestamp(job.updatedAt)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="muted">暂无任务，快去上传第一组图纸吧！</p>
          )}
        </section>

        <section className="panel">
          <h2>下一步</h2>
          <p>
            当前页面为占位骨架。后续将接入上传控件、任务详情页和差异可视化组件，验证完整的端到端流程。
          </p>
          <p>
            若需自定义 API 地址，可在前端目录创建 <code>.env</code> 并设置 <code>VITE_API_BASE_URL</code>。
          </p>
        </section>
      </main>

      <footer className="footer">© {new Date().getFullYear()} Floor Plan Comparer</footer>
    </div>
  );
}
