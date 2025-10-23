import type { FormEvent } from "react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

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

type DiffPolygon = {
  points: [number, number][];
};

type DiffEntity = {
  entity_id: string;
  entity_type: string;
  change_type: "added" | "removed" | "modified";
  label?: string | null;
  polygon: DiffPolygon;
};

type DiffSummary = {
  added: number;
  removed: number;
  modified: number;
};

type DiffPayload = {
  job_id: string;
  summary: DiffSummary;
  entities: DiffEntity[];
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
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const originalInputRef = useRef<HTMLInputElement | null>(null);
  const revisedInputRef = useRef<HTMLInputElement | null>(null);
  const [originalFile, setOriginalFile] = useState<File | null>(null);
  const [revisedFile, setRevisedFile] = useState<File | null>(null);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [diffPayload, setDiffPayload] = useState<DiffPayload | null>(null);
  const [isLoadingDiff, setIsLoadingDiff] = useState(false);
  const [diffError, setDiffError] = useState<string | null>(null);

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

  const loadDiff = useCallback(async (jobId: string) => {
    setDiffError(null);
    setIsLoadingDiff(true);
    try {
      const response = await fetch(`${API_BASE_URL}/jobs/${jobId}/diff`);
      if (!response.ok) {
        throw new Error(`无法获取差异：${response.status}`);
      }
      const body = await response.json();
      setDiffPayload(body?.data ?? null);
    } catch (err) {
      const message = err instanceof Error ? err.message : "加载差异时发生错误";
      setDiffPayload(null);
      setDiffError(message);
    } finally {
      setIsLoadingDiff(false);
    }
  }, []);

  useEffect(() => {
    void loadJobs();
  }, [loadJobs]);

  const hasJobs = useMemo(() => jobs.length > 0, [jobs]);
  const hasDiff = diffPayload !== null;

  const handleUpload = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      setUploadError(null);
      setUploadSuccess(null);

      if (!originalFile || !revisedFile) {
        setUploadError("请同时选择原始图纸和施工图纸文件。");
        return;
      }

      const formData = new FormData();
      formData.append("original_dwg", originalFile, originalFile.name);
      formData.append("revised_dwg", revisedFile, revisedFile.name);

      setIsUploading(true);
      try {
        const response = await fetch(`${API_BASE_URL}/jobs`, {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          const payload = await response.json().catch(() => ({}));
          const detail = payload?.detail ?? `${response.status}`;
          throw new Error(`上传失败：${detail}`);
        }

        const payload = await response.json();
        const jobId: string | undefined = payload?.data?.job_id;
        setUploadSuccess(jobId ? `任务已创建（ID: ${jobId}）。` : "任务已创建。");
        setOriginalFile(null);
        setRevisedFile(null);
        if (originalInputRef.current) {
          originalInputRef.current.value = "";
        }
        if (revisedInputRef.current) {
          revisedInputRef.current.value = "";
        }
        await loadJobs();
        setSelectedJobId(jobId ?? null);
        if (jobId) {
          void loadDiff(jobId);
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : "上传时发生未知错误";
        setUploadError(message);
      } finally {
        setIsUploading(false);
      }
    },
    [originalFile, revisedFile, loadJobs, loadDiff]
  );

  return (
    <div className="layout">
      <header className="header">
        <h1>Floor Plan Comparer</h1>
        <p>平面图差异比对的端到端工具。</p>
      </header>

      <main className="content">
        <section className="panel">
          <h2>上传图纸</h2>
          <p className="muted">支持 DWG 文件，上传后系统会自动执行转换与差异分析。</p>

          <form className="form" onSubmit={handleUpload}>
            <div className="form-grid">
              <label className="form-field">
                <span>原始图纸</span>
                <input
                  ref={originalInputRef}
                  type="file"
                  accept=".dwg"
                  onChange={(event) => setOriginalFile(event.target.files?.[0] ?? null)}
                  required
                />
              </label>

              <label className="form-field">
                <span>施工图纸</span>
                <input
                  ref={revisedInputRef}
                  type="file"
                  accept=".dwg"
                  onChange={(event) => setRevisedFile(event.target.files?.[0] ?? null)}
                  required
                />
              </label>
            </div>

            <div className="form-actions">
              <button className="primary-button" type="submit" disabled={isUploading}>
                {isUploading ? "提交中..." : "提交比对任务"}
              </button>
              <button
                className="ghost-button"
                type="button"
                onClick={() => {
                  setOriginalFile(null);
                  setRevisedFile(null);
                  setUploadError(null);
                  setUploadSuccess(null);
                  if (originalInputRef.current) {
                    originalInputRef.current.value = "";
                  }
                  if (revisedInputRef.current) {
                    revisedInputRef.current.value = "";
                  }
                }}
                disabled={isUploading}
              >
                重置
              </button>
            </div>
          </form>

          {uploadError && <p className="error">{uploadError}</p>}
          {uploadSuccess && <p className="success">{uploadSuccess}</p>}
        </section>

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
                    <tr
                      key={job.jobId}
                      className={job.jobId === selectedJobId ? "selected" : undefined}
                      onClick={() => {
                        setSelectedJobId(job.jobId);
                        void loadDiff(job.jobId);
                      }}
                    >
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
          <div className="panel-header">
            <h2>差异可视化</h2>
            {selectedJobId && (
              <span className="muted">当前任务：{selectedJobId}</span>
            )}
          </div>

          {!selectedJobId && <p className="muted">请选择任务以查看差异预览。</p>}
          {selectedJobId && diffError && <p className="error">{diffError}</p>}
          {selectedJobId && isLoadingDiff && <p className="muted">差异加载中...</p>}

          {selectedJobId && hasDiff && diffPayload && (
            <div className="diff-grid">
              <div className="diff-summary">
                <h3>统计概览</h3>
                <ul>
                  <li>
                    <span className="dot dot-added" /> 新增：{diffPayload.summary.added}
                  </li>
                  <li>
                    <span className="dot dot-removed" /> 删除：{diffPayload.summary.removed}
                  </li>
                  <li>
                    <span className="dot dot-modified" /> 修改：{diffPayload.summary.modified}
                  </li>
                </ul>
              </div>

              <DiffCanvas entities={diffPayload.entities} />
            </div>
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

type DiffCanvasProps = {
  entities: DiffEntity[];
};

function DiffCanvas({ entities }: DiffCanvasProps) {
  const allPoints = entities.flatMap((entity) => entity.polygon.points);
  const xs = allPoints.map(([x]) => x);
  const ys = allPoints.map(([, y]) => y);
  const minX = Math.min(...xs, 0);
  const maxX = Math.max(...xs, 100);
  const minY = Math.min(...ys, 0);
  const maxY = Math.max(...ys, 100);
  const padding = 10;
  const width = maxX - minX || 100;
  const height = maxY - minY || 100;

  const viewBox = `${minX - padding} ${minY - padding} ${width + padding * 2} ${height + padding * 2}`;

  return (
    <div className="diff-canvas">
      <svg viewBox={viewBox} role="img" aria-label="Diff preview">
        <defs>
          <pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
            <path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(226, 232, 240, 0.15)" strokeWidth="0.5" />
          </pattern>
        </defs>
        <rect
          x={minX - padding}
          y={minY - padding}
          width={width + padding * 2}
          height={height + padding * 2}
          fill="url(#grid)"
        />
        {entities.map((entity) => (
          <polygon
            key={entity.entity_id}
            points={entity.polygon.points.map((point) => point.join(",")).join(" ")}
            className={`diff-shape diff-${entity.change_type}`}
          >
            <title>{entity.label ?? entity.entity_id}</title>
          </polygon>
        ))}
      </svg>
      <ul className="diff-legend">
        {entities.map((entity) => (
          <li key={entity.entity_id}>
            <span className={`dot dot-${entity.change_type}`} />
            <strong>{entity.label ?? entity.entity_id}</strong>
            <small>{entity.entity_type}</small>
          </li>
        ))}
      </ul>
    </div>
  );
}
