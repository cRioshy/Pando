const state = {
  graphTimer: null,
  learningReportTimer: null,
  graphView: "list",
  layoutCacheKey: "",
  learningGraph: null,
  layoutPositions: new Map(),
  manualPositions: new Map(),
  nodePositions: new Map(),
  selectedNodeId: null,
  hoveredNodeId: null,
  searchTimer: null,
  pollTimer: null,
  socket: null,
  statistics: null,
  storageLoading: false,
  dragNodeId: null,
  svgPan: { x: 0, y: 0 },
  svgZoom: 1,
};

const $ = (id) => document.getElementById(id);
const SVG_NS = "http://www.w3.org/2000/svg";
const GRAPH_NODE_LIMIT = 300;
const GRAPH_EDGE_LIMIT = 800;
const GRAPH_WIDTH = 1600;
const GRAPH_HEIGHT = 980;
const GRAPH_MARGIN = 70;
const GRAPH_MIN_ZOOM = 0.25;
const GRAPH_MAX_ZOOM = 4.0;
const GRAPH_COLORS = {
  MARKET: "#39d5ff",
  INDICATOR: "#4f8cff",
  PATTERN: "#ffad42",
  LEARNING: "#3ddc84",
  DECISION: "#b58cff",
  RESULT: "#f2f5f7",
  DATA_SOURCE: "#ffd75e",
  SYSTEM: "#b8c2cc",
};
const GRAPH_TYPES = ["MARKET", "INDICATOR", "PATTERN", "LEARNING", "DECISION", "RESULT", "DATA_SOURCE", "SYSTEM"];
const CLUSTER_ORDER = ["crypto", "stock", "brain", "system", "indicator", "pattern", "learning", "decision", "result", "unconnected"];

function runtime(seconds) {
  const value = Math.max(0, Math.floor(Number(seconds || 0)));
  const h = String(Math.floor(value / 3600)).padStart(2, "0");
  const m = String(Math.floor((value % 3600) / 60)).padStart(2, "0");
  const s = String(value % 60).padStart(2, "0");
  return `${h}:${m}:${s}`;
}

function time(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleTimeString();
}

function percent(value) {
  if (value === null || value === undefined || value === "") return "-";
  return `${Number(value).toFixed(2)} %`;
}

function price(value) {
  if (value === null || value === undefined || value === "") return "-";
  return Number(value).toLocaleString(undefined, { maximumFractionDigits: 4 });
}

function setText(id, value) {
  const node = $(id);
  if (!node) return;
  node.textContent = value === null || value === undefined || value === "" ? "-" : value;
}

function setConnection(text, cls) {
  const node = $("wsState");
  node.textContent = text;
  node.className = `pill ${cls || ""}`;
}

async function fetchJsonWithTimeout(url, timeoutMs = 8000) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, { cache: "no-store", signal: controller.signal });
    const data = await response.json();
    return { response, data };
  } finally {
    clearTimeout(timeout);
  }
}

function renderRows(containerId, rows, emptyText = "-") {
  const node = $(containerId);
  node.innerHTML = "";
  if (!rows.length) {
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.textContent = emptyText;
    node.appendChild(empty);
    return;
  }
  rows.forEach(([left, right]) => {
    const row = document.createElement("div");
    row.className = "row";
    row.innerHTML = `<strong></strong><span></span>`;
    row.children[0].textContent = left;
    row.children[1].textContent = right;
    node.appendChild(row);
  });
}

function renderMarket(tableId, analyses, options = {}) {
  const body = $(tableId);
  body.innerHTML = "";
  const entries = Object.entries(analyses || {});
  if (!entries.length) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td colspan="${options.crypto ? 9 : 5}" class="empty">Keine Live-Daten</td>`;
    body.appendChild(tr);
    return;
  }
  entries.sort(([a], [b]) => a.localeCompare(b)).forEach(([symbol, item]) => {
    const tr = document.createElement("tr");
    tr.innerHTML = options.crypto
      ? "<td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td>"
      : "<td></td><td></td><td></td><td></td><td></td>";
    tr.children[0].textContent = symbol;
    if (item.label && item.label !== symbol) {
      tr.children[0].textContent = `${item.label} (${symbol})`;
    }
    tr.children[1].textContent = item.direction || "-";
    tr.children[2].textContent = percent(item.probability);
    if (options.crypto) {
      tr.children[3].textContent = price(item.entry_price);
      tr.children[4].textContent = price(item.current_stop_loss);
      tr.children[5].textContent = price(item.take_profit_1);
      tr.children[6].textContent = percent(item.current_profit_percent);
      tr.children[7].textContent = price(item.price);
      tr.children[8].textContent = time(item.received_at);
    } else {
      tr.children[3].textContent = price(item.price);
      tr.children[4].textContent = time(item.price_timestamp || item.received_at);
    }
    body.appendChild(tr);
  });
}

function renderStatistics(statistics) {
  const analyses = (statistics && statistics.analyses) || {};
  const developer = (statistics && statistics.developer) || {};
  const trading = (statistics && statistics.trading) || {};

  setText("tradeAnalysesTotal", trading.analyses_total || 0);
  setText("tradeFinalLong", trading.final_long || 0);
  setText("tradeFinalShort", trading.final_short || 0);
  setText("tradeFinalHold", trading.final_hold || 0);
  setText("tradeWatchlist", trading.watchlist || 0);
  setText("tradeActiveMarkets", trading.active_markets ?? 0);
  setText("tradeLearnedPatterns", trading.learned_patterns ?? "-");
  setText("tradeHitRate", trading.hit_rate === null || trading.hit_rate === undefined ? "-" : percent(trading.hit_rate));
  setText("tradeSimOpen", trading.simulated_open_trades ?? 0);
  setText("tradeSimClosed", trading.simulated_closed_trades ?? 0);
  setText("tradeSimWins", trading.simulated_wins ?? 0);
  setText("tradeSimLosses", trading.simulated_losses ?? 0);
  setText(
    "tradeAvgOutcomeProfit",
    trading.average_outcome_profit_percent === null || trading.average_outcome_profit_percent === undefined
      ? "-"
      : percent(trading.average_outcome_profit_percent)
  );
  setText(
    "tradeAvgHolding",
    trading.average_holding_seconds === null || trading.average_holding_seconds === undefined
      ? "-"
      : runtime(trading.average_holding_seconds)
  );
  setText("tradeSuccessfulLearnings", trading.successful_learnings || 0);
  setText("tradeAvgConfidence", trading.average_confidence === null || trading.average_confidence === undefined ? "-" : percent(trading.average_confidence));
  setText(
    "tradeAvgAnalysisTime",
    trading.average_analysis_time_ms === null || trading.average_analysis_time_ms === undefined
      ? "-"
      : `${Number(trading.average_analysis_time_ms).toFixed(0)} ms`
  );

  setText("devAnalysisEvents", developer.analysis_events || 0);
  setText("devBrainUpdates", developer.brain_updates || 0);
  setText("devApiCalls", developer.api_calls || 0);
  setText("devDatabaseWrites", developer.database_writes || 0);
  setText("devRetries", developer.retry_events || 0);
  setText("devServiceErrors", developer.service_errors || 0);
  setText("devDataWarnings", developer.data_warnings || 0);
  setText("devUniqueErrors", developer.unique_error_types || 0);
  setText("devRepeatedErrors", developer.repeated_errors || 0);
  setText("devRuntime", runtime(developer.system_runtime_seconds || 0));
  setText("devCpu", developer.cpu_percent === null || developer.cpu_percent === undefined ? "-" : `${Number(developer.cpu_percent).toFixed(2)} %`);
  setText("devRam", developer.ram_mb === null || developer.ram_mb === undefined ? "-" : `${Number(developer.ram_mb).toFixed(2)} MB`);

  setText("statTotal", analyses.total || 0);
  setText("statCrypto", analyses.crypto || 0);
  setText("statStocks", analyses.stocks || 0);
  setText("statBrain", analyses.brain_evaluations || 0);
  setText("statDecisions", analyses.decisions || 0);
  setText("statSignals", analyses.signals || 0);
  setText("statLong", analyses.long || 0);
  setText("statShort", analyses.short || 0);
  setText("statHold", analyses.hold || 0);
  setText("statErrors", analyses.errors || 0);
  setText("statLearning", analyses.learning_updates || 0);
  setText("statTelegram", analyses.telegram_messages_sent || 0);
}

function metric(value, suffix = "") {
  if (value === null || value === undefined || value === "" || typeof value === "string") return value || "-";
  return `${Number(value).toFixed(2)}${suffix}`;
}

function renderTableRows(bodyId, rows, columns, emptyText = "Nicht genuegend Daten") {
  const body = $(bodyId);
  if (!body) return;
  body.innerHTML = "";
  if (!rows || !rows.length) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td colspan="${columns.length}" class="empty">${emptyText}</td>`;
    body.appendChild(tr);
    return;
  }
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = columns.map(() => "<td></td>").join("");
    columns.forEach((column, index) => {
      const value = typeof column === "function" ? column(row) : row[column];
      tr.children[index].textContent = value === null || value === undefined || value === "" ? "-" : value;
    });
    body.appendChild(tr);
  });
}

function renderLearningReport(report) {
  if (!report) return;
  const summary = report.summary || {};
  const score = report.learning_score || {};
  const progress = report.progress || {};

  setText("learningScore", score.score === undefined ? "-" : `${Number(score.score).toFixed(1)} / 100`);
  setText("learningHitRate", typeof summary.hit_rate === "number" ? percent(summary.hit_rate) : summary.hit_rate);
  setText("learningTrend", progress.verdict || "-");
  setText("learningConfidence", typeof summary.average_confidence === "number" ? percent(summary.average_confidence) : summary.average_confidence);
  setText(
    "learningProfit",
    typeof summary.average_profit_simulation === "number" ? percent(summary.average_profit_simulation) : summary.average_profit_simulation
  );
  setText("learningOutcomes", summary.learning_events_with_outcome ?? "-");
  setText("learningDecisions", summary.decisions ?? "-");
  setText("learningReportUpdated", time(report.generated_at));

  renderTableRows("learningWindowRows", report.windows || [], [
    "label",
    "decisions",
    (row) => row.long ?? 0,
    (row) => row.hold ?? 0,
    (row) => typeof row.hit_rate === "number" ? percent(row.hit_rate) : row.hit_rate,
    (row) => typeof row.average_confidence === "number" ? percent(row.average_confidence) : row.average_confidence,
    (row) => typeof row.average_profit_simulation === "number" ? percent(row.average_profit_simulation) : row.average_profit_simulation,
  ]);
  renderTableRows("learningConfidenceRows", report.confidence_quality || [], [
    "confidence",
    "sample_size",
    (row) => typeof row.actual_hit_rate === "number" ? percent(row.actual_hit_rate) : row.actual_hit_rate,
  ]);
  renderTableRows("learningMarketRows", report.market_comparison || [], [
    "market",
    "decisions",
    (row) => typeof row.hit_rate === "number" ? percent(row.hit_rate) : row.hit_rate,
    (row) => typeof row.average_confidence === "number" ? percent(row.average_confidence) : row.average_confidence,
    (row) => typeof row.average_profit === "number" ? percent(row.average_profit) : row.average_profit,
  ]);
  renderTableRows("learningSymbolRows", report.symbol_comparison || [], [
    "symbol",
    "decisions",
    (row) => typeof row.hit_rate === "number" ? percent(row.hit_rate) : row.hit_rate,
    (row) => typeof row.confidence === "number" ? percent(row.confidence) : row.confidence,
    (row) => typeof row.profit === "number" ? percent(row.profit) : row.profit,
  ]);
  renderTableRows("learningIndicatorRows", report.indicators || [], [
    "indicator",
    "used",
    "successful",
    (row) => typeof row.hit_rate === "number" ? percent(row.hit_rate) : row.hit_rate,
  ]);

  const notes = [];
  (report.warnings || []).forEach((item) => notes.push(["Warnung", item]));
  (report.recommendations || []).slice(0, 6).forEach((item) => notes.push(["Empfehlung", item]));
  renderRows("learningReportNotes", notes, "Keine Hinweise");
}

function renderStorage(storage) {
  const body = $("storageRows");
  body.innerHTML = "";
  const scan = (storage && storage.scan) || {};
  const scanStatus = scan.status || (storage && storage.scan_status) || "IDLE";
  const completed = scan.files_total ? ` ${scan.files_completed || 0}/${scan.files_total} Dateien` : "";
  const duration = scan.duration_seconds != null ? ` | ${scan.duration_seconds}s` : "";
  const scanElement = $("storageScanStatus");
  if (scanElement) {
    scanElement.textContent = `Scan: ${scanStatus}${completed}${duration}`;
  }
  const folders = (storage && storage.folders) || [];
  if (!folders.length) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td colspan="6" class="empty">Keine Datenspeicher-Metadaten</td>`;
    body.appendChild(tr);
    return;
  }
  folders.forEach((folder) => {
    const tr = document.createElement("tr");
    tr.className = "clickable";
    tr.dataset.folder = folder.name;
    tr.innerHTML = "<td></td><td></td><td></td><td></td><td></td><td></td>";
    tr.children[0].textContent = folder.name;
    tr.children[1].textContent = folder.file_count ?? 0;
    tr.children[2].textContent = folder.record_count ?? "-";
    tr.children[3].textContent = folder.total_size_human || "-";
    tr.children[4].textContent = time(folder.last_modified_at);
    tr.children[5].textContent = folder.status || "-";
    tr.addEventListener("click", () => loadStorageFolder(folder.name));
    body.appendChild(tr);
  });
}

async function loadStorageSnapshot() {
  if (state.storageLoading) return;
  state.storageLoading = true;
  try {
    const response = await fetch("/api/statistics/storage", { cache: "no-store" });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Storage load failed");
    renderStorage(data.storage);
  } finally {
    state.storageLoading = false;
  }
}

function renderStorageDetails(folder) {
  const details = $("storageDetails");
  const files = (folder && folder.files) || [];
  if (!folder) {
    details.innerHTML = "";
    return;
  }
  const rows = files.map((file) => `
    <tr>
      <td>${escapeHtml(file.relative_path || file.name)}</td>
      <td>${escapeHtml(file.file_type || "-")}</td>
      <td>${escapeHtml(file.size_human || "-")}</td>
      <td>${file.record_count ?? file.log_lines ?? "-"}</td>
      <td>${time(file.modified_at)}</td>
      <td>${escapeHtml(file.status || "-")}</td>
    </tr>
  `).join("");
  details.innerHTML = `
    <h2>${escapeHtml(folder.name)}</h2>
    <table>
      <thead><tr><th>Datei</th><th>Typ</th><th>Größe</th><th>Datensätze</th><th>Letzte Änderung</th><th>Status</th></tr></thead>
      <tbody>${rows || `<tr><td colspan="6" class="empty">Keine Dateien</td></tr>`}</tbody>
    </table>
  `;
}

function renderLearningGraph(graph) {
  state.learningGraph = graph || state.learningGraph || {};
  const current = state.learningGraph || {};
  const stats = current.stats || {};
  const nodes = current.nodes || [];
  const edges = current.edges || [];

  $("graphNodeCount").textContent = stats.visible_nodes ?? nodes.length;
  $("graphEdgeCount").textContent = stats.visible_edges ?? edges.length;
  $("graphAnalyses").textContent = stats.analyses_processed ?? 0;
  $("graphPatterns").textContent = stats.patterns_recognized ?? 0;
  $("graphLearningsToday").textContent = stats.new_learnings_today ?? 0;
  $("graphMarkets").textContent = stats.active_markets ?? 0;
  $("graphStatus").textContent = stats.system_status || "-";
  $("graphUpdated").textContent = time(stats.last_update);

  renderLearningGraphNodes(nodes);
  renderLearningGraphEdges(edges);
  renderGraphLegend();
  if (state.selectedNodeId) {
    const selected = nodes.find((node) => node.id === state.selectedNodeId);
    renderLearningGraphDetails(selected || null);
  }
  renderLearningGraphNetwork();
}

function renderLearningGraphNodes(nodes) {
  const container = $("learningGraphNodes");
  container.innerHTML = "";
  if (!nodes.length) {
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.textContent = "Noch keine Lernknoten";
    container.appendChild(empty);
    return;
  }

  nodes.slice(0, 80).forEach((node) => {
    const button = document.createElement("button");
    button.className = "graph-item";
    button.type = "button";
    button.innerHTML = "<strong></strong><span></span><small></small>";
    button.children[0].textContent = node.label || node.id || "-";
    button.children[1].textContent = [node.type, node.market, node.public_result]
      .filter(Boolean)
      .join(" | ");
    button.children[2].textContent = node.last_seen ? `zuletzt ${time(node.last_seen)}` : node.id || "";
    button.addEventListener("click", () => loadLearningGraphNode(node.id));
    container.appendChild(button);
  });
}

function renderLearningGraphEdges(edges) {
  const container = $("learningGraphEdges");
  container.innerHTML = "";
  if (!edges.length) {
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.textContent = "Noch keine Verbindungen";
    container.appendChild(empty);
    return;
  }

  edges.slice(0, 80).forEach((edge) => {
    const item = document.createElement("div");
    item.className = "graph-item";
    item.innerHTML = "<strong></strong><span></span><small></small>";
    item.children[0].textContent = edge.label || edge.type || "-";
    item.children[1].textContent = `${edge.source || "-"} -> ${edge.target || "-"}`;
    item.children[2].textContent = `Anzahl ${edge.count ?? 1} | ${edge.status || "OBSERVED"}`;
    container.appendChild(item);
  });
}

function setLearningGraphView(view) {
  state.graphView = view === "graph" ? "graph" : "list";
  $("learningGraphListView").classList.toggle("hidden", state.graphView !== "list");
  $("learningGraphGraphView").classList.toggle("hidden", state.graphView !== "graph");
  document.querySelectorAll("[data-graph-view]").forEach((button) => {
    const active = button.dataset.graphView === state.graphView;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });
  if (state.graphView === "graph") {
    renderLearningGraphNetwork();
  }
}

function visibleGraphData() {
  const graph = state.learningGraph || {};
  const nodes = dedupeById((graph.nodes || []).slice(0, GRAPH_NODE_LIMIT));
  const nodeIds = new Set(nodes.map((node) => node.id));
  const edges = dedupeById((graph.edges || [])
    .filter((edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target))
    .slice(0, GRAPH_EDGE_LIMIT));
  return { nodes, edges, totalNodes: (graph.nodes || []).length };
}

function dedupeById(items) {
  const seen = new Set();
  const result = [];
  items.forEach((item) => {
    if (!item || !item.id || seen.has(item.id)) return;
    seen.add(item.id);
    result.push(item);
  });
  return result;
}

function renderLearningGraphNetwork() {
  const svg = $("learningGraphSvg");
  if (!svg || state.graphView !== "graph") return;
  const { nodes, edges, totalNodes } = visibleGraphData();
  svg.innerHTML = "";
  svg.setAttribute("viewBox", `${state.svgPan.x} ${state.svgPan.y} ${GRAPH_WIDTH / state.svgZoom} ${GRAPH_HEIGHT / state.svgZoom}`);
  $("learningGraphLimitNotice").textContent =
    totalNodes > nodes.length ? `Showing the most relevant ${nodes.length} of ${totalNodes} nodes.` : "";

  if (!nodes.length) {
    const text = svgElement("text", { x: 500, y: 325, "text-anchor": "middle", fill: "#9aa8b2" });
    text.textContent = "Keine Graph-Daten";
    svg.appendChild(text);
    return;
  }

  const positions = layoutGraph(nodes, edges);
  state.nodePositions = positions;
  const activeNodeId = state.selectedNodeId || state.hoveredNodeId;
  const neighborIds = selectedNeighborIds(edges, activeNodeId);
  const neighborEdgeIds = selectedNeighborEdgeIds(edges, activeNodeId);
  const edgeLayer = svgElement("g", {});
  const clusterLayer = svgElement("g", { class: "graph-clusters" });
  const nodeLayer = svgElement("g", {});
  svg.appendChild(clusterLayer);
  svg.appendChild(edgeLayer);
  svg.appendChild(nodeLayer);

  renderClusterLabels(clusterLayer, nodes, edges);

  edges.forEach((edge) => {
    const source = positions.get(edge.source);
    const target = positions.get(edge.target);
    if (!source || !target) return;
    const line = svgElement("line", {
      class: graphEdgeClass(edge, neighborEdgeIds),
      x1: source.x,
      y1: source.y,
      x2: target.x,
      y2: target.y,
      "stroke-width": edgeWidth(edge),
    });
    edgeLayer.appendChild(line);
  });

  nodes.forEach((node) => {
    const position = positions.get(node.id);
    if (!position) return;
    const group = svgElement("g", {
      class: graphNodeClass(node, neighborIds),
      transform: `translate(${position.x} ${position.y})`,
      tabindex: "0",
      role: "button",
      "aria-label": `${node.label || node.id} ${node.type || ""}`,
    });
    group.dataset.nodeId = node.id;
    group.classList.add("entering");
    group.addEventListener("mouseenter", () => {
      state.hoveredNodeId = node.id;
      renderLearningGraphNetwork();
    });
    group.addEventListener("mouseleave", () => {
      state.hoveredNodeId = null;
      renderLearningGraphNetwork();
    });
    group.addEventListener("click", (event) => {
      event.stopPropagation();
      selectLearningGraphNode(node.id);
    });
    group.addEventListener("dblclick", (event) => {
      event.stopPropagation();
      focusLearningGraphNode(node.id);
    });
    group.addEventListener("pointerdown", (event) => startNodeDrag(event, node.id));
    group.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        selectLearningGraphNode(node.id);
      }
    });

    const circle = svgElement("circle", {
      r: nodeRadius(node),
      fill: GRAPH_COLORS[node.type] || "#b8c2cc",
    });
    group.appendChild(circle);
    const labelText = displayNodeLabel(node);
    const showLabel = shouldShowNodeLabel(node, neighborIds);
    if (showLabel) {
      const labelY = labelOffset(node, position);
      const labelWidth = Math.max(42, labelText.length * 7 + 16);
      const labelBg = svgElement("rect", {
        class: "graph-label-bg",
        x: -labelWidth / 2,
        y: labelY - 15,
        width: labelWidth,
        height: 22,
        rx: 6,
      });
      const label = svgElement("text", {
        y: labelY,
        "text-anchor": "middle",
      });
      label.textContent = labelText;
      group.appendChild(labelBg);
      group.appendChild(label);
    }
    const title = svgElement("title", {});
    title.textContent = String(node.label || node.id || "-");
    group.appendChild(title);
    nodeLayer.appendChild(group);
  });
}

function layoutGraph(nodes, edges) {
  const cacheKey = nodes.map((node) => node.id).join("|") + "::" + edges.map((edge) => edge.id).join("|");
  if (state.layoutCacheKey !== cacheKey) {
    state.layoutCacheKey = cacheKey;
    keepCurrentGraphPositions(nodes);
  }
  const positions = initializeGraphPositions(nodes, edges);
  runForceSimulation(positions, nodes, edges);
  relaxGraphCollisions(positions, nodes);
  boundGraphPositions(positions, nodes);
  state.layoutPositions = new Map(positions);
  return positions;
}

function clusterKey(node) {
  const type = String(node.type || "").toUpperCase();
  const market = String(node.market || "").toLowerCase();
  const label = String(node.label || node.id || "").toLowerCase();
  if (market === "crypto" || label.includes("btcusdt") || label.includes("ethusdt") || label.includes("xrpusdt")) return "crypto";
  if (market === "stock" || label.includes("aapl") || label.includes("msft") || label.includes("nvda") || label.includes("tsla") || label.includes("spcx")) return "stock";
  if (type === "LEARNING" || label.includes("learning") || label.includes("brain")) return "brain";
  if (type === "INDICATOR") return "indicator";
  if (type === "PATTERN") return "pattern";
  if (type === "DECISION") return "decision";
  if (type === "RESULT") return "result";
  if (type === "DATA_SOURCE" || type === "SYSTEM") return "system";
  return "system";
}

function clusterCenters() {
  return {
    crypto: { x: 250, y: 310 },
    stock: { x: 1350, y: 310 },
    brain: { x: 800, y: 500 },
    system: { x: 800, y: 165 },
    indicator: { x: 800, y: 790 },
    pattern: { x: 470, y: 720 },
    learning: { x: 800, y: 625 },
    decision: { x: 1110, y: 720 },
    result: { x: 1340, y: 790 },
    unconnected: { x: 245, y: 825 },
  };
}

function keepCurrentGraphPositions(nodes) {
  const allowedIds = new Set(nodes.map((node) => node.id));
  state.layoutPositions = new Map(
    Array.from(state.layoutPositions.entries()).filter(([id]) => allowedIds.has(id))
  );
  state.manualPositions = new Map(
    Array.from(state.manualPositions.entries()).filter(([id]) => allowedIds.has(id))
  );
}

function initializeGraphPositions(nodes, edges) {
  const connectedIds = connectedNodeIds(edges);
  const centers = clusterCenters();
  const clusterIndexes = new Map();
  const positions = new Map();
  nodes.forEach((node) => {
    const manual = state.manualPositions.get(node.id);
    if (manual) {
      positions.set(node.id, { x: manual.x, y: manual.y });
      return;
    }
    const cached = state.layoutPositions.get(node.id);
    if (cached) {
      positions.set(node.id, { x: cached.x, y: cached.y });
      return;
    }
    const key = connectedIds.has(node.id) ? clusterKey(node) : "unconnected";
    const center = centers[key] || centers.system;
    const index = clusterIndexes.get(key) || 0;
    clusterIndexes.set(key, index + 1);
    const angle = seededAngle(node.id, index);
    const radius = 40 + Math.floor(index / 7) * 54 + (index % 7) * 8;
    positions.set(node.id, {
      x: clamp(center.x + Math.cos(angle) * radius, GRAPH_MARGIN, GRAPH_WIDTH - GRAPH_MARGIN),
      y: clamp(center.y + Math.sin(angle) * radius, GRAPH_MARGIN, GRAPH_HEIGHT - GRAPH_MARGIN),
    });
  });
  return positions;
}

function runForceSimulation(positions, nodes, edges) {
  const centers = clusterCenters();
  const connectedIds = connectedNodeIds(edges);
  const nodeById = new Map(nodes.map((node) => [node.id, node]));
  const iterations = nodes.length > 160 ? 55 : 90;
  for (let step = 0; step < iterations; step += 1) {
    const cooling = 1 - step / iterations;
    const forces = new Map(nodes.map((node) => [node.id, { x: 0, y: 0 }]));

    for (let i = 0; i < nodes.length; i += 1) {
      for (let j = i + 1; j < nodes.length; j += 1) {
        const aNode = nodes[i];
        const bNode = nodes[j];
        const a = positions.get(aNode.id);
        const b = positions.get(bNode.id);
        if (!a || !b) continue;
        let dx = b.x - a.x;
        let dy = b.y - a.y;
        let distance = Math.hypot(dx, dy);
        if (distance < 0.01) {
          const angle = seededAngle(`${aNode.id}:${bNode.id}`, j);
          dx = Math.cos(angle);
          dy = Math.sin(angle);
          distance = 1;
        }
        const sameCluster = clusterKey(aNode) === clusterKey(bNode);
        const desired = nodeRadius(aNode) + nodeRadius(bNode) + (sameCluster ? 82 : 128);
        const strength = Math.min(5.5, (desired * desired) / Math.max(80, distance * distance));
        const ux = dx / distance;
        const uy = dy / distance;
        forces.get(aNode.id).x -= ux * strength;
        forces.get(aNode.id).y -= uy * strength;
        forces.get(bNode.id).x += ux * strength;
        forces.get(bNode.id).y += uy * strength;
      }
    }

    edges.forEach((edge) => {
      const sourceNode = nodeById.get(edge.source);
      const targetNode = nodeById.get(edge.target);
      const source = positions.get(edge.source);
      const target = positions.get(edge.target);
      if (!sourceNode || !targetNode || !source || !target) return;
      const dx = target.x - source.x;
      const dy = target.y - source.y;
      const distance = Math.max(1, Math.hypot(dx, dy));
      const sameCluster = clusterKey(sourceNode) === clusterKey(targetNode);
      const ideal = sameCluster ? 185 : 300;
      const pull = clamp((distance - ideal) * 0.012, -3.5, 3.5);
      const ux = dx / distance;
      const uy = dy / distance;
      forces.get(edge.source).x += ux * pull;
      forces.get(edge.source).y += uy * pull;
      forces.get(edge.target).x -= ux * pull;
      forces.get(edge.target).y -= uy * pull;
    });

    nodes.forEach((node) => {
      const position = positions.get(node.id);
      const force = forces.get(node.id);
      if (!position || !force || state.manualPositions.has(node.id)) return;
      const key = connectedIds.has(node.id) ? clusterKey(node) : "unconnected";
      const center = centers[key] || centers.system;
      force.x += (center.x - position.x) * (key === "unconnected" ? 0.028 : 0.018);
      force.y += (center.y - position.y) * (key === "unconnected" ? 0.028 : 0.018);
      force.x += (GRAPH_WIDTH / 2 - position.x) * 0.002;
      force.y += (GRAPH_HEIGHT / 2 - position.y) * 0.002;
      position.x = clamp(position.x + force.x * cooling, GRAPH_MARGIN, GRAPH_WIDTH - GRAPH_MARGIN);
      position.y = clamp(position.y + force.y * cooling, GRAPH_MARGIN, GRAPH_HEIGHT - GRAPH_MARGIN);
    });
  }
}

function connectedNodeIds(edges) {
  const ids = new Set();
  edges.forEach((edge) => {
    ids.add(edge.source);
    ids.add(edge.target);
  });
  return ids;
}

function seededAngle(id, index) {
  let hash = 0;
  String(id).split("").forEach((char) => {
    hash = (hash * 31 + char.charCodeAt(0)) >>> 0;
  });
  return ((hash % 360) / 180) * Math.PI + index * 0.47;
}

function nodeSortScore(node) {
  return Number(node.activity_count || node.analysis_count || node.similar_cases || 1);
}

function relaxGraphCollisions(positions, nodes) {
  const ids = nodes.map((node) => node.id).filter((id) => positions.has(id));
  const nodeById = new Map(nodes.map((node) => [node.id, node]));
  for (let pass = 0; pass < 16; pass += 1) {
    for (let i = 0; i < ids.length; i += 1) {
      for (let j = i + 1; j < ids.length; j += 1) {
        const a = positions.get(ids[i]);
        const b = positions.get(ids[j]);
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const distance = Math.max(1, Math.hypot(dx, dy));
        const minDistance = nodeRadius(nodeById.get(ids[i])) + nodeRadius(nodeById.get(ids[j])) + 54;
        if (distance >= minDistance) continue;
        const push = (minDistance - distance) / 2;
        const ux = dx / distance;
        const uy = dy / distance;
        if (!state.manualPositions.has(ids[i])) {
          a.x = clamp(a.x - ux * push, GRAPH_MARGIN, GRAPH_WIDTH - GRAPH_MARGIN);
          a.y = clamp(a.y - uy * push, GRAPH_MARGIN, GRAPH_HEIGHT - GRAPH_MARGIN);
        }
        if (!state.manualPositions.has(ids[j])) {
          b.x = clamp(b.x + ux * push, GRAPH_MARGIN, GRAPH_WIDTH - GRAPH_MARGIN);
          b.y = clamp(b.y + uy * push, GRAPH_MARGIN, GRAPH_HEIGHT - GRAPH_MARGIN);
        }
      }
    }
  }
}

function boundGraphPositions(positions, nodes) {
  nodes.forEach((node) => {
    const position = positions.get(node.id);
    if (!position) return;
    const radius = nodeRadius(node) + 14;
    position.x = clamp(position.x, GRAPH_MARGIN + radius, GRAPH_WIDTH - GRAPH_MARGIN - radius);
    position.y = clamp(position.y, GRAPH_MARGIN + radius, GRAPH_HEIGHT - GRAPH_MARGIN - radius);
  });
}

function renderClusterLabels(layer, nodes, edges) {
  const present = new Set(nodes.map((node) => clusterKey(node)));
  const connectedIds = connectedNodeIds(edges);
  if (nodes.some((node) => !connectedIds.has(node.id))) present.add("unconnected");
  const centers = clusterCenters();
  const labels = {
    crypto: "Crypto",
    stock: "Stocks",
    brain: "Brain",
    system: "System",
    indicator: "Indicators",
    pattern: "Patterns",
    learning: "Learnings",
    decision: "Decisions",
    result: "Results",
    unconnected: "Unconnected",
  };
  Array.from(present).forEach((key) => {
    const center = centers[key];
    if (!center) return;
    const text = svgElement("text", {
      class: "graph-cluster-label",
      x: center.x,
      y: center.y - 112,
      "text-anchor": "middle",
    });
    text.textContent = labels[key] || key;
    layer.appendChild(text);
  });
}

function labelOffset(node, position) {
  const radius = nodeRadius(node);
  const stagger = Math.round((position.x + position.y) % 3) * 10;
  return radius + 20 + stagger;
}

function displayNodeLabel(node) {
  const label = String(node.label || node.id || "-");
  const cleaned = label
    .replace(/^Connected To Source$/i, "Source")
    .replace(/^([A-Z]+USDT)\s+Pattern\s+/i, "Pattern ")
    .replace(/^([A-Z]+)\s+Pattern\s+/i, "Pattern ");
  return cleaned.length > 18 ? `${cleaned.slice(0, 16)}...` : cleaned;
}

function shouldShowNodeLabel(node, neighborIds) {
  const type = String(node.type || "").toUpperCase();
  if (type === "MARKET" || type === "SYSTEM") return true;
  if (state.svgZoom >= 1.35) return true;
  if (state.selectedNodeId === node.id || state.hoveredNodeId === node.id) return true;
  return state.selectedNodeId && neighborIds.has(node.id) && state.svgZoom >= 0.95;
}

function selectedNeighborIds(edges, selectedId) {
  const ids = new Set();
  if (!selectedId) return ids;
  ids.add(selectedId);
  edges.forEach((edge) => {
    if (edge.source === selectedId) ids.add(edge.target);
    if (edge.target === selectedId) ids.add(edge.source);
  });
  return ids;
}

function selectedNeighborEdgeIds(edges, selectedId) {
  const ids = new Set();
  if (!selectedId) return ids;
  edges.forEach((edge) => {
    if (edge.source === selectedId || edge.target === selectedId) ids.add(edge.id);
  });
  return ids;
}

function graphNodeClass(node, neighborIds) {
  const classes = ["graph-node"];
  if (state.selectedNodeId === node.id) classes.push("selected");
  if (neighborIds.has(node.id) && state.selectedNodeId !== node.id) classes.push("neighbor");
  if (state.selectedNodeId && !neighborIds.has(node.id)) classes.push("dim");
  return classes.join(" ");
}

function graphEdgeClass(edge, neighborEdgeIds) {
  if (!state.selectedNodeId) return "graph-edge";
  return neighborEdgeIds.has(edge.id) ? "graph-edge neighbor" : "graph-edge dim";
}

function nodeRadius(node) {
  const type = String(node && node.type || "").toUpperCase();
  const activity = Number((node && (node.activity_count || node.analysis_count || node.similar_cases)) || 1);
  const baseByType = {
    MARKET: [28, 44],
    SYSTEM: [24, 36],
    PATTERN: [18, 30],
    LEARNING: [16, 26],
    INDICATOR: [14, 22],
    DECISION: [14, 22],
    RESULT: [14, 22],
    DATA_SOURCE: [16, 24],
  };
  const range = baseByType[type] || [16, 26];
  return clamp(range[0] + Math.sqrt(Math.max(1, activity)) * 1.8, range[0], range[1]);
}

function edgeWidth(edge) {
  return clamp(0.65 + Math.log10(Number(edge.count || 1) + 1) * 0.55, 0.65, 1.4);
}

function selectLearningGraphNode(nodeId) {
  state.selectedNodeId = nodeId;
  const node = ((state.learningGraph && state.learningGraph.nodes) || []).find((item) => item.id === nodeId);
  renderLearningGraphDetails(node);
  renderLearningGraphNetwork();
}

function focusLearningGraphNode(nodeId) {
  selectLearningGraphNode(nodeId);
  const position = state.nodePositions.get(nodeId);
  if (!position) return;
  state.svgZoom = 1.7;
  state.svgPan = {
    x: position.x - GRAPH_WIDTH / (2 * state.svgZoom),
    y: position.y - GRAPH_HEIGHT / (2 * state.svgZoom),
  };
  renderLearningGraphNetwork();
}

function searchLearningGraph() {
  const query = $("learningGraphSearch").value.trim().toLowerCase();
  const status = $("learningGraphSearchStatus");
  if (!query) {
    status.textContent = "-";
    return;
  }
  const nodes = ((state.learningGraph && state.learningGraph.nodes) || []);
  const match = nodes.find((node) => {
    const text = [node.id, node.label, node.type, node.market, node.public_result]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    return text.includes(query);
  });
  if (!match) {
    status.textContent = "Kein Treffer";
    return;
  }
  status.textContent = match.label || match.id;
  setLearningGraphView("graph");
  focusLearningGraphNode(match.id);
}

function resetLearningGraphView() {
  state.selectedNodeId = null;
  state.hoveredNodeId = null;
  state.svgPan = { x: 0, y: 0 };
  state.svgZoom = 1;
  state.layoutPositions = new Map();
  state.manualPositions = new Map();
  renderLearningGraphDetails(null);
  renderLearningGraphNetwork();
  fitLearningGraphView();
}

function fitLearningGraphView() {
  const positions = Array.from(state.nodePositions.values());
  if (!positions.length) {
    state.svgPan = { x: 0, y: 0 };
    state.svgZoom = 1;
    renderLearningGraphNetwork();
    return;
  }
  const minX = Math.min(...positions.map((point) => point.x)) - 90;
  const maxX = Math.max(...positions.map((point) => point.x)) + 90;
  const minY = Math.min(...positions.map((point) => point.y)) - 90;
  const maxY = Math.max(...positions.map((point) => point.y)) + 90;
  const width = Math.max(1, maxX - minX);
  const height = Math.max(1, maxY - minY);
  state.svgZoom = clamp(Math.min(GRAPH_WIDTH / width, GRAPH_HEIGHT / height), 0.45, 1.8);
  state.svgPan = { x: minX, y: minY };
  renderLearningGraphNetwork();
}

function renderGraphLegend() {
  const legend = $("learningGraphLegend");
  if (!legend || legend.dataset.rendered === "true") return;
  legend.innerHTML = "";
  GRAPH_TYPES.forEach((type) => {
    const row = document.createElement("div");
    row.className = "legend-row";
    row.innerHTML = "<span class=\"legend-dot\"></span><span></span>";
    row.children[0].style.background = GRAPH_COLORS[type] || "#b8c2cc";
    row.children[1].textContent = type;
    legend.appendChild(row);
  });
  legend.dataset.rendered = "true";
}

function svgElement(name, attributes) {
  const node = document.createElementNS(SVG_NS, name);
  Object.entries(attributes || {}).forEach(([key, value]) => node.setAttribute(key, String(value)));
  return node;
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function graphPointFromEvent(event) {
  const svg = $("learningGraphSvg");
  const rect = svg.getBoundingClientRect();
  const viewWidth = GRAPH_WIDTH / state.svgZoom;
  const viewHeight = GRAPH_HEIGHT / state.svgZoom;
  return {
    x: state.svgPan.x + ((event.clientX - rect.left) / Math.max(1, rect.width)) * viewWidth,
    y: state.svgPan.y + ((event.clientY - rect.top) / Math.max(1, rect.height)) * viewHeight,
  };
}

function startNodeDrag(event, nodeId) {
  event.preventDefault();
  event.stopPropagation();
  state.dragNodeId = nodeId;
  state.selectedNodeId = nodeId;
  const point = graphPointFromEvent(event);
  state.manualPositions.set(nodeId, point);
  const svg = $("learningGraphSvg");
  try {
    svg.setPointerCapture(event.pointerId);
  } catch (error) {
    // Pointer capture may not be available for every synthetic event.
  }
  renderLearningGraphNetwork();
}

function updateNodeDrag(event) {
  if (!state.dragNodeId) return false;
  const point = graphPointFromEvent(event);
  state.manualPositions.set(state.dragNodeId, {
    x: clamp(point.x, GRAPH_MARGIN, GRAPH_WIDTH - GRAPH_MARGIN),
    y: clamp(point.y, GRAPH_MARGIN, GRAPH_HEIGHT - GRAPH_MARGIN),
  });
  renderLearningGraphDetails(((state.learningGraph && state.learningGraph.nodes) || []).find((node) => node.id === state.dragNodeId));
  renderLearningGraphNetwork();
  return true;
}

function stopNodeDrag(event) {
  if (!state.dragNodeId) return false;
  const svg = $("learningGraphSvg");
  try {
    svg.releasePointerCapture(event.pointerId);
  } catch (error) {
    // Pointer capture may already be released.
  }
  state.dragNodeId = null;
  return true;
}

function renderLearningGraphDetails(node) {
  const details = $("learningGraphDetails");
  if (!node) {
    details.className = "details empty";
    details.textContent = "Noch kein Knoten ausgewaehlt";
    return;
  }

  details.className = "details";
  const rows = [
    ["ID", node.id],
    ["Name", node.label],
    ["Typ", node.type],
    ["Status", node.status],
    ["Markt", node.market],
    ["Zeit", time(node.timestamp || node.last_seen)],
    ["Datenqualitaet", node.data_quality],
    ["Confidence", node.public_confidence],
    ["Ergebnis", node.public_result],
    ["Aehnliche Faelle", node.similar_cases],
    ["Aktivitaet", node.activity_count],
  ].filter(([, value]) => value !== null && value !== undefined && value !== "");

  details.innerHTML = `
    <div class="graph-detail-grid">
      ${rows.map(([label, value]) => `<span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong>`).join("")}
    </div>
  `;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function render(snapshot) {
  if (!snapshot) return;
  const statistics = snapshot.statistics || state.statistics;
  if (snapshot.statistics) {
    state.statistics = snapshot.statistics;
  }
  $("health").textContent = snapshot.platform_health || "PENDING";
  $("runtime").textContent = runtime(snapshot.runtime_seconds);
  $("events").textContent = snapshot.events_received || 0;
  $("errors").textContent = snapshot.error_count || 0;
  $("queue").textContent = snapshot.event_bus_queue_size || 0;
  $("lastUpdate").textContent = `Update ${time(snapshot.last_update_at)}`;

  const serviceStatus = snapshot.service_status || {};
  const heartbeats = snapshot.service_heartbeats || {};
  const serviceRows = Object.keys(serviceStatus).sort().map((name) => [
    name,
    `${serviceStatus[name]} | Heartbeat ${time(heartbeats[name])}`,
  ]);
  renderRows("services", serviceRows, "Keine Services");

  renderMarket("cryptoRows", snapshot.last_crypto_analysis || {}, { crypto: true });
  renderMarket("stockRows", snapshot.last_stock_analysis || {});
  renderMarket("commodityRows", snapshot.last_commodity_analysis || {});

  const brain = snapshot.last_brain_decision || {};
  const learning = snapshot.last_learning_update || {};
  $("brainDecision").textContent = brain.symbol ? `${brain.symbol} ${brain.direction || ""}` : "-";
  $("brainConfidence").textContent = percent(brain.probability || brain.confidence);
  $("brainLearning").textContent = learning.updates || learning.status || "-";

  const telegram = snapshot.telegram_status || {};
  $("telegramEnabled").textContent = String(telegram.enabled ?? false);
  $("telegramDryRun").textContent = String(telegram.dry_run ?? true);
  $("telegramReady").textContent = telegram.messages_ready || 0;

  renderStatistics(statistics);
  if (statistics && statistics.storage) {
    loadStorageSnapshot().catch(() => {});
  }
  if (state.learningGraph) {
    renderLearningGraph(state.learningGraph);
  }

  const events = snapshot.latest_events || [];
  renderRows(
    "signals",
    events
      .filter((event) => String(event.topic).includes("SIGNAL") || String(event.topic).includes("DECISION"))
      .slice(-8)
      .map((event) => [event.topic, `${event.source} | ${time(event.created_at)}`]),
    "Keine fertigen Signale"
  );
  renderRows(
    "errorRows",
    events
      .filter((event) => String(event.topic).toUpperCase().includes("ERROR"))
      .slice(-8)
      .map((event) => [event.topic, `${event.source} | ${time(event.created_at)}`]),
    "Keine Fehler"
  );
}

async function loadLearningGraph() {
  const response = await fetch("/api/v1/learning-graph", { cache: "no-store" });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Learning graph failed");
  renderLearningGraph(data.learning_graph);
}

async function loadLearningReport() {
  const { response, data } = await fetchJsonWithTimeout("/api/learning-report", 8000);
  if (!response.ok) throw new Error(data.error || "Learning report failed");
  renderLearningReport(data.learning_report);
}

async function loadStatistics() {
  const response = await fetch("/api/statistics", { cache: "no-store" });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Statistics failed");
  state.statistics = data;
  renderStatistics(data);
  if (data.storage) {
    await loadStorageSnapshot();
  }
}

async function loadLearningGraphNode(nodeId) {
  if (!nodeId) return;
  const response = await fetch(`/api/v1/learning-graph/node/${encodeURIComponent(nodeId)}`, { cache: "no-store" });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Learning graph node failed");
  state.selectedNodeId = nodeId;
  renderLearningGraphDetails(data.node);
  renderLearningGraphNetwork();
}

async function loadStorageFolder(folderName) {
  const response = await fetch(`/api/statistics/storage/${encodeURIComponent(folderName)}`, { cache: "no-store" });
  const data = await response.json();
  if (response.ok) {
    renderStorageDetails(data.folder);
  }
}

async function poll() {
  try {
    const response = await fetch("/api/status", { cache: "no-store" });
    render(await response.json());
  } catch (error) {
    setConnection("Polling Fehler", "bad");
  }
}

function connectWebSocket() {
  const protocol = location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${protocol}://${location.host}/ws/live`);
  state.socket = socket;

  socket.addEventListener("open", () => {
    setConnection("WebSocket", "ok");
    if (state.pollTimer) clearInterval(state.pollTimer);
  });
  socket.addEventListener("message", (message) => {
    const data = JSON.parse(message.data);
    if (data.event && data.event.topic === "STATISTICS_UPDATED" && data.payload) {
      state.statistics = data.payload;
    }
    render(data.snapshot);
  });
  socket.addEventListener("close", () => {
    setConnection("Polling", "");
    state.pollTimer = setInterval(poll, 1000);
  });
  socket.addEventListener("error", () => {
    setConnection("Polling", "");
  });
}

async function control(action) {
  const response = await fetch(`/api/control/${action}`, { method: "POST" });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Control command failed");
  await poll();
}

async function refreshStorage() {
  const button = $("refreshStorage");
  button.disabled = true;
  try {
    const response = await fetch("/api/statistics/storage/refresh", { method: "POST" });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Storage refresh failed");
    renderStorage(data.storage);
    await poll();
  } finally {
    button.disabled = false;
  }
}

async function refreshLearningGraph() {
  const button = $("refreshLearningGraph");
  button.disabled = true;
  try {
    await loadLearningGraph();
  } finally {
    button.disabled = false;
  }
}

async function refreshLearningReport() {
  const button = $("refreshLearningReport");
  button.disabled = true;
  try {
    await loadLearningReport();
  } finally {
    button.disabled = false;
  }
}

document.querySelectorAll("[data-action]").forEach((button) => {
  button.addEventListener("click", async () => {
    button.disabled = true;
    try {
      await control(button.dataset.action);
    } catch (error) {
      alert(error.message);
    } finally {
      button.disabled = false;
    }
  });
});

$("refreshStorage").addEventListener("click", () => {
  refreshStorage().catch((error) => alert(error.message));
});

$("refreshLearningGraph").addEventListener("click", () => {
  refreshLearningGraph().catch((error) => alert(error.message));
});

$("refreshLearningReport").addEventListener("click", () => {
  refreshLearningReport().catch((error) => alert(error.message));
});

document.querySelectorAll("[data-graph-view]").forEach((button) => {
  button.addEventListener("click", () => setLearningGraphView(button.dataset.graphView));
});

$("fitLearningGraph").addEventListener("click", fitLearningGraphView);
$("resetLearningGraph").addEventListener("click", resetLearningGraphView);
$("toggleGraphLegend").addEventListener("click", () => {
  $("learningGraphLegend").classList.toggle("hidden");
});

function enableGraphPanZoom() {
  const svg = $("learningGraphSvg");
  if (!svg) return;
  let dragging = false;
  let last = null;
  svg.addEventListener("wheel", (event) => {
    event.preventDefault();
    const before = graphPointFromEvent(event);
    const delta = event.deltaY > 0 ? 0.9 : 1.12;
    state.svgZoom = clamp(state.svgZoom * delta, GRAPH_MIN_ZOOM, GRAPH_MAX_ZOOM);
    const after = graphPointFromEvent(event);
    state.svgPan.x += before.x - after.x;
    state.svgPan.y += before.y - after.y;
    renderLearningGraphNetwork();
  }, { passive: false });
  svg.addEventListener("pointerdown", (event) => {
    if (event.target.closest && event.target.closest(".graph-node")) return;
    dragging = true;
    last = { x: event.clientX, y: event.clientY };
    svg.setPointerCapture(event.pointerId);
  });
  svg.addEventListener("pointermove", (event) => {
    if (updateNodeDrag(event)) return;
    if (!dragging || !last) return;
    const scale = 1 / state.svgZoom;
    state.svgPan.x -= (event.clientX - last.x) * scale;
    state.svgPan.y -= (event.clientY - last.y) * scale;
    last = { x: event.clientX, y: event.clientY };
    renderLearningGraphNetwork();
  });
  svg.addEventListener("pointerup", (event) => {
    if (stopNodeDrag(event)) return;
    dragging = false;
    last = null;
    try {
      svg.releasePointerCapture(event.pointerId);
    } catch (error) {
      // Pointer capture may already be released by the browser.
    }
  });
  svg.addEventListener("pointercancel", (event) => {
    stopNodeDrag(event);
    dragging = false;
    last = null;
  });
  svg.addEventListener("click", (event) => {
    if (event.target === svg) {
      state.selectedNodeId = null;
      state.hoveredNodeId = null;
      renderLearningGraphDetails(null);
      renderLearningGraphNetwork();
    }
  });
}

function enableLearningGraphSearch() {
  $("searchLearningGraph").addEventListener("click", searchLearningGraph);
  $("learningGraphSearch").addEventListener("input", () => {
    if (state.searchTimer) clearTimeout(state.searchTimer);
    state.searchTimer = setTimeout(searchLearningGraph, 260);
  });
  $("learningGraphSearch").addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      searchLearningGraph();
    }
  });
}

function enableGraphResize() {
  let timer = null;
  window.addEventListener("resize", () => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => {
      if (state.graphView === "graph") fitLearningGraphView();
    }, 180);
  });
}

connectWebSocket();
poll();
loadStatistics().catch(() => {});
enableGraphPanZoom();
enableLearningGraphSearch();
enableGraphResize();
loadLearningGraph().catch(() => {});
loadLearningReport().catch(() => {});
state.graphTimer = setInterval(() => {
  loadLearningGraph().catch(() => {});
}, 5000);
state.learningReportTimer = setInterval(() => {
  loadLearningReport().catch(() => {});
}, 60000);
