import { useState } from "react";

import { DiffViewer } from "./components/DiffViewer";
import { JobsTable } from "./components/JobsTable";
import { ProcessSteps } from "./components/ProcessSteps";
import { UploadForm } from "./components/UploadForm";
import { EnhancedUploadForm } from "./components/EnhancedUploadForm";
import { useJobs } from "./hooks/useJobs";
import type { UploadHint } from "./types/jobs";

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

export default function App() {
  const [activeIndex, setActiveIndex] = useState(0);
  const [enhancedMode, setEnhancedMode] = useState(false);
  const {
    jobs,
    isLoadingJobs,
    jobsError,
    selectedJobId,
    diffPayload,
    isLoadingDiff,
    diffError,
    isUploading,
    uploadError,
    uploadSuccess,
    refreshJobs,
    selectJob,
    uploadFiles,
    clearUploadFeedback,
    jobReports,
  } = useJobs();

  const handleJobCreated = (jobId: string) => {
    // Refresh jobs to show the new job
    refreshJobs();
    // Select the new job
    selectJob(jobId);
  };

  return (
    <div className="layout">
      <header className="header">
        <h1>Floor Plan Comparer</h1>
        <p>平面图差异比对的端到端工具。</p>
        <div style={{ marginTop: '10px' }}>
          <button 
            onClick={() => setEnhancedMode(!enhancedMode)}
            style={{ 
              padding: '5px 10px', 
              backgroundColor: enhancedMode ? '#1890ff' : '#f0f0f0',
              color: enhancedMode ? 'white' : 'black',
              border: '1px solid #d9d9d9',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            {enhancedMode ? '切换到标准模式' : '切换到增强模式'}
          </button>
        </div>
      </header>

      <main className="content">
        {enhancedMode ? (
          <EnhancedUploadForm onJobCreated={handleJobCreated} />
        ) : (
          <UploadForm
            onSubmit={uploadFiles}
            isUploading={isUploading}
            error={uploadError}
            success={uploadSuccess}
            onFeedbackClear={clearUploadFeedback}
          />
        )}

        <ProcessSteps hints={hints} activeIndex={activeIndex} onSelect={(index) => setActiveIndex(index)} />

        <JobsTable
          jobs={jobs}
          isLoading={isLoadingJobs}
          error={jobsError}
          selectedJobId={selectedJobId}
          onRefresh={() => void refreshJobs()}
          onSelect={selectJob}
        />

        <DiffViewer
          jobId={selectedJobId}
          payload={diffPayload}
          isLoading={isLoadingDiff}
          error={diffError}
          reports={jobReports}
        />

        <section className="panel">
          <h2>下一步</h2>
          <p>继续完善任务详情页、批量导出与权限控制，以支撑真实场景。</p>
          <p>
            若需自定义 API 地址，可在前端目录创建 <code>.env</code> 并设置 <code>VITE_API_BASE_URL</code>。
          </p>
        </section>
      </main>

      <footer className="footer">© {new Date().getFullYear()} Floor Plan Comparer</footer>
    </div>
  );
}