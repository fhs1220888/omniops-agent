const scenarioSelect = document.querySelector("#scenarioSelect");
const statusEl = document.querySelector("#status");
const runScenarioBtn = document.querySelector("#runScenarioBtn");
const benchmarkBtn = document.querySelector("#benchmarkBtn");
const highRiskBtn = document.querySelector("#highRiskBtn");
const approveBtn = document.querySelector("#approveBtn");
const rejectBtn = document.querySelector("#rejectBtn");

let currentApprovalId = null;

function setStatus(text) {
  statusEl.textContent = text;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`${response.status} ${body}`);
  }
  return response.json();
}

function setText(id, value) {
  document.querySelector(`#${id}`).textContent = value ?? "-";
}

function renderList(id, items, renderer) {
  const el = document.querySelector(`#${id}`);
  el.innerHTML = "";
  if (!items || items.length === 0) {
    el.innerHTML = '<div class="item">None</div>';
    return;
  }
  for (const item of items) {
    const row = document.createElement("div");
    row.className = "item";
    row.textContent = renderer(item);
    el.appendChild(row);
  }
}

function renderScenario(payload) {
  setText("rootCause", payload.root_cause);
  setText("confidence", payload.confidence);

  const report = payload.report_markdown || "";
  document.querySelector("#reportOutput").textContent = report || "No report returned.";

  const reflectionDecision = findReportValue(report, "Decision") || "-";
  const replanning = findReportValue(report, "Replanning requested") || "-";
  const rounds = findReportValue(report, "Investigation rounds") || "-";
  setText("reflection", reflectionDecision);
  setText("replanning", replanning);
  setText("rounds", rounds);

  renderList("agentTimeline", payload.agent_timeline, (item) => item);
  renderList("toolTimeline", payload.tool_timeline, (item) => item);
  renderList("evidenceItems", payload.evidence, (item) => item);

  renderList("deniedTools", payload.denied_tools || [], (item) => {
    return `${item.tool_name}: ${item.reason}`;
  });
  renderList("approvalRequiredTools", payload.approval_required_tools || [], (item) => {
    return `${item.tool_name}: ${item.approval_id || "pending"} ${item.reason}`;
  });

  document.querySelector("#evidenceGraph").textContent = JSON.stringify(
    payload.evidence_graph || {},
    null,
    2
  );
}

function findReportValue(report, label) {
  const line = report
    .split("\n")
    .find((entry) => entry.trim().startsWith(`- ${label}:`));
  if (!line) return null;
  return line.split(":").slice(1).join(":").trim();
}

async function runScenario() {
  setStatus("Running");
  try {
    const scenario = scenarioSelect.value;
    const result = await api(`/api/demo/run/${scenario}`, { method: "POST" });
    renderScenario(result);
    setStatus("Ready");
  } catch (error) {
    setStatus("Error");
    document.querySelector("#reportOutput").textContent = error.message;
  }
}

async function runBenchmark() {
  setStatus("Benchmarking");
  try {
    const result = await api("/api/demo/benchmark");
    setText("benchCount", result.scenario_count);
    setText("benchAccuracy", result.rca_accuracy);
    setText("benchEvidence", result.evidence_precision);
    setText("benchAgents", result.average_agent_count);
    setText("benchTools", result.average_tool_count);
    setStatus("Ready");
  } catch (error) {
    setStatus("Error");
  }
}

async function runHighRiskDemo() {
  setStatus("Requesting approval");
  approveBtn.disabled = true;
  rejectBtn.disabled = true;
  currentApprovalId = null;
  try {
    const result = await api("/api/demo/high-risk-tool", { method: "POST" });
    currentApprovalId = result.approval_id;
    renderList("approvalResult", [result], (item) => {
      return `${item.status}: ${item.tool_name} approval_id=${item.approval_id} reason=${item.reason}`;
    });
    approveBtn.disabled = false;
    rejectBtn.disabled = false;
    setStatus("Approval pending");
  } catch (error) {
    renderList("approvalResult", [{ error: error.message }], (item) => item.error);
    setStatus("Error");
  }
}

async function decideApproval(decision) {
  if (!currentApprovalId) return;
  setStatus(decision === "approve" ? "Approving" : "Rejecting");
  const path = `/api/approvals/${currentApprovalId}/${decision}`;
  const result = await api(path, {
    method: "POST",
    body: JSON.stringify({
      reviewer: "demo-user",
      reason: `${decision} from dashboard`,
    }),
  });
  renderList("approvalResult", [result], (item) => {
    return `${item.status}: ${item.tool_name} reviewed_by=${item.reviewer} reason=${item.decision_reason}`;
  });
  approveBtn.disabled = true;
  rejectBtn.disabled = true;
  setStatus("Ready");
}

runScenarioBtn.addEventListener("click", runScenario);
benchmarkBtn.addEventListener("click", runBenchmark);
highRiskBtn.addEventListener("click", runHighRiskDemo);
approveBtn.addEventListener("click", () => decideApproval("approve"));
rejectBtn.addEventListener("click", () => decideApproval("reject"));
