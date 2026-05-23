const SERVICE_SNAPSHOT = {
  totalBills: 36039,
  sourceSummary: 36038,
  aiSummary: 36038,
  missingAiSummary: 0,
  latestProposeDate: "2026-05-18",
  updatedAt: "20:50 KST",
};

const STAGES = [
  { name: "법안 수집", status: "확인 필요", tone: "warning" },
  { name: "원천 summary", status: "정상", tone: "success" },
  { name: "AI 요약 생성", status: "대상 없음", tone: "neutral" },
  { name: "Batch 제출", status: "대기 없음", tone: "neutral" },
  { name: "결과 회수", status: "관제 원천 미연결", tone: "warning" },
  { name: "서비스 노출", status: "정상", tone: "success" },
];

const BATCH_ROWS = [
  {
    id: "prod-summary-coverage",
    target: "운영 Bill 요약 필드",
    state: "반영 정상",
    tone: "success",
    progress: "36,038 / 36,038",
    source: "lawDB Bill",
    signal: "미요약 0",
    next: "신선도 확인",
    facts: [
      ["total bills", "36,039"],
      ["source summary present", "36,038"],
      ["AI summary present", "36,038"],
      ["missing AI summary", "0"],
      ["latest propose_date", "2026-05-18"],
    ],
    note: "요약 실패 대응보다 최신 수집 기준일 확인이 우선입니다.",
    providerNote: "최근 dry-run: Codex CLI 3/3 성공, Gemini CLI 5/5 성공",
  },
  {
    id: "prod-batch-monitor",
    target: "ai_batch_jobs/items",
    state: "관제 미연결",
    tone: "warning",
    progress: "테이블 없음",
    source: "lawDB",
    signal: "migration 필요",
    next: "상태 테이블 확인",
    facts: [
      ["table", "ai_batch_jobs"],
      ["prod status", "missing"],
      ["impact", "batch 상태 추적 불가"],
      ["safe publish", "요약 필드는 정상"],
    ],
    note: "서비스 노출은 가능하지만 batch 제출/회수 상태를 운영 DB에서 직접 추적할 수 없습니다.",
    providerNote: "테스트 DB에는 Gemini batch 5/5 완료 기록이 있습니다.",
  },
  {
    id: "test-gemini-batch-001",
    target: "테스트 배치",
    state: "완료",
    tone: "success",
    progress: "5 / 5 DONE",
    source: "Gemini batch",
    signal: "실패 0",
    next: "운영 적용 여부 판단",
    facts: [
      ["provider", "gemini"],
      ["status", "COMPLETED"],
      ["success", "5"],
      ["failed", "0"],
    ],
    note: "테스트 batch 경로는 정상 동작했으나 운영 상태 테이블 연결 여부는 별도 확인이 필요합니다.",
    providerNote: "model: gemini-3-flash-preview",
  },
  {
    id: "cli-summary-smoke",
    target: "최근 수동 요약 검증",
    state: "성공",
    tone: "success",
    progress: "3 / 3 dry-run",
    source: "Codex CLI",
    signal: "DB 미반영",
    next: "샘플 품질 확인",
    facts: [
      ["command", "ai.summary"],
      ["mode", "dry_run"],
      ["success", "3"],
      ["failure", "0"],
    ],
    note: "수동 검증은 성공했지만 dry-run이므로 서비스 DB 반영은 별도 실행이 필요합니다.",
    providerNote: "cli_provider: codex",
  },
  {
    id: "bill-ingest-hourly",
    target: "법안 수집 DAG",
    state: "스케줄됨",
    tone: "neutral",
    progress: "매시 00분",
    source: "국회 API",
    signal: "최신일 2026-05-18",
    next: "수집 공백 확인",
    facts: [
      ["dag", "bill_ingest_dag"],
      ["schedule", "0 * * * *"],
      ["latest propose_date", "2026-05-18"],
      ["service priority", "freshness"],
    ],
    note: "요약 커버리지는 정상입니다. 다음 운영 판단은 최신 법안 수집 기준일입니다.",
    providerNote: "AI provider와 무관한 수집 단계입니다.",
  },
];

const $ = (selector) => document.querySelector(selector);

const els = {
  metricGrid: $("#metricGrid"),
  chartGrid: $("#chartGrid"),
  stageStrip: $("#stageStrip"),
  batchRows: $("#batchRows"),
  mobileBatchRows: $("#mobileBatchRows"),
  batchCountLabel: $("#batchCountLabel"),
  detailPanel: $("#detailPanel"),
  evidenceLines: $("#evidenceLines"),
  runSourceLabel: $("#runSourceLabel"),
  searchInput: $("#searchInput"),
  sidebarSearchInput: $("#sidebarSearchInput"),
  sidebarUpdatedAt: $("#sidebarUpdatedAt"),
};

const state = {
  selectedId: "prod-summary-coverage",
  query: "",
  runSource: "pipeline-runs.jsonl",
  runEvidence: [],
};

function apiUrl(path) {
  return new URL(path, window.location.href).toString();
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function number(value) {
  return Number(value).toLocaleString("ko-KR");
}

function toneClass(tone) {
  if (tone === "success") return "success";
  if (tone === "warning") return "warning";
  return "neutral";
}

function getFilteredRows() {
  const query = state.query.trim().toLowerCase();
  if (!query) return BATCH_ROWS;
  return BATCH_ROWS.filter((row) => (
    [
      row.id,
      row.target,
      row.state,
      row.progress,
      row.source,
      row.signal,
      row.next,
      row.note,
      row.providerNote,
    ].join(" ").toLowerCase().includes(query)
  ));
}

function renderMetrics() {
  const coverage = `${number(SERVICE_SNAPSHOT.aiSummary)} / ${number(SERVICE_SNAPSHOT.sourceSummary)}`;
  const metrics = [
    ["AI 요약 커버리지", coverage],
    ["미요약", `${number(SERVICE_SNAPSHOT.missingAiSummary)}건`],
    ["최신 발의일", SERVICE_SNAPSHOT.latestProposeDate],
    ["원천 summary", `${number(SERVICE_SNAPSHOT.sourceSummary)} / ${number(SERVICE_SNAPSHOT.totalBills)}`],
  ];
  els.metricGrid.innerHTML = metrics.map(([label, value]) => (
    `<div class="metric"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`
  )).join("");
}

function renderCharts() {
  els.chartGrid.innerHTML = `
    <article class="panel">
      <div class="panel-head"><h3>요약 커버리지</h3><span>100%</span></div>
      <div class="progress-shell"><div class="progress-fill" style="--value: 100%"></div></div>
      <div class="chart-note"><span>${number(SERVICE_SNAPSHOT.aiSummary)} ready</span><span>${number(SERVICE_SNAPSHOT.missingAiSummary)} missing</span></div>
    </article>
    <article class="panel">
      <div class="panel-head"><h3>최신성</h3><span>05-18 → 05-23</span></div>
      <div class="freshness-line" aria-hidden="true">
        <span class="freshness-point" style="left: 0%"></span>
        <span class="freshness-point now" style="left: 100%"></span>
      </div>
      <div class="chart-note"><span>latest 05-18</span><span>확인 필요</span></div>
    </article>
    <article class="panel">
      <div class="panel-head"><h3>Batch 상태</h3><span>3 signals</span></div>
      <div class="segment-list">
        <div class="segment-row"><span>요약 대상 없음</span><strong>0</strong></div>
        <div class="segment-row warning"><span>관제 미연결</span><strong>prod</strong></div>
        <div class="segment-row neutral"><span>테스트 완료</span><strong>5/5</strong></div>
      </div>
    </article>
  `;
}

function renderStages() {
  els.stageStrip.innerHTML = STAGES.map((stage) => (
    `<article class="stage-cell ${toneClass(stage.tone)}"><span>${escapeHtml(stage.name)}</span><strong>${escapeHtml(stage.status)}</strong></article>`
  )).join("");
}

function renderRows() {
  const rows = getFilteredRows();
  if (!rows.some((row) => row.id === state.selectedId)) {
    state.selectedId = rows[0]?.id || BATCH_ROWS[0].id;
  }
  els.batchCountLabel.textContent = `${rows.length}개 기준`;
  els.batchRows.innerHTML = rows.map((row) => `
    <tr class="${row.id === state.selectedId ? "is-selected" : ""}" data-row-id="${escapeHtml(row.id)}">
      <td><code>${escapeHtml(row.id)}</code></td>
      <td>${escapeHtml(row.target)}</td>
      <td><span class="state-pill ${toneClass(row.tone)}">${escapeHtml(row.state)}</span></td>
      <td>${escapeHtml(row.progress)}</td>
      <td>${escapeHtml(row.source)}</td>
      <td>${escapeHtml(row.signal)}</td>
      <td>${escapeHtml(row.next)}</td>
    </tr>
  `).join("");

  els.mobileBatchRows.innerHTML = rows.map((row) => `
    <button class="mobile-batch ${row.id === state.selectedId ? "is-selected" : ""}" type="button" data-row-id="${escapeHtml(row.id)}">
      <header><code>${escapeHtml(row.id)}</code><span class="state-pill ${toneClass(row.tone)}">${escapeHtml(row.state)}</span></header>
      <p>${escapeHtml(row.target)} · ${escapeHtml(row.progress)}</p>
      <p>${escapeHtml(row.signal)} · ${escapeHtml(row.next)}</p>
    </button>
  `).join("");
}

function renderDetail() {
  const row = BATCH_ROWS.find((item) => item.id === state.selectedId) || BATCH_ROWS[0];
  const status = row.tone === "success" && row.id === "prod-summary-coverage"
    ? "서비스 노출 가능 · 요약 필드 정상"
    : `${row.state} · ${row.next}`;
  els.detailPanel.innerHTML = `
    <h2>선택 기준 상세</h2>
    <div class="detail-status ${toneClass(row.tone)}">${escapeHtml(status)}</div>
    <ul class="fact-list">
      ${row.facts.map(([label, value]) => `<li><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></li>`).join("")}
    </ul>
    <p class="decision-note">${escapeHtml(row.note)}</p>
    <div class="dryrun-box"><strong>실행 보조 정보</strong><span>${escapeHtml(row.providerNote)}</span></div>
  `;
}

function renderEvidence() {
  const baseLines = [
    "prod.bill_summary_coverage missing_ai_summary=0",
    "prod.ai_batch_jobs table_missing",
    "test.gemini_batch status=COMPLETED success=5 failed=0",
    "runtime.ai.summary codex dry_run success=3 failure=0",
  ];
  const lines = [...baseLines, ...state.runEvidence].slice(0, 8);
  els.runSourceLabel.textContent = state.runSource;
  els.evidenceLines.innerHTML = lines.map((line, index) => (
    `<div class="evidence-line"><span>${String(index + 1).padStart(2, "0")}</span><code>${escapeHtml(line)}</code></div>`
  )).join("");
}

function render() {
  renderMetrics();
  renderCharts();
  renderStages();
  renderRows();
  renderDetail();
  renderEvidence();
  els.sidebarUpdatedAt.textContent = `updated ${SERVICE_SNAPSHOT.updatedAt}`;
}

async function loadRuntimeEvidence() {
  try {
    const health = await fetch(apiUrl(`api/health?ts=${Date.now()}`), { cache: "no-store" });
    if (health.ok) {
      const payload = await health.json();
      state.runSource = payload.source_exists ? "api · pipeline-runs.jsonl" : "api · source missing";
      state.runEvidence = [
        `pipeline_monitor health ok runs=${payload.runs ?? 0} skipped=${payload.skipped ?? 0}`,
      ];
    }
    const runs = await fetch(apiUrl(`api/runs?ts=${Date.now()}`), { cache: "no-store" });
    if (runs.ok) {
      const payload = await runs.json();
      const summary = payload.summary || {};
      state.runEvidence.push(
        `runtime.runs success=${summary.success ?? 0} failed=${summary.failed ?? 0} running=${summary.running ?? 0}`,
      );
    }
  } catch {
    state.runSource = "static snapshot";
    state.runEvidence = ["pipeline_monitor runtime evidence unavailable"];
  }
  renderEvidence();
}

function selectRow(id) {
  if (!id) return;
  state.selectedId = id;
  renderRows();
  renderDetail();
}

function updateQuery(value) {
  state.query = value || "";
  renderRows();
  renderDetail();
}

document.addEventListener("click", (event) => {
  const row = event.target.closest("[data-row-id]");
  if (row) {
    selectRow(row.dataset.rowId);
    return;
  }
  const action = event.target.closest("[data-action]")?.dataset.action;
  if (action === "refresh") {
    loadRuntimeEvidence();
  }
  if (action === "focus-freshness") {
    selectRow("bill-ingest-hourly");
  }
});

[els.searchInput, els.sidebarSearchInput].forEach((input) => {
  input?.addEventListener("input", (event) => {
    updateQuery(event.target.value);
    if (event.target === els.searchInput && els.sidebarSearchInput) {
      els.sidebarSearchInput.value = event.target.value;
    }
    if (event.target === els.sidebarSearchInput && els.searchInput) {
      els.searchInput.value = event.target.value;
    }
  });
});

document.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
    event.preventDefault();
    els.searchInput?.focus();
  }
  if (event.key === "Escape") {
    if (els.searchInput) els.searchInput.value = "";
    if (els.sidebarSearchInput) els.sidebarSearchInput.value = "";
    updateQuery("");
  }
});

render();
loadRuntimeEvidence();
