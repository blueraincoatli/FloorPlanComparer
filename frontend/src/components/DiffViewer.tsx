import type { DiffPayload, StoredFile } from "../types/jobs";
import { DiffCanvas } from "./DiffCanvas";

type DiffViewerProps = {
  jobId: string | null;
  payload: DiffPayload | null;
  isLoading: boolean;
  error: string | null;
  reports: StoredFile[];
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

export function DiffViewer({ jobId, payload, isLoading, error, reports }: DiffViewerProps) {
  const hasDiff = Boolean(payload);
  const pdfReport = reports.find((report) => report.kind === "pdf_overlay" || report.name.toLowerCase().endswith(".pdf"));

  const handleOpenFullscreen = () => {
    if (!jobId || !payload) {
      return;
    }

    if (typeof window === "undefined") {
      return;
    }

    try {
      sessionStorage.setItem(`diff:${jobId}`, JSON.stringify(payload));
    } catch (storageError) {
      console.warn("无法在 sessionStorage 中缓存差异数据", storageError);
    }

    const url = new URL("/fullscreen.html", window.location.origin);
    url.searchParams.set("job", jobId);
    window.open(url.toString(), "_blank", "noopener,noreferrer");
  };

  const handleDownloadOverlay = () => {
    if (!jobId || !payload) {
      return;
    }

    const blob = new Blob([JSON.stringify(payload)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${jobId}-diff.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  const handleOpenPdfReport = () => {
    if (!jobId || !pdfReport) {
      return;
    }
    const artefactKey = pdfReport.kind === "pdf_overlay" ? "pdf-overlay" : pdfReport.kind ?? pdfReport.name;
    const url = `${API_BASE_URL}/jobs/${jobId}/artefacts/${encodeURIComponent(artefactKey)}`;
    window.open(url, "_blank", "noopener,noreferrer");
  };

  return (
    <section className="panel">
      <div className="panel-header">
        <div className="panel-title">
          <h2>差异可视化</h2>
          {jobId && <span className="muted">当前任务：{jobId}</span>}
        </div>
        {jobId && hasDiff && (
          <div className="panel-header-actions">
            <button type="button" className="ghost-button" onClick={handleOpenFullscreen}>
              全屏查看
            </button>
            <button type="button" className="ghost-button" onClick={handleDownloadOverlay}>
              下载差异数据
            </button>
            <button
              type="button"
              className="ghost-button"
              onClick={handleOpenPdfReport}
              disabled={!pdfReport}
            >
              {pdfReport ? "打开 PDF 报告" : "PDF 报告生成中"}
            </button>
          </div>
        )}
      </div>

      {!jobId && <p className="muted">请选择任务以查看差异预览。</p>}
      {jobId && error && <p className="error">{error}</p>}
      {jobId && isLoading && <p className="muted">差异加载中...</p>}

      {jobId && hasDiff && payload && (
        <div className="diff-grid">
          <div className="diff-summary">
            <h3>统计概览</h3>
            <ul>
              <li>
                <span className="dot dot-added" /> 新增：{payload.summary.added}
              </li>
              <li>
                <span className="dot dot-removed" /> 删除：{payload.summary.removed}
              </li>
              <li>
                <span className="dot dot-modified" /> 修改：{payload.summary.modified}
              </li>
            </ul>
          </div>

          <DiffCanvas entities={payload.entities} />
        </div>
      )}

      {jobId && hasDiff && !pdfReport && !isLoading && (
        <p className="muted">PDF 差异报告正在生成或尚不可用。</p>
      )}
    </section>
  );
}
