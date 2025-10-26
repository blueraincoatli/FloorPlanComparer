import type { JobSummary } from "../types/jobs";
import { formatProgress, formatTimestamp } from "../utils/format";

type JobsTableProps = {
  jobs: JobSummary[];
  isLoading: boolean;
  error: string | null;
  selectedJobId: string | null;
  onRefresh: () => void;
  onSelect: (jobId: string) => void;
};

export function JobsTable({ jobs, isLoading, error, selectedJobId, onRefresh, onSelect }: JobsTableProps) {
  const hasJobs = jobs.length > 0;

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>任务概览</h2>
        <button className="ghost-button" type="button" onClick={onRefresh} disabled={isLoading}>
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
                  onClick={() => onSelect(job.jobId)}
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
  );
}

const statusText: Record<string, string> = {
  queued: "排队中",
  processing: "处理中",
  completed: "已完成",
  failed: "失败",
};
