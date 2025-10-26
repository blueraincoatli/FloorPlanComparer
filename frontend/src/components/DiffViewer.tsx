import type { DiffPayload } from "../types/jobs";
import { DiffCanvas } from "./DiffCanvas";

type DiffViewerProps = {
  jobId: string | null;
  payload: DiffPayload | null;
  isLoading: boolean;
  error: string | null;
};

export function DiffViewer({ jobId, payload, isLoading, error }: DiffViewerProps) {
  const hasDiff = Boolean(payload);

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>差异可视化</h2>
        {jobId && <span className="muted">当前任务：{jobId}</span>}
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
    </section>
  );
}
