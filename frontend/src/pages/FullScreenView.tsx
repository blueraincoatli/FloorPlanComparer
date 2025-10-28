import { useEffect, useMemo, useState, type ChangeEvent } from "react";

import { DiffCanvas } from "../components/DiffCanvas";
import type { DiffPayload, StoredFile } from "../types/jobs";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

type DiffState = {
  loading: boolean;
  error: string | null;
  payload: DiffPayload | null;
};

export function FullScreenView() {
  const params = useMemo(() => new URLSearchParams(window.location.search), []);
  const jobId = params.get("job");
  const [scale, setScale] = useState(1.2);
  const [state, setState] = useState<DiffState>({ loading: true, error: null, payload: null });
  const [reports, setReports] = useState<StoredFile[]>([]);

  useEffect(() => {
    if (!jobId) {
      setState({ loading: false, error: "缺少 job 参数，无法加载差异数据。", payload: null });
      setReports([]);
      return;
    }

    const key = `diff:${jobId}`;
    const cached = sessionStorage.getItem(key);
    let cachedPayload: DiffPayload | null = null;
    if (cached) {
      try {
        cachedPayload = JSON.parse(cached) as DiffPayload;
      } catch (error) {
        console.warn("无法解析缓存的差异数据，将回退到网络请求。", error);
      }
    }

    if (cachedPayload) {
      setState({ loading: false, error: null, payload: cachedPayload });
    } else {
      setState({ loading: true, error: null, payload: null });
    }

    setReports([]);
    const controller = new AbortController();

    const loadDiff = async () => {
      if (cachedPayload) {
        return;
      }
      try {
        const response = await fetch(`${API_BASE_URL}/jobs/${jobId}/diff`, {
          signal: controller.signal,
        });
        if (!response.ok) {
          throw new Error(`请求失败：${response.status}`);
        }
        const body = await response.json();
        const payload = body?.data as DiffPayload;
        setState({ loading: false, error: null, payload });
        sessionStorage.setItem(key, JSON.stringify(payload));
      } catch (error) {
        if (controller.signal.aborted) {
          return;
        }
        const message = error instanceof Error ? error.message : "加载差异失败";
        setState({ loading: false, error: message, payload: null });
      }
    };

    const loadStatus = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`, {
          signal: controller.signal,
        });
        if (!response.ok) {
          throw new Error(`状态查询失败：${response.status}`);
        }
        const body = await response.json();
        const reportsData = (body?.data?.reports ?? []) as StoredFile[];
        setReports(reportsData);
      } catch (error) {
        if (controller.signal.aborted) {
          return;
        }
        setReports([]);
      }
    };

    void loadDiff();
    void loadStatus();

    return () => controller.abort();
  }, [jobId]);

  const summary = state.payload?.summary;
  const pdfReport = useMemo(
    () => reports.find((report) => report.kind === "pdf_overlay" || report.name.toLowerCase().endsWith(".pdf")),
    [reports]
  );

  const handleScaleChange = (event: ChangeEvent<HTMLInputElement>) => {
    setScale(Number(event.target.value));
  };

  const handleReset = () => setScale(1.0);

  const handleOpenPdf = () => {
    if (!jobId || !pdfReport) {
      return;
    }
    const artefactKey = pdfReport.kind === "pdf_overlay" ? "pdf-overlay" : pdfReport.kind ?? pdfReport.name;
    const url = `${API_BASE_URL}/jobs/${jobId}/artefacts/${encodeURIComponent(artefactKey)}`;
    window.open(url, "_blank", "noopener,noreferrer");
  };

  return (
    <div className="fullscreen-root">
      <header className="fullscreen-toolbar">
        <div>
          <h1>全屏差异视图</h1>
          <p>{jobId ? `当前任务：${jobId}` : "未选择任务"}</p>
        </div>
        <div className="fullscreen-controls">
          <button
            type="button"
            className="ghost-button"
            onClick={handleOpenPdf}
            disabled={!pdfReport}
          >
            {pdfReport ? "打开 PDF 报告" : "PDF 报告生成中"}
          </button>
          <div className="fullscreen-scale">
            <label htmlFor="scale">缩放</label>
            <input
              type="range"
              id="scale"
              min="0.6"
              max="2.5"
              step="0.1"
              value={scale}
              onChange={handleScaleChange}
            />
            <span>{scale.toFixed(1)}x</span>
            <button type="button" className="ghost-button" onClick={handleReset}>
              重置
            </button>
          </div>
          <button type="button" className="ghost-button" onClick={() => window.close()}>
            关闭
          </button>
        </div>
      </header>

      <main className="fullscreen-main">
        <aside className="fullscreen-summary">
          <h2>统计概览</h2>
          {summary ? (
            <ul>
              <li>
                <span className="dot dot-added" /> 新增：{summary.added}
              </li>
              <li>
                <span className="dot dot-removed" /> 删除：{summary.removed}
              </li>
              <li>
                <span className="dot dot-modified" /> 修改：{summary.modified}
              </li>
            </ul>
          ) : (
            <p className="muted">暂无统计信息。</p>
          )}
          {pdfReport ? (
            <div className="fullscreen-report">
              <p>PDF 报告：{pdfReport.name}</p>
              <p>文件大小：{Math.max(1, Math.round(pdfReport.size / 1024))} KB</p>
            </div>
          ) : (
            <p className="muted">PDF 报告尚未生成或不可用。</p>
          )}
          {state.error && <p className="error">{state.error}</p>}
          {state.loading && <p className="muted">差异加载中...</p>}
        </aside>

        <section className="fullscreen-canvas-area">
          <div className="fullscreen-canvas-scroll">
            {state.payload ? (
              <div className="fullscreen-canvas-inner" style={{ transform: `scale(${scale})` }}>
                <DiffCanvas entities={state.payload.entities} height={640} showLegend={false} />
                <ul className="fullscreen-legend">
                  {state.payload.entities.map((entity) => (
                    <li key={entity.entity_id}>
                      <span className={`dot dot-${entity.change_type}`} />
                      <strong>{entity.label ?? entity.entity_id}</strong>
                      <small>{entity.entity_type}</small>
                    </li>
                  ))}
                </ul>
              </div>
            ) : state.loading ? (
              <div className="fullscreen-empty">正在加载差异数据...</div>
            ) : (
              <div className="fullscreen-empty">未能加载差异数据。</div>
            )}
          </div>
        </section>
      </main>

      <footer className="fullscreen-footer">© {new Date().getFullYear()} Floor Plan Comparer</footer>
    </div>
  );
}
