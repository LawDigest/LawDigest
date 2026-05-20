const STATUS_META = {
  success: { label: "성공", className: "success" },
  failed: { label: "실패", className: "failed" },
  running: { label: "실행 중", className: "running" },
  warning: { label: "주의 필요", className: "warning" },
  fallback: { label: "Fallback", className: "fallback" },
  schema: { label: "검증 실패", className: "schema" },
};

const SAMPLE_RUNS = [
  {
    run_id: "run_20260520_210412_9f3a1b2c",
    command: "bill.ingest",
    status: "failed",
    provider: "Gemini CLI",
    started_at: "2026-05-20T21:04:12+09:00",
    finished_at: "2026-05-20T21:06:30+09:00",
    duration_seconds: 138,
    items: 128,
    artifacts: [],
    error: "schema_validation_failed",
    fallback_used: false,
    schema_failures: 2,
    steps: [
      { name: "스케줄 트리거", status: "success", started_at: "2026-05-20T21:04:12+09:00", duration: "120ms" },
      { name: "대상 수집", status: "success", started_at: "2026-05-20T21:04:12+09:00", duration: "1.2s" },
      { name: "문서 다운로드", status: "success", started_at: "2026-05-20T21:04:14+09:00", duration: "22.6s" },
      { name: "AI 요약 생성", status: "failed", started_at: "2026-05-20T21:04:37+09:00", duration: "1m 41s" },
      { name: "DB 저장", status: "pending", started_at: null, duration: "-" },
    ],
    logs: [
      { ts: "2026-05-20T21:04:37.512+09:00", level: "info", step: "run", msg: "gemini cli request started" },
      { ts: "2026-05-20T21:05:02.084+09:00", level: "error", error: "empty response", retry: true },
      { ts: "2026-05-20T21:06:02.005+09:00", level: "info", provider: "fallback", target: "Codex CLI" },
      { ts: "2026-05-20T21:06:30.213+09:00", level: "error", error: "schema_validation_failed", fields: ["ai_title", "status"] },
      { ts: "2026-05-20T21:06:38.084+09:00", level: "error", field: "ai_title", reason: "sentence ending" },
      { ts: "2026-05-20T21:06:40.110+09:00", fallback: "Codex CLI", next_action: "queued" },
    ],
  },
  {
    run_id: "run_20260520_210413_fallback",
    command: "bill.ingest (fallback)",
    status: "warning",
    provider: "Codex CLI",
    started_at: "2026-05-20T21:04:13+09:00",
    finished_at: "2026-05-20T21:07:55+09:00",
    duration_seconds: 222,
    items: 128,
    artifacts: ["artifacts/bill-ingest-fallback.json", "artifacts/bill-ingest-fallback.md", "logs/codex-fallback.jsonl"],
    error: null,
    fallback_used: true,
    schema_failures: 0,
    steps: [
      { name: "Fallback queue", status: "success", started_at: "2026-05-20T21:04:13+09:00", duration: "90ms" },
      { name: "Codex CLI 실행", status: "success", started_at: "2026-05-20T21:04:14+09:00", duration: "2m 54s" },
      { name: "산출물 저장", status: "success", started_at: "2026-05-20T21:07:45+09:00", duration: "10s" },
    ],
    logs: [
      { ts: "2026-05-20T21:04:13.203+09:00", level: "warn", fallback: "Codex CLI", reason: "Gemini CLI failed" },
      { ts: "2026-05-20T21:07:55.503+09:00", level: "info", status: "completed", artifacts: 3 },
    ],
  },
  {
    run_id: "run_20260520_205835_summary",
    command: "bill.summarize",
    status: "success",
    provider: "Gemini CLI",
    started_at: "2026-05-20T20:58:35+09:00",
    finished_at: "2026-05-20T21:02:46+09:00",
    duration_seconds: 251,
    items: 128,
    artifacts: ["output/latest-bills-summary.json", "output/latest-bills-summary.md", "logs/gemini-summary.jsonl"],
    error: null,
    fallback_used: false,
    schema_failures: 0,
    steps: [
      { name: "최신 법안 조회", status: "success", started_at: "2026-05-20T20:58:35+09:00", duration: "1.8s" },
      { name: "Gemini CLI 요약", status: "success", started_at: "2026-05-20T20:58:39+09:00", duration: "3m 41s" },
      { name: "Pydantic 검증", status: "success", started_at: "2026-05-20T21:02:28+09:00", duration: "1.3s" },
    ],
    logs: [
      { ts: "2026-05-20T21:02:46.120+09:00", level: "info", status: "success", target: 5 },
    ],
  },
  {
    run_id: "run_20260520_205842_summary",
    command: "bill.summarize",
    status: "success",
    provider: "Gemini CLI",
    started_at: "2026-05-20T20:58:42+09:00",
    finished_at: "2026-05-20T21:02:41+09:00",
    duration_seconds: 239,
    items: 127,
    artifacts: ["output/bill-summary-205842.json", "output/bill-summary-205842.md"],
    fallback_used: false,
    schema_failures: 0,
    steps: [{ name: "요약 생성", status: "success", started_at: "2026-05-20T20:58:42+09:00", duration: "3m 59s" }],
    logs: [{ ts: "2026-05-20T21:02:41.021+09:00", level: "info", status: "success" }],
  },
  {
    run_id: "run_20260520_205511_normalize",
    command: "document.normalize",
    status: "success",
    provider: "Claude CLI",
    started_at: "2026-05-20T20:55:11+09:00",
    finished_at: "2026-05-20T20:56:32+09:00",
    duration_seconds: 81,
    items: 128,
    artifacts: ["artifacts/document-normalize.json", "logs/claude-normalize.jsonl", "reports/normalize.md"],
    fallback_used: false,
    schema_failures: 0,
    steps: [{ name: "문서 정규화", status: "success", started_at: "2026-05-20T20:55:11+09:00", duration: "1m 21s" }],
    logs: [{ ts: "2026-05-20T20:56:32.001+09:00", level: "info", status: "success" }],
  },
  {
    run_id: "run_20260520_205307_fetch",
    command: "document.fetch",
    status: "success",
    provider: "Gemini CLI",
    started_at: "2026-05-20T20:53:07+09:00",
    finished_at: "2026-05-20T20:53:54+09:00",
    duration_seconds: 47,
    items: 128,
    artifacts: ["artifacts/document-fetch.json", "logs/document-fetch.jsonl"],
    fallback_used: false,
    schema_failures: 0,
    steps: [{ name: "문서 다운로드", status: "success", started_at: "2026-05-20T20:53:07+09:00", duration: "47s" }],
    logs: [{ ts: "2026-05-20T20:53:54.301+09:00", level: "info", status: "success" }],
  },
  {
    run_id: "run_20260520_205015_schedule",
    command: "schedule.daily",
    status: "success",
    provider: "-",
    started_at: "2026-05-20T20:50:15+09:00",
    finished_at: "2026-05-20T20:50:20+09:00",
    duration_seconds: 5,
    items: 1,
    artifacts: ["logs/schedule-daily.jsonl"],
    fallback_used: false,
    schema_failures: 0,
    steps: [{ name: "스케줄 등록", status: "success", started_at: "2026-05-20T20:50:15+09:00", duration: "5s" }],
    logs: [{ ts: "2026-05-20T20:50:20.001+09:00", level: "info", status: "success" }],
  },
  {
    run_id: "run_20260520_210521_running",
    command: "bill.summarize",
    status: "running",
    provider: "Gemini CLI",
    started_at: "2026-05-20T21:05:21+09:00",
    finished_at: null,
    duration_seconds: 19,
    items: null,
    artifacts: [],
    fallback_used: false,
    schema_failures: 0,
    steps: [
      { name: "최신 법안 조회", status: "success", started_at: "2026-05-20T21:05:21+09:00", duration: "1.4s" },
      { name: "Gemini CLI 요약", status: "running", started_at: "2026-05-20T21:05:23+09:00", duration: "진행 중" },
    ],
    logs: [{ ts: "2026-05-20T21:05:40.320+09:00", level: "info", status: "running" }],
  },
  {
    run_id: "run_20260520_204810_ingest",
    command: "bill.ingest",
    status: "success",
    provider: "Gemini CLI",
    started_at: "2026-05-20T20:48:10+09:00",
    finished_at: "2026-05-20T20:50:02+09:00",
    duration_seconds: 112,
    items: 127,
    artifacts: ["artifacts/bill-ingest.json", "logs/bill-ingest.jsonl", "reports/ingest.md"],
    fallback_used: false,
    schema_failures: 0,
    steps: [{ name: "법안 수집", status: "success", started_at: "2026-05-20T20:48:10+09:00", duration: "1m 52s" }],
    logs: [{ ts: "2026-05-20T20:50:02.100+09:00", level: "info", status: "success" }],
  },
  {
    run_id: "run_20260520_204502_fetch",
    command: "document.fetch",
    status: "success",
    provider: "Gemini CLI",
    started_at: "2026-05-20T20:45:02+09:00",
    finished_at: "2026-05-20T20:45:51+09:00",
    duration_seconds: 49,
    items: 127,
    artifacts: ["artifacts/document-fetch-204502.json", "logs/document-fetch-204502.jsonl"],
    fallback_used: false,
    schema_failures: 0,
    steps: [{ name: "문서 다운로드", status: "success", started_at: "2026-05-20T20:45:02+09:00", duration: "49s" }],
    logs: [{ ts: "2026-05-20T20:45:51.019+09:00", level: "info", status: "success" }],
  },
];

const state = {
  runs: [],
  selectedRunId: null,
  provider: "all",
  status: "all",
  query: "",
  logMode: "pretty",
  source: "sample",
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

const els = {
  providerButtons: () => $$("[data-provider]"),
  statusRail: $("#statusRail"),
  searchInput: $("#searchInput"),
  updatedAt: $("#updatedAt"),
  incidentCopy: $("#incidentCopy"),
  runCountLabel: $("#runCountLabel"),
  runsTableBody: $("#runsTableBody"),
  currentPage: $("#currentPage"),
  traceStatus: $("#traceStatus"),
  traceMeta: $("#traceMeta"),
  schemaPill: $("#schemaPill"),
  stepsList: $("#stepsList"),
  schemaColumn: $("#schemaColumn"),
  logBox: $("#logBox"),
  phoneIncident: $("#phoneIncident"),
  phoneKpis: $("#phoneKpis"),
  phoneFilters: $("#phoneFilters"),
  phoneRunCount: $("#phoneRunCount"),
  phoneRuns: $("#phoneRuns"),
  trayHead: $("#trayHead"),
  trayId: $("#trayId"),
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function parseJsonl(text) {
  const trimmed = text.trim();
  if (!trimmed) return [];
  if (trimmed.startsWith("[")) return JSON.parse(trimmed).map(normalizeRun);
  return trimmed
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => normalizeRun(JSON.parse(line)))
    .filter(Boolean);
}

function normalizeRun(raw) {
  if (!raw) return null;
  const result = raw.result || {};
  const runId = raw.run_id || raw.id || result.run_id;
  const command = raw.command || result.command || raw.step || raw.event || "pipeline.run";
  const status = normalizeStatus(raw.status || result.status || raw.level);
  return {
    run_id: runId || `run_${Math.random().toString(36).slice(2, 10)}`,
    command,
    status,
    provider: raw.provider || result.provider || "-",
    started_at: raw.started_at || raw.start_time || raw.ts || result.started_at || new Date().toISOString(),
    finished_at: raw.finished_at || raw.end_time || result.finished_at || null,
    duration_seconds: Number(raw.duration_seconds ?? result.duration_seconds ?? 0),
    items: raw.items ?? raw.count ?? result.items ?? result.success ?? null,
    artifacts: raw.artifacts || result.artifacts || [],
    error: raw.error || result.error || null,
    fallback_used: Boolean(raw.fallback_used || result.fallback_used || raw.fallback),
    schema_failures: Number(raw.schema_failures ?? result.schema_failures ?? 0),
    steps: raw.steps || result.steps || [],
    logs: raw.logs || [raw],
  };
}

function normalizeStatus(value) {
  const status = String(value || "").toLowerCase();
  if (["success", "succeeded", "ok", "info"].includes(status)) return "success";
  if (["failed", "failure", "error"].includes(status)) return "failed";
  if (["running", "in_progress", "pending"].includes(status)) return "running";
  if (["warning", "warn", "fallback"].includes(status)) return "warning";
  return status || "unknown";
}

async function loadRuns() {
  try {
    const response = await fetch(`/api/runs?ts=${Date.now()}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`/api/runs ${response.status}`);
    const payload = await response.json();
    if (!payload.runs?.length) throw new Error("empty /api/runs");
    state.runs = payload.runs.map(normalizeRun);
    state.source = payload.source_exists ? "api" : "api-empty";
  } catch {
    try {
      const response = await fetch(`./pipeline-runs.jsonl?ts=${Date.now()}`, { cache: "no-store" });
      if (!response.ok) throw new Error(`pipeline-runs.jsonl ${response.status}`);
      const parsed = parseJsonl(await response.text());
      if (!parsed.length) throw new Error("empty pipeline-runs.jsonl");
      state.runs = parsed;
      state.source = "pipeline-runs.jsonl";
    } catch {
      state.runs = SAMPLE_RUNS;
      state.source = "sample";
    }
  }
  if (!state.selectedRunId || !state.runs.some((run) => run.run_id === state.selectedRunId)) {
    state.selectedRunId = getIncidentRun()?.run_id || state.runs[0]?.run_id || null;
  }
  render();
}

function getSummary() {
  return {
    running: state.runs.filter((run) => run.status === "running").length,
    success: state.runs.filter((run) => run.status === "success").length,
    failed: state.runs.filter((run) => run.status === "failed").length,
    warning: state.runs.filter((run) => run.status === "warning").length,
    fallback: state.runs.filter((run) => run.fallback_used).length,
    schema: state.runs.reduce((sum, run) => sum + (run.schema_failures || 0), 0),
  };
}

function getIncidentRun() {
  return state.runs.find((run) => run.status === "failed" || run.schema_failures > 0 || run.fallback_used)
    || state.runs.find((run) => run.status === "running")
    || state.runs[0];
}

function getVisibleRuns() {
  const query = state.query.trim().toLowerCase();
  return state.runs.filter((run) => {
    if (state.provider !== "all" && run.provider !== state.provider) return false;
    if (state.status !== "all") {
      if (state.status === "fallback" && !run.fallback_used) return false;
      else if (state.status === "schema" && !run.schema_failures) return false;
      else if (!["fallback", "schema"].includes(state.status) && run.status !== state.status) return false;
    }
    if (!query) return true;
    const haystack = [
      run.run_id,
      run.command,
      run.provider,
      run.error,
      ...(Array.isArray(run.artifacts) ? run.artifacts : Object.values(run.artifacts || {})),
    ].join(" ").toLowerCase();
    return haystack.includes(query);
  });
}

function formatDateTime(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, "0");
  const dd = String(date.getDate()).padStart(2, "0");
  const hh = String(date.getHours()).padStart(2, "0");
  const mi = String(date.getMinutes()).padStart(2, "0");
  const ss = String(date.getSeconds()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd} ${hh}:${mi}:${ss}`;
}

function formatTime(value) {
  const full = formatDateTime(value);
  return full.includes(" ") ? full.split(" ")[1] : full;
}

function formatDuration(seconds) {
  if (!seconds && seconds !== 0) return "--";
  if (seconds < 60) return `00:${String(seconds).padStart(2, "0")}`;
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(rest).padStart(2, "0")}`;
}

function statusLabel(run) {
  if (run.fallback_used && run.status !== "failed") return STATUS_META.warning.label;
  return STATUS_META[run.status]?.label || "알 수 없음";
}

function statusClass(run) {
  if (run.fallback_used && run.status !== "failed") return "warning";
  return STATUS_META[run.status]?.className || "fallback";
}

function artifactCount(run) {
  if (Array.isArray(run.artifacts)) return run.artifacts.length;
  if (run.artifacts && typeof run.artifacts === "object") return Object.keys(run.artifacts).length;
  return 0;
}

function render() {
  const visible = getVisibleRuns();
  if (!visible.some((run) => run.run_id === state.selectedRunId)) {
    state.selectedRunId = visible[0]?.run_id || state.runs[0]?.run_id || null;
  }
  renderProviders();
  renderStatusRail();
  renderIncident();
  renderRuns(visible);
  renderTrace();
  renderPhone(visible);
  const sourceLabel = state.source === "api" ? "API · 방금 전" : state.source === "pipeline-runs.jsonl" ? "JSONL · 방금 전" : "샘플 데이터 · 방금 전";
  els.updatedAt.textContent = sourceLabel;
}

function renderProviders() {
  els.providerButtons().forEach((button) => {
    button.classList.toggle("is-active", button.dataset.provider === state.provider);
  });
}

function renderStatusRail() {
  const summary = getSummary();
  const cells = [
    ["running", "실행 중", summary.running],
    ["success", "성공", summary.success],
    ["failed", "실패", summary.failed],
    ["warning", "주의 필요", summary.warning],
    ["fallback", "Fallback", summary.fallback],
    ["schema", "검증 실패", summary.schema],
  ];
  els.statusRail.innerHTML = cells.map(([key, label, count]) => (
    `<button class="status-cell ${key} ${state.status === key ? "is-active" : ""}" type="button" data-status="${key}">${label} <b>${count}</b></button>`
  )).join("");
}

function renderIncident() {
  const run = getIncidentRun();
  if (!run) {
    els.incidentCopy.innerHTML = "<strong>정상</strong><span>표시할 실행 이력이 없습니다.</span>";
    return;
  }
  const prefix = run.status === "failed" ? "주의 필요" : run.status === "running" ? "실행 중" : "확인 필요";
  const fallback = run.fallback_used ? " · fallback 사용" : "";
  els.incidentCopy.innerHTML = `<strong>${prefix}</strong><span>${escapeHtml(run.command)} · ${escapeHtml(run.provider)}${fallback} · ${formatDuration(run.duration_seconds)}</span>`;
}

function renderRuns(runs) {
  els.runCountLabel.textContent = `${runs.length}건 표시`;
  if (!runs.length) {
    els.runsTableBody.innerHTML = `<tr><td colspan="7"><div class="empty-state">조건에 맞는 실행 이력이 없습니다.</div></td></tr>`;
    return;
  }
  els.runsTableBody.innerHTML = runs.slice(0, 10).map((run) => {
    const selected = run.run_id === state.selectedRunId ? " class=\"is-selected\"" : "";
    return `
      <tr${selected} data-run-id="${escapeHtml(run.run_id)}">
        <td><span class="row-status ${statusClass(run)}">${statusLabel(run)}</span></td>
        <td title="${escapeHtml(formatDateTime(run.started_at))}">${escapeHtml(formatDateTime(run.started_at))}</td>
        <td><code>${escapeHtml(run.command)}</code></td>
        <td>${escapeHtml(run.provider)}</td>
        <td>${escapeHtml(formatDuration(run.duration_seconds))}</td>
        <td>${run.items ?? "--"}</td>
        <td class="chevron">${artifactCount(run)} ›</td>
      </tr>
    `;
  }).join("");
  els.currentPage.textContent = "1";
}

function renderTrace() {
  const run = state.runs.find((item) => item.run_id === state.selectedRunId) || state.runs[0];
  if (!run) return;
  els.traceStatus.innerHTML = `<span class="row-status ${statusClass(run)}">${statusLabel(run)}</span><strong>${escapeHtml(run.command)}</strong><button class="retry" type="button" data-action="readonly">재시도</button>`;
  els.traceMeta.innerHTML = `
    <span>Run ID</span><span>${escapeHtml(run.run_id)}</span>
    <span>시작 시간</span><span>${escapeHtml(formatDateTime(run.started_at))}</span>
    <span>종료 시간</span><span>${escapeHtml(formatDateTime(run.finished_at))}</span>
    <span>Provider</span><span>${escapeHtml(run.provider)}</span>
    <span>소요 시간</span><span>${escapeHtml(formatDuration(run.duration_seconds))}</span>
    <span>처리 항목</span><span>${run.items ?? "--"}건</span>
  `;
  const failures = run.schema_failures || (run.status === "failed" ? 1 : 0);
  els.schemaPill.textContent = failures ? `실패 (${failures}) ›` : "통과";
  els.schemaColumn.innerHTML = failures ? `스키마 검증<br><br>실패 (${failures}) ›` : "스키마 검증<br><br>통과";
  els.stepsList.innerHTML = (run.steps || []).map((step) => {
    const dot = step.status === "failed" ? "error" : step.status === "pending" ? "blank" : "";
    const mark = step.status === "failed" ? "×" : step.status === "pending" ? "" : "✓";
    return `<div class="step"><span class="step-dot ${dot}">${mark}</span><span>${escapeHtml(step.name)}<small>${escapeHtml(step.started_at ? formatTime(step.started_at) : "-")}</small></span><span class="step-time">${escapeHtml(step.duration || "-")}</span></div>`;
  }).join("") || `<div class="empty-state">단계 로그가 없습니다.</div>`;
  renderLogs(run);
}

function renderLogs(run) {
  const logs = run.logs?.length ? run.logs : [{ ts: new Date().toISOString(), level: "info", run_id: run.run_id }];
  els.logBox.innerHTML = logs.map((entry, index) => {
    const line = 1421 + index;
    const value = state.logMode === "pretty" ? JSON.stringify(entry, null, 0) : JSON.stringify(entry);
    return `<div class="log-row"><span>${line}</span><span>${escapeHtml(value)}</span></div>`;
  }).join("");
}

function renderPhone(runs) {
  const summary = getSummary();
  els.phoneKpis.innerHTML = [
    ["실행", summary.running],
    ["성공", summary.success],
    ["실패", summary.failed],
    ["주의", summary.warning],
  ].map(([label, count]) => `<div class="phone-kpi"><small>${label}</small><strong>${count}</strong></div>`).join("");
  const filters = [
    ["all", "전체"],
    ["running", `실행 중 ${summary.running}`],
    ["success", `성공 ${summary.success}`],
    ["failed", `실패 ${summary.failed}`],
    ["warning", `주의 ${summary.warning}`],
  ];
  els.phoneFilters.innerHTML = filters.map(([key, label]) => `<button class="phone-filter ${state.status === key ? "is-active" : ""}" type="button" data-status="${key}">${label}</button>`).join("");
  const incident = getIncidentRun();
  if (incident) {
    els.phoneIncident.innerHTML = `<strong>${incident.status === "failed" ? "주의 필요" : statusLabel(incident)}</strong><span>${escapeHtml(incident.command)} · ${escapeHtml(incident.provider)}</span>`;
  }
  els.phoneRunCount.textContent = `${runs.length}건`;
  els.phoneRuns.innerHTML = runs.slice(0, 6).map((run) => `
    <article class="phone-run ${statusClass(run)}" data-run-id="${escapeHtml(run.run_id)}">
      <div class="phone-run-top"><strong>${statusLabel(run)}</strong><span>${escapeHtml(run.provider)}</span></div>
      <em>${escapeHtml(run.command)}</em>
      <div class="phone-run-bottom"><span>${escapeHtml(formatTime(run.started_at))} · ${escapeHtml(formatDuration(run.duration_seconds))} · ${run.items ?? "--"}건</span><span>${artifactCount(run)} ▫</span></div>
    </article>
  `).join("");
  const selected = state.runs.find((run) => run.run_id === state.selectedRunId);
  if (selected) {
    els.trayHead.innerHTML = `<strong>선택된 실행</strong><span>${statusLabel(selected)}</span>`;
    els.trayId.textContent = selected.run_id;
  }
}

async function selectRun(runId) {
  if (!runId) return;
  state.selectedRunId = runId;
  if (state.source === "api") {
    try {
      const response = await fetch(`/api/runs/${encodeURIComponent(runId)}`, { cache: "no-store" });
      if (response.ok) {
        const payload = await response.json();
        const detail = normalizeRun(payload.run);
        state.runs = state.runs.map((run) => run.run_id === detail.run_id ? detail : run);
      }
    } catch {
      // Keep the table copy if the detail endpoint is temporarily unavailable.
    }
  }
  render();
}

document.addEventListener("click", (event) => {
  const provider = event.target.closest("[data-provider]");
  if (provider) {
    state.provider = provider.dataset.provider;
    render();
    return;
  }
  const status = event.target.closest("[data-status]");
  if (status) {
    state.status = state.status === status.dataset.status ? "all" : status.dataset.status;
    render();
    return;
  }
  const row = event.target.closest("[data-run-id]");
  if (row) {
    selectRun(row.dataset.runId);
    return;
  }
  const logMode = event.target.closest("[data-log-mode]");
  if (logMode) {
    state.logMode = logMode.dataset.logMode;
    $$("[data-log-mode]").forEach((button) => button.classList.toggle("is-active", button === logMode));
    renderTrace();
    return;
  }
  const action = event.target.closest("[data-action]")?.dataset.action;
  if (action === "refresh") loadRuns();
  if (action === "focus-incident") selectRun(getIncidentRun()?.run_id);
  if (action === "clear-selection") selectRun(getVisibleRuns()[0]?.run_id || state.runs[0]?.run_id);
  if (action === "copy-log") copyCurrentLog();
  if (action === "readonly") window.alert("현재 버전은 read-only 모니터링입니다. 재시도 실행은 아직 연결하지 않았습니다.");
});

els.searchInput.addEventListener("input", (event) => {
  state.query = event.target.value;
  render();
});

document.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
    event.preventDefault();
    els.searchInput.focus();
  }
  if (event.key === "Escape" && document.activeElement === els.searchInput) {
    els.searchInput.value = "";
    state.query = "";
    render();
  }
});

function copyCurrentLog() {
  const run = state.runs.find((item) => item.run_id === state.selectedRunId);
  const value = (run?.logs || []).map((entry) => JSON.stringify(entry)).join("\n");
  navigator.clipboard?.writeText(value);
}

loadRuns();
