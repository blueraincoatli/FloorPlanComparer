import { useState } from "react";

import { DiffViewer } from "./components/DiffViewer";
import { JobsTable } from "./components/JobsTable";
import { ProcessSteps } from "./components/ProcessSteps";
import { UploadForm } from "./components/UploadForm";
import EnhancedUploadForm from "./components/EnhancedUploadForm";
import DWGConverter from "./components/DWGConverter";
import ModernDWGConverter from "./components/ModernDWGConverter";
import MaterialLayout from "./components/MaterialLayout";
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
  const [mode, setMode] = useState<'standard' | 'enhanced' | 'converter'>('standard');
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
    <MaterialLayout
      selectedMode={mode}
      onModeChange={(newMode) => setMode(newMode)}
    >
      {mode === 'converter' ? (
        <ModernDWGConverter onJobCreated={handleJobCreated} />
      ) : mode === 'enhanced' ? (
        <div>
          <Alert
            message="增强比对模式"
            description="此模式使用 AutoCAD 进行高级 DWG 文件比对，提供更精确的差异化分析。"
            type="info"
            showIcon
            style={{ marginBottom: 24 }}
          />
          <EnhancedUploadForm onJobCreated={handleJobCreated} />
        </div>
      ) : (
        <div>
          <Alert
            message="标准比对模式"
            description="传统的 DWG 文件差异比对功能，适用于基本的图纸比较需求。"
            type="info"
            showIcon
            style={{ marginBottom: 24 }}
          />
          <UploadForm
            onSubmit={uploadFiles}
            isUploading={isUploading}
            error={uploadError}
            success={uploadSuccess}
            onFeedbackClear={clearUploadFeedback}
          />
        </div>
      )}

      {/* 任务列表 */}
      <Card title="任务历史" style={{ marginTop: 24 }}>
        <JobsTable
          jobs={jobs}
          isLoading={isLoadingJobs}
          error={jobsError}
          selectedJobId={selectedJobId}
          onRefresh={() => void refreshJobs()}
          onSelect={selectJob}
        />
      </Card>

      {/* 差异查看器 */}
      {selectedJobId && (
        <Card title="差异分析结果" style={{ marginTop: 24 }}>
          <DiffViewer
            jobId={selectedJobId}
            payload={diffPayload}
            isLoading={isLoadingDiff}
            error={diffError}
            reports={jobReports}
          />
        </Card>
      )}
    </MaterialLayout>
  );
}