import { useCallback, useEffect, useState } from "react";

import type { ApiJobSummary, DiffPayload, JobSummary, StoredFile } from "../types/jobs";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

type JobsHookState = {
  jobs: JobSummary[];
  isLoadingJobs: boolean;
  jobsError: string | null;
  selectedJobId: string | null;
  diffPayload: DiffPayload | null;
  isLoadingDiff: boolean;
  diffError: string | null;
  isUploading: boolean;
  uploadError: string | null;
  uploadSuccess: string | null;
  jobReports: StoredFile[];
};

type UploadParams = {
  original: File;
  revised: File;
};

export function useJobs() {
  const [state, setState] = useState<JobsHookState>({
    jobs: [],
    isLoadingJobs: false,
    jobsError: null,
    selectedJobId: null,
    diffPayload: null,
    isLoadingDiff: false,
    diffError: null,
    isUploading: false,
    uploadError: null,
    uploadSuccess: null,
    jobReports: [],
  });

  const refreshJobs = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoadingJobs: true, jobsError: null }));
    try {
      const response = await fetch(`${API_BASE_URL}/jobs?limit=10&offset=0`);
      if (!response.ok) {
        throw new Error(`请求失败：${response.status}`);
      }
      const body = await response.json();
      const entries: ApiJobSummary[] = body?.data?.jobs ?? [];
      const jobs: JobSummary[] = entries.map((item) => ({
        jobId: item.job_id,
        status: item.status,
        progress: item.progress,
        createdAt: item.created_at,
        updatedAt: item.updated_at,
      }));
      const jobIds = new Set(jobs.map((job) => job.jobId));
      setState((prev) => {
        const selectedJobId = prev.selectedJobId && jobIds.has(prev.selectedJobId) ? prev.selectedJobId : null;
        return {
          ...prev,
          jobs,
          isLoadingJobs: false,
          jobsError: null,
          selectedJobId,
          diffPayload: selectedJobId ? prev.diffPayload : null,
          diffError: selectedJobId ? prev.diffError : null,
          jobReports: selectedJobId ? prev.jobReports : [],
        };
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法获取任务列表";
      setState((prev) => ({ ...prev, jobsError: message, isLoadingJobs: false }));
    }
  }, []);

  const fetchDiff = useCallback(async (jobId: string) => {
    setState((prev) => ({ ...prev, isLoadingDiff: true, diffError: null, jobReports: [] }));
    try {
      const [diffResponse, statusResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/jobs/${jobId}/diff`),
        fetch(`${API_BASE_URL}/jobs/${jobId}`),
      ]);

      if (!diffResponse.ok) {
        throw new Error(`无法获取差异：${diffResponse.status}`);
      }

      const diffBody = await diffResponse.json();
      let reports: StoredFile[] = [];
      if (statusResponse.ok) {
        const statusBody = await statusResponse.json();
        reports = statusBody?.data?.reports ?? [];
      }

      setState((prev) => ({
        ...prev,
        diffPayload: diffBody?.data ?? null,
        isLoadingDiff: false,
        jobReports: reports,
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "加载差异时发生错误";
      setState((prev) => ({
        ...prev,
        diffPayload: null,
        diffError: message,
        isLoadingDiff: false,
        jobReports: [],
      }));
    }
  }, []);

  const selectJob = useCallback(
    (jobId: string) => {
      setState((prev) => ({ ...prev, selectedJobId: jobId }));
      void fetchDiff(jobId);
    },
    [fetchDiff]
  );

  const uploadFiles = useCallback(
    async ({ original, revised }: UploadParams) => {
      setState((prev) => ({
        ...prev,
        isUploading: true,
        uploadError: null,
        uploadSuccess: null,
      }));

      try {
        const formData = new FormData();
        formData.append("original_dwg", original, original.name);
        formData.append("revised_dwg", revised, revised.name);

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
        const jobId: string | null = payload?.data?.job_id ?? null;
        const successMessage = jobId ? `任务已创建（ID: ${jobId}）。` : "任务已创建。";
        setState((prev) => ({
          ...prev,
          isUploading: false,
          uploadSuccess: successMessage,
        }));

        await refreshJobs();
        if (jobId) {
          selectJob(jobId);
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : "上传时发生未知错误";
        setState((prev) => ({
          ...prev,
          isUploading: false,
          uploadError: message,
        }));
      }
    },
    [refreshJobs, selectJob]
  );

  const clearUploadFeedback = useCallback(() => {
    setState((prev) => ({ ...prev, uploadError: null, uploadSuccess: null }));
  }, []);

  useEffect(() => {
    void refreshJobs();
  }, [refreshJobs]);

  return {
    jobs: state.jobs,
    isLoadingJobs: state.isLoadingJobs,
    jobsError: state.jobsError,
    selectedJobId: state.selectedJobId,
    diffPayload: state.diffPayload,
    isLoadingDiff: state.isLoadingDiff,
    diffError: state.diffError,
    isUploading: state.isUploading,
    uploadError: state.uploadError,
    uploadSuccess: state.uploadSuccess,
    jobReports: state.jobReports,
    refreshJobs,
    selectJob,
    uploadFiles,
    clearUploadFeedback,
  };
}
