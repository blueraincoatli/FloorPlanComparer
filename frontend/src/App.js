import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";
const hints = [
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
const statusText = {
    queued: "排队中",
    processing: "处理中",
    completed: "已完成",
    failed: "失败",
};
function formatTimestamp(value) {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? "-" : date.toLocaleString();
}
function formatProgress(progress) {
    return `${Math.round(progress * 100)}%`;
}
export default function App() {
    const [activeIndex, setActiveIndex] = useState(0);
    const [jobs, setJobs] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadError, setUploadError] = useState(null);
    const [uploadSuccess, setUploadSuccess] = useState(null);
    const originalInputRef = useRef(null);
    const revisedInputRef = useRef(null);
    const [originalFile, setOriginalFile] = useState(null);
    const [revisedFile, setRevisedFile] = useState(null);
    const [selectedJobId, setSelectedJobId] = useState(null);
    const [diffPayload, setDiffPayload] = useState(null);
    const [isLoadingDiff, setIsLoadingDiff] = useState(false);
    const [diffError, setDiffError] = useState(null);
    const loadJobs = useCallback(async () => {
        setIsLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE_URL}/jobs?limit=10&offset=0`);
            if (!response.ok) {
                throw new Error(`请求失败：${response.status}`);
            }
            const body = await response.json();
            const entries = body?.data?.jobs ?? [];
            const mapped = entries.map((item) => ({
                jobId: item.job_id,
                status: item.status,
                progress: item.progress,
                createdAt: item.created_at,
                updatedAt: item.updated_at,
            }));
            setJobs(mapped);
        }
        catch (err) {
            const message = err instanceof Error ? err.message : "无法获取任务列表";
            setError(message);
        }
        finally {
            setIsLoading(false);
        }
    }, []);
    const loadDiff = useCallback(async (jobId) => {
        setDiffError(null);
        setIsLoadingDiff(true);
        try {
            const response = await fetch(`${API_BASE_URL}/jobs/${jobId}/diff`);
            if (!response.ok) {
                throw new Error(`无法获取差异：${response.status}`);
            }
            const body = await response.json();
            setDiffPayload(body?.data ?? null);
        }
        catch (err) {
            const message = err instanceof Error ? err.message : "加载差异时发生错误";
            setDiffPayload(null);
            setDiffError(message);
        }
        finally {
            setIsLoadingDiff(false);
        }
    }, []);
    useEffect(() => {
        void loadJobs();
    }, [loadJobs]);
    const hasJobs = useMemo(() => jobs.length > 0, [jobs]);
    const hasDiff = diffPayload !== null;
    const handleUpload = useCallback(async (event) => {
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
            const jobId = payload?.data?.job_id;
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
        }
        catch (err) {
            const message = err instanceof Error ? err.message : "上传时发生未知错误";
            setUploadError(message);
        }
        finally {
            setIsUploading(false);
        }
    }, [originalFile, revisedFile, loadJobs, loadDiff]);
    return (_jsxs("div", { className: "layout", children: [_jsxs("header", { className: "header", children: [_jsx("h1", { children: "Floor Plan Comparer" }), _jsx("p", { children: "\u5E73\u9762\u56FE\u5DEE\u5F02\u6BD4\u5BF9\u7684\u7AEF\u5230\u7AEF\u5DE5\u5177\u3002" })] }), _jsxs("main", { className: "content", children: [_jsxs("section", { className: "panel", children: [_jsx("h2", { children: "\u4E0A\u4F20\u56FE\u7EB8" }), _jsx("p", { className: "muted", children: "\u652F\u6301 DWG \u6587\u4EF6\uFF0C\u4E0A\u4F20\u540E\u7CFB\u7EDF\u4F1A\u81EA\u52A8\u6267\u884C\u8F6C\u6362\u4E0E\u5DEE\u5F02\u5206\u6790\u3002" }), _jsxs("form", { className: "form", onSubmit: handleUpload, children: [_jsxs("div", { className: "form-grid", children: [_jsxs("label", { className: "form-field", children: [_jsx("span", { children: "\u539F\u59CB\u56FE\u7EB8" }), _jsx("input", { ref: originalInputRef, type: "file", accept: ".dwg", onChange: (event) => setOriginalFile(event.target.files?.[0] ?? null), required: true })] }), _jsxs("label", { className: "form-field", children: [_jsx("span", { children: "\u65BD\u5DE5\u56FE\u7EB8" }), _jsx("input", { ref: revisedInputRef, type: "file", accept: ".dwg", onChange: (event) => setRevisedFile(event.target.files?.[0] ?? null), required: true })] })] }), _jsxs("div", { className: "form-actions", children: [_jsx("button", { className: "primary-button", type: "submit", disabled: isUploading, children: isUploading ? "提交中..." : "提交比对任务" }), _jsx("button", { className: "ghost-button", type: "button", onClick: () => {
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
                                                }, disabled: isUploading, children: "\u91CD\u7F6E" })] })] }), uploadError && _jsx("p", { className: "error", children: uploadError }), uploadSuccess && _jsx("p", { className: "success", children: uploadSuccess })] }), _jsxs("section", { className: "panel", children: [_jsx("h2", { children: "\u6838\u5FC3\u6D41\u7A0B" }), _jsx("ul", { children: hints.map((hint, index) => (_jsx("li", { children: _jsxs("button", { className: index === activeIndex ? "step active" : "step", type: "button", onClick: () => setActiveIndex(index), children: [_jsx("span", { className: "step-index", children: index + 1 }), _jsxs("span", { children: [_jsx("strong", { children: hint.title }), _jsx("br", {}), _jsx("small", { children: hint.description })] })] }) }, hint.title))) })] }), _jsxs("section", { className: "panel", children: [_jsxs("div", { className: "panel-header", children: [_jsx("h2", { children: "\u4EFB\u52A1\u6982\u89C8" }), _jsx("button", { className: "ghost-button", type: "button", onClick: () => void loadJobs(), disabled: isLoading, children: isLoading ? "刷新中..." : "刷新" })] }), error ? (_jsx("p", { className: "error", children: error })) : hasJobs ? (_jsx("div", { className: "table-wrapper", children: _jsxs("table", { className: "table", children: [_jsx("thead", { children: _jsxs("tr", { children: [_jsx("th", { children: "\u4EFB\u52A1 ID" }), _jsx("th", { children: "\u72B6\u6001" }), _jsx("th", { children: "\u8FDB\u5EA6" }), _jsx("th", { children: "\u6700\u8FD1\u66F4\u65B0\u65F6\u95F4" })] }) }), _jsx("tbody", { children: jobs.map((job) => (_jsxs("tr", { className: job.jobId === selectedJobId ? "selected" : undefined, onClick: () => {
                                                    setSelectedJobId(job.jobId);
                                                    void loadDiff(job.jobId);
                                                }, children: [_jsx("td", { children: job.jobId }), _jsx("td", { children: _jsx("span", { className: `badge status-${job.status}`, children: statusText[job.status] ?? job.status }) }), _jsx("td", { children: formatProgress(job.progress) }), _jsx("td", { children: formatTimestamp(job.updatedAt) })] }, job.jobId))) })] }) })) : (_jsx("p", { className: "muted", children: "\u6682\u65E0\u4EFB\u52A1\uFF0C\u5FEB\u53BB\u4E0A\u4F20\u7B2C\u4E00\u7EC4\u56FE\u7EB8\u5427\uFF01" }))] }), _jsxs("section", { className: "panel", children: [_jsxs("div", { className: "panel-header", children: [_jsx("h2", { children: "\u5DEE\u5F02\u53EF\u89C6\u5316" }), selectedJobId && (_jsxs("span", { className: "muted", children: ["\u5F53\u524D\u4EFB\u52A1\uFF1A", selectedJobId] }))] }), !selectedJobId && _jsx("p", { className: "muted", children: "\u8BF7\u9009\u62E9\u4EFB\u52A1\u4EE5\u67E5\u770B\u5DEE\u5F02\u9884\u89C8\u3002" }), selectedJobId && diffError && _jsx("p", { className: "error", children: diffError }), selectedJobId && isLoadingDiff && _jsx("p", { className: "muted", children: "\u5DEE\u5F02\u52A0\u8F7D\u4E2D..." }), selectedJobId && hasDiff && diffPayload && (_jsxs("div", { className: "diff-grid", children: [_jsxs("div", { className: "diff-summary", children: [_jsx("h3", { children: "\u7EDF\u8BA1\u6982\u89C8" }), _jsxs("ul", { children: [_jsxs("li", { children: [_jsx("span", { className: "dot dot-added" }), " \u65B0\u589E\uFF1A", diffPayload.summary.added] }), _jsxs("li", { children: [_jsx("span", { className: "dot dot-removed" }), " \u5220\u9664\uFF1A", diffPayload.summary.removed] }), _jsxs("li", { children: [_jsx("span", { className: "dot dot-modified" }), " \u4FEE\u6539\uFF1A", diffPayload.summary.modified] })] })] }), _jsx(DiffCanvas, { entities: diffPayload.entities })] }))] }), _jsxs("section", { className: "panel", children: [_jsx("h2", { children: "\u4E0B\u4E00\u6B65" }), _jsx("p", { children: "\u5F53\u524D\u9875\u9762\u4E3A\u5360\u4F4D\u9AA8\u67B6\u3002\u540E\u7EED\u5C06\u63A5\u5165\u4E0A\u4F20\u63A7\u4EF6\u3001\u4EFB\u52A1\u8BE6\u60C5\u9875\u548C\u5DEE\u5F02\u53EF\u89C6\u5316\u7EC4\u4EF6\uFF0C\u9A8C\u8BC1\u5B8C\u6574\u7684\u7AEF\u5230\u7AEF\u6D41\u7A0B\u3002" }), _jsxs("p", { children: ["\u82E5\u9700\u81EA\u5B9A\u4E49 API \u5730\u5740\uFF0C\u53EF\u5728\u524D\u7AEF\u76EE\u5F55\u521B\u5EFA ", _jsx("code", { children: ".env" }), " \u5E76\u8BBE\u7F6E ", _jsx("code", { children: "VITE_API_BASE_URL" }), "\u3002"] })] })] }), _jsxs("footer", { className: "footer", children: ["\u00A9 ", new Date().getFullYear(), " Floor Plan Comparer"] })] }));
}
function DiffCanvas({ entities }) {
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
    return (_jsxs("div", { className: "diff-canvas", children: [_jsxs("svg", { viewBox: viewBox, role: "img", "aria-label": "Diff preview", children: [_jsx("defs", { children: _jsx("pattern", { id: "grid", width: "10", height: "10", patternUnits: "userSpaceOnUse", children: _jsx("path", { d: "M 10 0 L 0 0 0 10", fill: "none", stroke: "rgba(226, 232, 240, 0.15)", strokeWidth: "0.5" }) }) }), _jsx("rect", { x: minX - padding, y: minY - padding, width: width + padding * 2, height: height + padding * 2, fill: "url(#grid)" }), entities.map((entity) => (_jsx("polygon", { points: entity.polygon.points.map((point) => point.join(",")).join(" "), className: `diff-shape diff-${entity.change_type}`, children: _jsx("title", { children: entity.label ?? entity.entity_id }) }, entity.entity_id)))] }), _jsx("ul", { className: "diff-legend", children: entities.map((entity) => (_jsxs("li", { children: [_jsx("span", { className: `dot dot-${entity.change_type}` }), _jsx("strong", { children: entity.label ?? entity.entity_id }), _jsx("small", { children: entity.entity_type })] }, entity.entity_id))) })] }));
}
