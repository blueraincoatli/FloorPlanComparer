import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useCallback, useEffect, useMemo, useState } from "react";
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
    useEffect(() => {
        void loadJobs();
    }, [loadJobs]);
    const hasJobs = useMemo(() => jobs.length > 0, [jobs]);
    return (_jsxs("div", { className: "layout", children: [_jsxs("header", { className: "header", children: [_jsx("h1", { children: "Floor Plan Comparer" }), _jsx("p", { children: "\u5E73\u9762\u56FE\u5DEE\u5F02\u6BD4\u5BF9\u7684\u7AEF\u5230\u7AEF\u5DE5\u5177\u3002" })] }), _jsxs("main", { className: "content", children: [_jsxs("section", { className: "panel", children: [_jsx("h2", { children: "\u6838\u5FC3\u6D41\u7A0B" }), _jsx("ul", { children: hints.map((hint, index) => (_jsx("li", { children: _jsxs("button", { className: index === activeIndex ? "step active" : "step", type: "button", onClick: () => setActiveIndex(index), children: [_jsx("span", { className: "step-index", children: index + 1 }), _jsxs("span", { children: [_jsx("strong", { children: hint.title }), _jsx("br", {}), _jsx("small", { children: hint.description })] })] }) }, hint.title))) })] }), _jsxs("section", { className: "panel", children: [_jsxs("div", { className: "panel-header", children: [_jsx("h2", { children: "\u4EFB\u52A1\u6982\u89C8" }), _jsx("button", { className: "ghost-button", type: "button", onClick: () => void loadJobs(), disabled: isLoading, children: isLoading ? "刷新中..." : "刷新" })] }), error ? (_jsx("p", { className: "error", children: error })) : hasJobs ? (_jsx("div", { className: "table-wrapper", children: _jsxs("table", { className: "table", children: [_jsx("thead", { children: _jsxs("tr", { children: [_jsx("th", { children: "\u4EFB\u52A1 ID" }), _jsx("th", { children: "\u72B6\u6001" }), _jsx("th", { children: "\u8FDB\u5EA6" }), _jsx("th", { children: "\u6700\u8FD1\u66F4\u65B0\u65F6\u95F4" })] }) }), _jsx("tbody", { children: jobs.map((job) => (_jsxs("tr", { children: [_jsx("td", { children: job.jobId }), _jsx("td", { children: _jsx("span", { className: `badge status-${job.status}`, children: statusText[job.status] ?? job.status }) }), _jsx("td", { children: formatProgress(job.progress) }), _jsx("td", { children: formatTimestamp(job.updatedAt) })] }, job.jobId))) })] }) })) : (_jsx("p", { className: "muted", children: "\u6682\u65E0\u4EFB\u52A1\uFF0C\u5FEB\u53BB\u4E0A\u4F20\u7B2C\u4E00\u7EC4\u56FE\u7EB8\u5427\uFF01" }))] }), _jsxs("section", { className: "panel", children: [_jsx("h2", { children: "\u4E0B\u4E00\u6B65" }), _jsx("p", { children: "\u5F53\u524D\u9875\u9762\u4E3A\u5360\u4F4D\u9AA8\u67B6\u3002\u540E\u7EED\u5C06\u63A5\u5165\u4E0A\u4F20\u63A7\u4EF6\u3001\u4EFB\u52A1\u8BE6\u60C5\u9875\u548C\u5DEE\u5F02\u53EF\u89C6\u5316\u7EC4\u4EF6\uFF0C\u9A8C\u8BC1\u5B8C\u6574\u7684\u7AEF\u5230\u7AEF\u6D41\u7A0B\u3002" }), _jsxs("p", { children: ["\u82E5\u9700\u81EA\u5B9A\u4E49 API \u5730\u5740\uFF0C\u53EF\u5728\u524D\u7AEF\u76EE\u5F55\u521B\u5EFA ", _jsx("code", { children: ".env" }), " \u5E76\u8BBE\u7F6E ", _jsx("code", { children: "VITE_API_BASE_URL" }), "\u3002"] })] })] }), _jsxs("footer", { className: "footer", children: ["\u00A9 ", new Date().getFullYear(), " Floor Plan Comparer"] })] }));
}
