export type UploadHint = {
  title: string;
  description: string;
};

export type ApiJobSummary = {
  job_id: string;
  status: string;
  progress: number;
  created_at: string;
  updated_at: string;
};

export type JobSummary = {
  jobId: string;
  status: string;
  progress: number;
  createdAt: string;
  updatedAt: string;
};

export type DiffPolygon = {
  points: [number, number][];
};

export type DiffEntity = {
  entity_id: string;
  entity_type: string;
  change_type: "added" | "removed" | "modified";
  label?: string | null;
  polygon: DiffPolygon;
};

export type StoredFile = {
  name: string;
  path: string;
  size: number;
  checksum: string;
  content_type?: string | null;
  kind?: string | null;
};

export type JobStatusData = {
  job_id: string;
  status: string;
  progress: number;
  reports: StoredFile[];
};

export type DiffSummary = {
  added: number;
  removed: number;
  modified: number;
};

export type DiffPayload = {
  job_id: string;
  summary: DiffSummary;
  entities: DiffEntity[];
};
