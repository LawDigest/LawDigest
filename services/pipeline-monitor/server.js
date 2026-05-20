#!/usr/bin/env node
const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");
const { URL } = require("node:url");

const ROOT = __dirname;
const PORT = Number(process.env.PORT || 32240);
const PIPELINE_RUNS_PATH = path.resolve(process.env.PIPELINE_RUNS_PATH || path.join(ROOT, "pipeline-runs.jsonl"));
const ALLOWED_ROOTS = [
  ROOT,
  path.resolve(process.env.PIPELINE_ARTIFACT_ROOT || ROOT),
  path.dirname(PIPELINE_RUNS_PATH),
];

const MIME_TYPES = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".jsonl": "application/x-ndjson; charset=utf-8",
  ".md": "text/markdown; charset=utf-8",
  ".txt": "text/plain; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".ico": "image/x-icon",
};

function sendJson(res, status, payload) {
  const body = JSON.stringify(payload);
  res.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
    "content-length": Buffer.byteLength(body),
  });
  res.end(body);
}

function sendText(res, status, text, type = "text/plain; charset=utf-8") {
  res.writeHead(status, { "content-type": type, "cache-control": "no-store" });
  res.end(text);
}

function redact(value) {
  if (Array.isArray(value)) return value.map(redact);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => {
      if (/api[_-]?key|token|password|secret|credential/i.test(key)) return [key, "[redacted]"];
      return [key, redact(item)];
    }));
  }
  if (typeof value === "string") {
    return value.replace(/(api[_-]?key|token|password|secret)=([^&\s]+)/gi, "$1=[redacted]");
  }
  return value;
}

function normalizeStatus(value) {
  const status = String(value || "").toLowerCase();
  if (["success", "succeeded", "ok", "info"].includes(status)) return "success";
  if (["failed", "failure", "error"].includes(status)) return "failed";
  if (["running", "in_progress", "pending"].includes(status)) return "running";
  if (["warning", "warn", "fallback"].includes(status)) return "warning";
  return status || "unknown";
}

function normalizeRun(raw, index) {
  const source = redact(raw);
  const result = source.result || {};
  const runId = source.run_id || source.id || result.run_id || `line_${index + 1}`;
  const command = source.command || result.command || source.step || source.event || "pipeline.run";
  const status = normalizeStatus(source.status || result.status || source.level);
  return {
    run_id: runId,
    command,
    status,
    provider: source.provider || result.provider || "-",
    started_at: source.started_at || source.start_time || source.ts || result.started_at || null,
    finished_at: source.finished_at || source.end_time || result.finished_at || null,
    duration_seconds: Number(source.duration_seconds ?? result.duration_seconds ?? 0),
    items: source.items ?? source.count ?? result.items ?? result.success ?? null,
    artifacts: source.artifacts || result.artifacts || [],
    error: source.error || result.error || null,
    fallback_used: Boolean(source.fallback_used || result.fallback_used || source.fallback),
    schema_failures: Number(source.schema_failures ?? result.schema_failures ?? 0),
    steps: source.steps || result.steps || [],
    logs: source.logs || [source],
  };
}

function readRuns() {
  if (!fs.existsSync(PIPELINE_RUNS_PATH)) {
    return {
      source: PIPELINE_RUNS_PATH,
      exists: false,
      runs: [],
      skipped: [{ line: 0, error: "pipeline-runs.jsonl not found" }],
    };
  }

  const raw = fs.readFileSync(PIPELINE_RUNS_PATH, "utf8").trim();
  if (!raw) return { source: PIPELINE_RUNS_PATH, exists: true, runs: [], skipped: [] };

  if (raw.startsWith("[")) {
    return {
      source: PIPELINE_RUNS_PATH,
      exists: true,
      runs: JSON.parse(raw).map(normalizeRun),
      skipped: [],
    };
  }

  const runs = [];
  const skipped = [];
  raw.split(/\r?\n/).forEach((line, index) => {
    if (!line.trim()) return;
    try {
      runs.push(normalizeRun(JSON.parse(line), index));
    } catch (error) {
      skipped.push({ line: index + 1, error: error.message });
    }
  });
  runs.sort((a, b) => String(b.started_at || "").localeCompare(String(a.started_at || "")));
  return { source: PIPELINE_RUNS_PATH, exists: true, runs, skipped };
}

function summarize(runs) {
  return {
    running: runs.filter((run) => run.status === "running").length,
    success: runs.filter((run) => run.status === "success").length,
    failed: runs.filter((run) => run.status === "failed").length,
    warning: runs.filter((run) => run.status === "warning").length,
    fallback: runs.filter((run) => run.fallback_used).length,
    schema: runs.reduce((sum, run) => sum + (run.schema_failures || 0), 0),
  };
}

function isAllowedFile(filePath) {
  const resolved = path.resolve(filePath);
  return ALLOWED_ROOTS.some((root) => resolved === root || resolved.startsWith(`${root}${path.sep}`));
}

function serveStatic(reqUrl, res) {
  const requestPath = decodeURIComponent(reqUrl.pathname === "/" ? "/index.html" : reqUrl.pathname);
  const filePath = path.resolve(ROOT, `.${requestPath}`);
  if (!filePath.startsWith(`${ROOT}${path.sep}`)) {
    sendText(res, 403, "Forbidden");
    return;
  }
  fs.readFile(filePath, (error, data) => {
    if (error) {
      sendText(res, error.code === "ENOENT" ? 404 : 500, error.code === "ENOENT" ? "Not found" : "Server error");
      return;
    }
    const ext = path.extname(filePath);
    res.writeHead(200, {
      "content-type": MIME_TYPES[ext] || "application/octet-stream",
      "cache-control": "no-store",
    });
    res.end(data);
  });
}

function handleApi(req, res, reqUrl) {
  if (reqUrl.pathname === "/api/health") {
    const info = readRuns();
    sendJson(res, 200, {
      ok: true,
      service: "pipeline-monitor",
      source: info.source,
      source_exists: info.exists,
      runs: info.runs.length,
      skipped: info.skipped.length,
    });
    return;
  }

  if (reqUrl.pathname === "/api/runs") {
    const info = readRuns();
    sendJson(res, 200, {
      source: info.source,
      source_exists: info.exists,
      skipped: info.skipped,
      summary: summarize(info.runs),
      runs: info.runs,
    });
    return;
  }

  const runMatch = reqUrl.pathname.match(/^\/api\/runs\/([^/]+)$/);
  if (runMatch) {
    const runId = decodeURIComponent(runMatch[1]);
    const info = readRuns();
    const run = info.runs.find((item) => item.run_id === runId);
    if (!run) {
      sendJson(res, 404, { error: "run not found", run_id: runId });
      return;
    }
    sendJson(res, 200, { source: info.source, run });
    return;
  }

  const artifactMatch = reqUrl.pathname.match(/^\/api\/artifacts\/(.+)$/);
  if (artifactMatch) {
    const artifactPath = decodeURIComponent(artifactMatch[1]);
    const resolved = path.resolve(path.dirname(PIPELINE_RUNS_PATH), artifactPath);
    if (!isAllowedFile(resolved)) {
      sendJson(res, 403, { error: "artifact path is outside allowed roots" });
      return;
    }
    fs.readFile(resolved, "utf8", (error, text) => {
      if (error) {
        sendJson(res, error.code === "ENOENT" ? 404 : 500, { error: error.message });
        return;
      }
      sendJson(res, 200, { path: resolved, content: redact(text) });
    });
    return;
  }

  sendJson(res, 404, { error: "unknown api route" });
}

const server = http.createServer((req, res) => {
  const reqUrl = new URL(req.url, `http://${req.headers.host || "localhost"}`);
  if (req.method !== "GET" && req.method !== "HEAD") {
    sendJson(res, 405, { error: "method not allowed" });
    return;
  }
  if (reqUrl.pathname.startsWith("/api/")) {
    handleApi(req, res, reqUrl);
    return;
  }
  serveStatic(reqUrl, res);
});

server.listen(PORT, "0.0.0.0", () => {
  console.log(`pipeline-monitor listening on http://0.0.0.0:${PORT}`);
  console.log(`PIPELINE_RUNS_PATH=${PIPELINE_RUNS_PATH}`);
});
