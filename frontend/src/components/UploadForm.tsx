import type { FormEvent } from "react";
import { useCallback, useEffect, useRef, useState } from "react";

type UploadFormProps = {
  onSubmit: (files: { original: File; revised: File }) => Promise<void>;
  isUploading: boolean;
  error: string | null;
  success: string | null;
  onFeedbackClear: () => void;
};

export function UploadForm({ onSubmit, isUploading, error, success, onFeedbackClear }: UploadFormProps) {
  const [originalFile, setOriginalFile] = useState<File | null>(null);
  const [revisedFile, setRevisedFile] = useState<File | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);
  const originalInputRef = useRef<HTMLInputElement | null>(null);
  const revisedInputRef = useRef<HTMLInputElement | null>(null);

  const resetForm = useCallback(() => {
    setOriginalFile(null);
    setRevisedFile(null);
    setLocalError(null);
    onFeedbackClear();
    if (originalInputRef.current) {
      originalInputRef.current.value = "";
    }
    if (revisedInputRef.current) {
      revisedInputRef.current.value = "";
    }
  }, [onFeedbackClear]);

  const handleSubmit = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      setLocalError(null);

      if (!originalFile || !revisedFile) {
        setLocalError("请同时选择原始图纸和施工图纸文件。");
        return;
      }

      onFeedbackClear();
      await onSubmit({ original: originalFile, revised: revisedFile });
    },
    [originalFile, revisedFile, onSubmit, onFeedbackClear]
  );

  useEffect(() => {
    if (success) {
      setOriginalFile(null);
      setRevisedFile(null);
      if (originalInputRef.current) {
        originalInputRef.current.value = "";
      }
      if (revisedInputRef.current) {
        revisedInputRef.current.value = "";
      }
    }
  }, [success]);

  return (
    <section className="panel">
      <h2>上传图纸</h2>
      <p className="muted">支持 DWG 文件，上传后系统会自动执行转换与差异分析。</p>

      <form className="form" onSubmit={handleSubmit}>
        <div className="form-grid">
          <label className="form-field">
            <span>原始图纸</span>
            <input
              ref={originalInputRef}
              type="file"
              accept=".dwg"
              onChange={(event) => {
                setOriginalFile(event.target.files?.[0] ?? null);
                onFeedbackClear();
              }}
              required
            />
          </label>

          <label className="form-field">
            <span>施工图纸</span>
            <input
              ref={revisedInputRef}
              type="file"
              accept=".dwg"
              onChange={(event) => {
                setRevisedFile(event.target.files?.[0] ?? null);
                onFeedbackClear();
              }}
              required
            />
          </label>
        </div>

        <div className="form-actions">
          <button className="primary-button" type="submit" disabled={isUploading}>
            {isUploading ? "提交中..." : "提交比对任务"}
          </button>
          <button className="ghost-button" type="button" onClick={resetForm} disabled={isUploading}>
            重置
          </button>
        </div>
      </form>

      {localError && <p className="error">{localError}</p>}
      {error && <p className="error">{error}</p>}
      {success && <p className="success">{success}</p>}
    </section>
  );
}
