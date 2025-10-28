import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";

import { DiffViewer } from "../src/components/DiffViewer";
import type { DiffPayload } from "../src/types/jobs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function usage(): never {
  console.error("Usage: tsx scripts/render_diff.tsx <diff-json-path> [job-id]");
  process.exit(1);
}

const [, , diffPathArg, jobIdArg] = process.argv;

if (!diffPathArg) {
  usage();
}

const diffPath = path.isAbsolute(diffPathArg)
  ? diffPathArg
  : path.resolve(__dirname, "..", diffPathArg);

if (!fs.existsSync(diffPath)) {
  console.error(`Diff file not found: ${diffPath}`);
  process.exit(1);
}

const diffPayload = JSON.parse(fs.readFileSync(diffPath, "utf-8")) as DiffPayload;
const jobId = jobIdArg ?? "demo-job";

const markup = renderToStaticMarkup(
  <DiffViewer jobId={jobId} payload={diffPayload} isLoading={false} error={null} reports={[]} />
);

console.log(markup);
