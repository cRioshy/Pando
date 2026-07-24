(function () {
  const SVG_NS = "http://www.w3.org/2000/svg";
  const WIDTH = 2200;
  const HEIGHT = 1350;
  const MARGIN = 90;
  const MIN_ZOOM = 0.22;
  const MAX_ZOOM = 4.5;
  const NODE_LIMIT = 300;
  const EDGE_LIMIT = 800;
  const REFRESH_MS = 20000;

  const colors = {
    brain: "#3ddc84",
    project: "#f2f5f7",
    market: "#39d5ff",
    crypto: "#39d5ff",
    stock: "#ffad42",
    indicator: "#4f8cff",
    decision: "#b58cff",
    signal: "#f5c542",
    learning: "#3ddc84",
    pattern: "#ff8bb3",
    data_source: "#ffd75e",
    bot: "#9aa8b2",
    service: "#b8c2cc",
    error: "#ff6868",
    warning: "#f5c542",
    memory: "#67e8f9",
  };

  const groupCenters = {
    system: { x: 1100, y: 145 },
    infrastructure: { x: 1100, y: 330 },
    brain: { x: 1100, y: 625 },
    crypto: { x: 330, y: 540 },
    stocks: { x: 1870, y: 540 },
    indicators: { x: 545, y: 1095 },
    patterns: { x: 1100, y: 1130 },
    decisions: { x: 1660, y: 1095 },
    warnings: { x: 325, y: 1070 },
    errors: { x: 1880, y: 1070 },
  };

  const state = {
    graph: null,
    positions: new Map(),
    velocities: new Map(),
    metrics: new Map(),
    manual: new Map(),
    selected: null,
    hovered: null,
    dragNode: null,
    pan: { x: 0, y: 0 },
    zoom: 1,
    timer: null,
    layoutSignature: "",
  };

  const $ = (id) => document.getElementById(id);

  function init() {
    if (!$("knowledgeGraphSvg")) return;
    bindControls();
    loadGraph().catch(showError);
    state.timer = setInterval(() => loadGraph({ soft: true }).catch(showError), REFRESH_MS);
  }

  function bindControls() {
    $("refreshKnowledgeGraph").addEventListener("click", () => loadGraph().catch(showError));
    $("fitKnowledgeGraph").addEventListener("click", fit);
    $("resetKnowledgeGraph").addEventListener("click", reset);
    $("searchKnowledgeGraph").addEventListener("click", search);
    $("knowledgeGraphSearch").addEventListener("keydown", (event) => {
      if (event.key === "Enter") search();
    });
    $("knowledgeGraphTypeFilter").addEventListener("change", render);
    $("knowledgeGraphGroupFilter").addEventListener("change", render);
    $("knowledgeGraphNeighborsOnly").addEventListener("change", render);
    $("toggleKnowledgeFullscreen").addEventListener("click", toggleFullscreen);
    enablePanZoom();
    window.addEventListener("resize", () => {
      window.clearTimeout(state.resizeTimer);
      state.resizeTimer = window.setTimeout(fit, 180);
    });
  }

  async function loadGraph(options = {}) {
    const graph = await requestJson("/api/v1/graph/overview");
    state.graph = graph;
    prunePositions();
    populateFilters();
    render();
    if (!options.soft) fit();
  }

  function visibleData() {
    const graph = state.graph || { nodes: [], edges: [] };
    const type = $("knowledgeGraphTypeFilter").value;
    const group = $("knowledgeGraphGroupFilter").value;
    let nodes = dedupe((graph.nodes || []).slice(0, NODE_LIMIT));
    if (type) nodes = nodes.filter((node) => node.type === type);
    if (group) nodes = nodes.filter((node) => node.group === group);

    const nodeIds = new Set(nodes.map((node) => node.id));
    let edges = dedupe((graph.edges || [])
      .filter((edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target))
      .slice(0, EDGE_LIMIT));

    if ($("knowledgeGraphNeighborsOnly").checked && state.selected) {
      const neighbors = neighborIds(edges, state.selected);
      nodes = nodes.filter((node) => neighbors.has(node.id));
      const allowed = new Set(nodes.map((node) => node.id));
      edges = edges.filter((edge) => allowed.has(edge.source) && allowed.has(edge.target));
    }
    return { nodes, edges };
  }

  function render() {
    if (!state.graph) return;
    const svg = $("knowledgeGraphSvg");
    const { nodes, edges } = visibleData();
    setText("knowledgeNodeCount", state.graph.node_count ?? nodes.length);
    setText("knowledgeEdgeCount", state.graph.edge_count ?? edges.length);
    setText("knowledgeVersion", state.graph.version ?? "-");
    setText("knowledgeUpdated", time(state.graph.generated_at));
    setText("knowledgeGraphStatus", nodes.length ? `${nodes.length} Knoten sichtbar` : "Keine Graph-Daten");
    renderDiagnostics(state.graph);
    renderLegend();

    svg.innerHTML = "";
    svg.setAttribute("viewBox", `${state.pan.x} ${state.pan.y} ${WIDTH / state.zoom} ${HEIGHT / state.zoom}`);
    if (!nodes.length) {
      const text = el("text", { x: WIDTH / 2, y: HEIGHT / 2, "text-anchor": "middle", fill: "#9aa8b2" });
      text.textContent = "Keine Knowledge-Graph-Daten";
      svg.appendChild(text);
      return;
    }

    const positions = layout(nodes, edges);
    const active = state.selected || state.hovered;
    const nIds = neighborIds(edges, active);
    const eIds = neighborEdgeIds(edges, active);
    const clusterLayer = el("g", {});
    const edgeLayer = el("g", {});
    const nodeLayer = el("g", {});
    svg.appendChild(clusterLayer);
    svg.appendChild(edgeLayer);
    svg.appendChild(nodeLayer);
    renderClusterLabels(clusterLayer, nodes);

    edges.forEach((edge) => {
      const a = positions.get(edge.source);
      const b = positions.get(edge.target);
      if (!a || !b) return;
      const line = el("line", {
        class: edgeClass(edge, eIds),
        x1: a.x,
        y1: a.y,
        x2: b.x,
        y2: b.y,
        "stroke-width": edgeWidth(edge),
      });
      edgeLayer.appendChild(line);
    });

    nodes.forEach((node) => {
      const point = positions.get(node.id);
      if (!point) return;
      const group = el("g", {
        class: nodeClass(node, nIds),
        transform: `translate(${point.x} ${point.y})`,
        tabindex: "0",
        role: "button",
        "aria-label": `${node.label} ${node.type}`,
      });
      group.dataset.nodeId = node.id;
      group.classList.add("entering");
      group.addEventListener("mouseenter", () => {
        state.hovered = node.id;
        render();
      });
      group.addEventListener("mouseleave", () => {
        state.hovered = null;
        render();
      });
      group.addEventListener("click", (event) => {
        event.stopPropagation();
        selectNode(node.id);
      });
      group.addEventListener("dblclick", (event) => {
        event.stopPropagation();
        focusNode(node.id);
      });
      group.addEventListener("pointerdown", (event) => startDrag(event, node.id));
      group.appendChild(el("circle", { r: radius(node), fill: colors[node.type] || "#b8c2cc" }));
      if (showLabel(node, nIds)) {
        const label = shortLabel(node.label || node.id);
        const labelWidth = Math.max(42, label.length * 7 + 16);
        group.appendChild(el("rect", {
          class: "kg-label-bg",
          x: -labelWidth / 2,
          y: radius(node) + 8,
          width: labelWidth,
          height: 22,
          rx: 6,
        }));
        const text = el("text", { class: "kg-label", y: radius(node) + 24, "text-anchor": "middle" });
        text.textContent = label;
        group.appendChild(text);
      }
      const title = el("title", {});
      title.textContent = `${node.label || node.id} | ${node.type} | ${node.group}`;
      group.appendChild(title);
      nodeLayer.appendChild(group);
    });
  }

  function layout(nodes, edges) {
    state.metrics = graphMetrics(nodes, edges);
    initializePositions(nodes, edges);
    runForces(nodes, edges);
    bound(nodes);
    return state.positions;
  }

  function initializePositions(nodes, edges) {
    const connected = new Set();
    edges.forEach((edge) => {
      connected.add(edge.source);
      connected.add(edge.target);
    });
    const indexes = new Map();
    nodes.forEach((node) => {
      if (state.manual.has(node.id)) {
        state.positions.set(node.id, state.manual.get(node.id));
        if (!state.velocities.has(node.id)) state.velocities.set(node.id, { x: 0, y: 0 });
        return;
      }
      if (state.positions.has(node.id)) return;
      const group = connected.has(node.id) ? node.group : "system";
      const center = groupCenters[group] || groupCenters.system;
      const index = indexes.get(group) || 0;
      indexes.set(group, index + 1);
      const angle = seededAngle(node.id, index);
      const ring = 50 + Math.floor(index / 8) * 68 + (index % 8) * 7;
      state.positions.set(node.id, {
        x: clamp(center.x + Math.cos(angle) * ring, MARGIN, WIDTH - MARGIN),
        y: clamp(center.y + Math.sin(angle) * ring, MARGIN, HEIGHT - MARGIN),
      });
      state.velocities.set(node.id, { x: 0, y: 0 });
    });
  }

  function runForces(nodes, edges) {
    runForceDirectedSimulation(nodes, edges);
  }

  function runForceDirectedSimulation(nodes, edges) {
    const nodeById = new Map(nodes.map((node) => [node.id, node]));
    const signature = nodes.map((node) => node.id).join("|") + "::" + edges.map((edge) => edge.id).join("|");
    const coldStart = state.layoutSignature !== signature;
    state.layoutSignature = signature;
    const iterations = coldStart ? (nodes.length > 180 ? 140 : 180) : 35;
    let alpha = coldStart ? 1.0 : 0.28;
    for (let step = 0; step < iterations; step += 1) {
      const forces = new Map(nodes.map((node) => [node.id, { x: 0, y: 0 }]));
      for (let i = 0; i < nodes.length; i += 1) {
        for (let j = i + 1; j < nodes.length; j += 1) {
          const aNode = nodes[i];
          const bNode = nodes[j];
          const a = state.positions.get(aNode.id);
          const b = state.positions.get(bNode.id);
          if (!a || !b) continue;
          let dx = b.x - a.x;
          let dy = b.y - a.y;
          let distance = Math.hypot(dx, dy);
          if (distance < 1) {
            const angle = seededAngle(`${aNode.id}:${bNode.id}`, j);
            dx = Math.cos(angle);
            dy = Math.sin(angle);
            distance = 1;
          }
          const sameGroup = aNode.group === bNode.group;
          const desired = radius(aNode) + radius(bNode) + (sameGroup ? 118 : 245);
          const push = Math.min(10, (desired * desired) / Math.max(120, distance * distance));
          const ux = dx / distance;
          const uy = dy / distance;
          forces.get(aNode.id).x -= ux * push * alpha;
          forces.get(aNode.id).y -= uy * push * alpha;
          forces.get(bNode.id).x += ux * push * alpha;
          forces.get(bNode.id).y += uy * push * alpha;
        }
      }

      edges.forEach((edge) => {
        const aNode = nodeById.get(edge.source);
        const bNode = nodeById.get(edge.target);
        const a = state.positions.get(edge.source);
        const b = state.positions.get(edge.target);
        if (!aNode || !bNode || !a || !b) return;
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const distance = Math.max(1, Math.hypot(dx, dy));
        const ideal = linkDistance(edge, aNode, bNode);
        const pull = clamp((distance - ideal) * linkStrength(edge, aNode, bNode), -5.5, 5.5);
        const ux = dx / distance;
        const uy = dy / distance;
        forces.get(edge.source).x += ux * pull * alpha;
        forces.get(edge.source).y += uy * pull * alpha;
        forces.get(edge.target).x -= ux * pull * alpha;
        forces.get(edge.target).y -= uy * pull * alpha;
      });

      nodes.forEach((node) => {
        if (state.manual.has(node.id)) return;
        const point = state.positions.get(node.id);
        const force = forces.get(node.id);
        const velocity = state.velocities.get(node.id) || { x: 0, y: 0 };
        const center = groupCenters[node.group] || groupCenters.system;
        if (!point || !force || !center) return;
        const groupPull = node.type === "brain" || node.type === "project" ? 0.032 : 0.048;
        force.x += (center.x - point.x) * groupPull * alpha;
        force.y += (center.y - point.y) * groupPull * alpha;
        force.x += (WIDTH / 2 - point.x) * 0.0008 * alpha;
        force.y += (HEIGHT / 2 - point.y) * 0.0008 * alpha;
        velocity.x = (velocity.x + force.x) * 0.72;
        velocity.y = (velocity.y + force.y) * 0.72;
        point.x = clamp(point.x + velocity.x, MARGIN, WIDTH - MARGIN);
        point.y = clamp(point.y + velocity.y, MARGIN, HEIGHT - MARGIN);
        state.velocities.set(node.id, velocity);
      });
      alpha *= 0.965;
    }
    setText("knowledgeGraphStatus", coldStart ? "Force-Layout stabilisiert" : "Layout aktualisiert");
  }

  function linkDistance(edge, aNode, bNode) {
    const sameGroup = aNode.group === bNode.group;
    const relation = String(edge.relation || "");
    if (relation === "belongs_to") return sameGroup ? 245 : 410;
    if (relation === "generated") return sameGroup ? 260 : 470;
    if (relation === "learned_from") return sameGroup ? 245 : 520;
    if (relation === "influenced") return sameGroup ? 320 : 620;
    if (relation === "uses") return sameGroup ? 280 : 680;
    if (relation === "received_from") return 260;
    if (relation === "depends_on") return 310;
    return sameGroup ? 280 : 560;
  }

  function linkStrength(edge, aNode, bNode) {
    const sameGroup = aNode.group === bNode.group;
    const weighted = Math.min(2.4, Math.log10(Number(edge.event_count || 1) + 1) + Number(edge.weight || 1) * 0.15);
    return (sameGroup ? 0.014 : 0.0045) * weighted;
  }

  function selectNode(id) {
    state.selected = id;
    loadNodeDetails(id).catch(() => renderDetails(findNode(id)));
    render();
  }

  async function loadNodeDetails(id) {
    const data = await requestJson(`/api/v1/graph/node/${encodeURIComponent(id)}`);
    renderDetails(data.node, data.neighbors || [], data.edges || []);
  }

  async function search() {
    const query = $("knowledgeGraphSearch").value.trim();
    if (!query) return;
    const data = await requestJson(`/api/v1/graph/search?q=${encodeURIComponent(query)}`);
    if (!data.nodes || !data.nodes.length) {
      setText("knowledgeGraphStatus", "Kein Treffer");
      return;
    }
    focusNode(data.nodes[0].id);
  }

  function focusNode(id) {
    state.selected = id;
    if (!state.positions.has(id)) {
      render();
    }
    const point = state.positions.get(id);
    if (point) {
      state.zoom = 1.9;
      state.pan = {
        x: point.x - WIDTH / (2 * state.zoom),
        y: point.y - HEIGHT / (2 * state.zoom),
      };
    }
    loadNodeDetails(id).catch(() => {});
    render();
  }

  function renderDetails(node, neighbors = [], edges = []) {
    const panel = $("knowledgeGraphDetails");
    if (!node) {
      panel.className = "details empty";
      panel.textContent = "Noch kein Knoten ausgewaehlt";
      return;
    }
    panel.className = "details";
    const metadata = node.metadata || {};
    const rows = [
      ["Name", node.label],
      ["Typ", node.type],
      ["Cluster", node.group],
      ["Status", node.status],
      ["Health", node.health],
      ["Confidence", node.confidence === null || node.confidence === undefined ? "-" : `${Number(node.confidence).toFixed(2)} %`],
      ["Wichtigkeit", node.importance],
      ["Anzahl", node.count],
      ["Nachbarn", neighbors.length],
      ["Verbindungen", edges.length],
      ["Update", time(node.last_updated)],
      ...Object.entries(metadata).slice(0, 6).map(([key, value]) => [key, value]),
    ];
    panel.innerHTML = `
      <div class="graph-detail-grid">
        ${rows.map(([key, value]) => `<span>${escapeHtml(key)}</span><strong>${escapeHtml(value ?? "-")}</strong>`).join("")}
      </div>
    `;
  }

  function populateFilters() {
    const graph = state.graph || { nodes: [] };
    populateSelect("knowledgeGraphTypeFilter", unique(graph.nodes.map((node) => node.type)), "Alle Typen");
    populateSelect("knowledgeGraphGroupFilter", unique(graph.nodes.map((node) => node.group)), "Alle Cluster");
  }

  function populateSelect(id, values, empty) {
    const select = $(id);
    const previous = select.value;
    select.innerHTML = "";
    const option = document.createElement("option");
    option.value = "";
    option.textContent = empty;
    select.appendChild(option);
    values.forEach((value) => {
      const item = document.createElement("option");
      item.value = value;
      item.textContent = value;
      select.appendChild(item);
    });
    select.value = values.includes(previous) ? previous : "";
  }

  function enablePanZoom() {
    const svg = $("knowledgeGraphSvg");
    let dragging = false;
    let last = null;
    svg.addEventListener("wheel", (event) => {
      event.preventDefault();
      const factor = event.deltaY < 0 ? 1.12 : 0.88;
      const before = pointFromEvent(event);
      const nextZoom = clamp(state.zoom * factor, MIN_ZOOM, MAX_ZOOM);
      state.zoom = nextZoom;
      const afterWidth = WIDTH / state.zoom;
      const afterHeight = HEIGHT / state.zoom;
      const rect = svg.getBoundingClientRect();
      state.pan = {
        x: before.x - ((event.clientX - rect.left) / Math.max(1, rect.width)) * afterWidth,
        y: before.y - ((event.clientY - rect.top) / Math.max(1, rect.height)) * afterHeight,
      };
      render();
    }, { passive: false });
    svg.addEventListener("pointerdown", (event) => {
      if (event.target.closest && event.target.closest(".kg-node")) return;
      dragging = true;
      last = { x: event.clientX, y: event.clientY };
      svg.setPointerCapture(event.pointerId);
    });
    svg.addEventListener("pointermove", (event) => {
      if (updateDrag(event)) return;
      if (!dragging || !last) return;
      const rect = svg.getBoundingClientRect();
      state.pan.x -= (event.clientX - last.x) * (WIDTH / state.zoom) / Math.max(1, rect.width);
      state.pan.y -= (event.clientY - last.y) * (HEIGHT / state.zoom) / Math.max(1, rect.height);
      last = { x: event.clientX, y: event.clientY };
      render();
    });
    svg.addEventListener("pointerup", (event) => {
      stopDrag(event);
      dragging = false;
      last = null;
    });
    svg.addEventListener("click", (event) => {
      if (event.target === svg) {
        state.selected = null;
        renderDetails(null);
        render();
      }
    });
  }

  function startDrag(event, id) {
    event.preventDefault();
    event.stopPropagation();
    state.dragNode = id;
    state.selected = id;
    state.manual.set(id, pointFromEvent(event));
    $("knowledgeGraphSvg").setPointerCapture(event.pointerId);
    render();
  }

  function updateDrag(event) {
    if (!state.dragNode) return false;
    const point = pointFromEvent(event);
    state.manual.set(state.dragNode, {
      x: clamp(point.x, MARGIN, WIDTH - MARGIN),
      y: clamp(point.y, MARGIN, HEIGHT - MARGIN),
    });
    state.positions.set(state.dragNode, state.manual.get(state.dragNode));
    renderDetails(findNode(state.dragNode));
    render();
    return true;
  }

  function stopDrag(event) {
    if (!state.dragNode) return;
    try {
      $("knowledgeGraphSvg").releasePointerCapture(event.pointerId);
    } catch (error) {
      // Browser may release capture automatically.
    }
    state.dragNode = null;
  }

  function fit() {
    const positions = Array.from(state.positions.values());
    if (!positions.length) {
      state.pan = { x: 0, y: 0 };
      state.zoom = 1;
      render();
      return;
    }
    const minX = Math.min(...positions.map((point) => point.x)) - 130;
    const maxX = Math.max(...positions.map((point) => point.x)) + 130;
    const minY = Math.min(...positions.map((point) => point.y)) - 130;
    const maxY = Math.max(...positions.map((point) => point.y)) + 130;
    const width = Math.max(1, maxX - minX);
    const height = Math.max(1, maxY - minY);
    state.zoom = clamp(Math.min(WIDTH / width, HEIGHT / height), 0.45, 2.1);
    state.pan = { x: minX, y: minY };
    render();
  }

  function reset() {
    state.selected = null;
    state.hovered = null;
    state.positions = new Map();
    state.velocities = new Map();
    state.manual = new Map();
    state.layoutSignature = "";
    state.pan = { x: 0, y: 0 };
    state.zoom = 1;
    renderDetails(null);
    render();
    fit();
  }

  function toggleFullscreen() {
    document.querySelector(".knowledge-panel").classList.toggle("fullscreen");
    window.setTimeout(fit, 120);
  }

  function prunePositions() {
    const ids = new Set(((state.graph && state.graph.nodes) || []).map((node) => node.id));
    state.positions = new Map(Array.from(state.positions.entries()).filter(([id]) => ids.has(id)));
    state.velocities = new Map(Array.from(state.velocities.entries()).filter(([id]) => ids.has(id)));
    state.manual = new Map(Array.from(state.manual.entries()).filter(([id]) => ids.has(id)));
  }

  function renderClusterLabels(layer, nodes) {
    unique(nodes.map((node) => node.group)).forEach((group) => {
      const center = groupCenters[group];
      if (!center) return;
      const text = el("text", { class: "kg-cluster-label", x: center.x, y: center.y - 122, "text-anchor": "middle" });
      text.textContent = group;
      layer.appendChild(text);
    });
  }

  function renderLegend() {
    const legend = $("knowledgeGraphLegend");
    if (legend.dataset.rendered === "true") return;
    legend.innerHTML = "";
    Object.entries(colors).forEach(([type, color]) => {
      const row = document.createElement("div");
      row.className = "knowledge-legend-row";
      row.innerHTML = "<span class=\"knowledge-legend-dot\"></span><span></span>";
      row.children[0].style.background = color;
      row.children[1].textContent = type;
      legend.appendChild(row);
    });
    legend.dataset.rendered = "true";
  }

  function graphMetrics(nodes, edges) {
    const metrics = new Map(nodes.map((node) => [node.id, { degree: 0, weighted: 0 }]));
    edges.forEach((edge) => {
      const weight = Math.max(1, Number(edge.event_count || 1)) * Math.max(0.5, Number(edge.weight || 1));
      if (metrics.has(edge.source)) {
        const source = metrics.get(edge.source);
        source.degree += 1;
        source.weighted += weight;
      }
      if (metrics.has(edge.target)) {
        const target = metrics.get(edge.target);
        target.degree += 1;
        target.weighted += weight;
      }
    });
    return metrics;
  }

  function radius(node) {
    const base = {
      brain: [34, 56],
      project: [30, 46],
      market: [26, 40],
      crypto: [22, 38],
      stock: [22, 38],
      indicator: [14, 24],
      decision: [16, 28],
      signal: [18, 30],
      learning: [18, 30],
      pattern: [16, 28],
      data_source: [16, 26],
      bot: [18, 30],
      service: [16, 26],
      error: [18, 30],
      warning: [16, 28],
      memory: [16, 28],
    }[node.type] || [15, 25];
    const metric = state.metrics.get(node.id) || { degree: 0, weighted: 0 };
    const importance = Number(node.importance || 1);
    const count = Math.log10(Number(node.count || 1) + 1);
    const size = base[0] + count * 2.8 + metric.degree * 0.75 + Math.sqrt(metric.weighted) * 0.9 + importance * 0.035;
    return clamp(size, base[0], base[1]);
  }

  function showLabel(node, neighbors) {
    if (state.selected === node.id || state.hovered === node.id) return true;
    if (state.selected && neighbors.has(node.id) && state.zoom >= 0.85) return true;
    if (["brain", "project", "market"].includes(node.type)) return true;
    return state.zoom >= 1.35 && Number(node.importance || 0) >= 70;
  }

  function nodeClass(node, neighbors) {
    const classes = ["kg-node"];
    if (state.selected === node.id) classes.push("selected");
    if (state.hovered === node.id || (state.selected && neighbors.has(node.id))) classes.push("focus");
    if (state.selected && !neighbors.has(node.id)) classes.push("dim");
    return classes.join(" ");
  }

  function edgeClass(edge, edgeIds) {
    const classes = ["kg-edge"];
    if (state.selected) {
      classes.push(edgeIds.has(edge.id) ? "focus" : "dim");
    }
    return classes.join(" ");
  }

  function edgeWidth(edge) {
    return clamp(0.6 + Math.log10(Number(edge.event_count || 1) + 1) * 0.7 + Number(edge.weight || 1) * 0.16, 0.7, 4);
  }

  function bound(nodes) {
    nodes.forEach((node) => {
      const point = state.positions.get(node.id);
      if (!point) return;
      const r = radius(node) + 16;
      point.x = clamp(point.x, MARGIN + r, WIDTH - MARGIN - r);
      point.y = clamp(point.y, MARGIN + r, HEIGHT - MARGIN - r);
    });
  }

  function pointFromEvent(event) {
    const svg = $("knowledgeGraphSvg");
    const rect = svg.getBoundingClientRect();
    return {
      x: state.pan.x + ((event.clientX - rect.left) / Math.max(1, rect.width)) * (WIDTH / state.zoom),
      y: state.pan.y + ((event.clientY - rect.top) / Math.max(1, rect.height)) * (HEIGHT / state.zoom),
    };
  }

  function neighborIds(edges, id) {
    const ids = new Set();
    if (!id) return ids;
    ids.add(id);
    edges.forEach((edge) => {
      if (edge.source === id) ids.add(edge.target);
      if (edge.target === id) ids.add(edge.source);
    });
    return ids;
  }

  function neighborEdgeIds(edges, id) {
    const ids = new Set();
    if (!id) return ids;
    edges.forEach((edge) => {
      if (edge.source === id || edge.target === id) ids.add(edge.id);
    });
    return ids;
  }

  function findNode(id) {
    return ((state.graph && state.graph.nodes) || []).find((node) => node.id === id);
  }

  function dedupe(items) {
    const seen = new Set();
    const result = [];
    items.forEach((item) => {
      if (!item || !item.id || seen.has(item.id)) return;
      seen.add(item.id);
      result.push(item);
    });
    return result;
  }

  function unique(values) {
    return Array.from(new Set(values.filter(Boolean))).sort();
  }

  function requestJson(url) {
    const cacheBustedUrl = `${url}${url.includes("?") ? "&" : "?"}_=${Date.now()}`;
    if (typeof window.fetch === "function") {
      return window.fetch(cacheBustedUrl, { cache: "no-store" }).then(async (response) => {
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || "Knowledge graph failed");
        return payload;
      });
    }
    return new Promise((resolve, reject) => {
      const request = new XMLHttpRequest();
      request.open("GET", cacheBustedUrl, true);
      request.setRequestHeader("Accept", "application/json");
      request.onload = function () {
        try {
          const payload = JSON.parse(request.responseText || "{}");
          if (request.status < 200 || request.status >= 300) {
            reject(new Error(payload.error || `Knowledge graph failed: ${request.status}`));
            return;
          }
          resolve(payload);
        } catch (error) {
          reject(error);
        }
      };
      request.onerror = function () {
        reject(new Error("Knowledge graph request failed"));
      };
      request.send();
    });
  }

  function seededAngle(id, index) {
    let hash = 0;
    String(id).split("").forEach((char) => {
      hash = (hash * 31 + char.charCodeAt(0)) >>> 0;
    });
    return ((hash % 360) / 180) * Math.PI + index * 0.43;
  }

  function shortLabel(value) {
    const text = String(value || "-");
    return text.length > 20 ? `${text.slice(0, 18)}...` : text;
  }

  function el(name, attributes) {
    const node = document.createElementNS(SVG_NS, name);
    Object.entries(attributes || {}).forEach(([key, value]) => node.setAttribute(key, String(value)));
    return node;
  }

  function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
  }

  function setText(id, value) {
    const node = $(id);
    if (!node) return;
    node.textContent = value === null || value === undefined || value === "" ? "-" : value;
  }

  function renderDiagnostics(graph) {
    const diagnostics = (graph && graph.diagnostics) || {};
    const bounds = diagnostics.bounds || {};
    setText("knowledgeRenderer", "SVG Fallback");
    setText("knowledgeProjection", diagnostics.projection || graph.mode || "overview");
    setText("knowledgeCommunities", diagnostics.communities ?? "-");
    setText("knowledgeFa2Iterations", diagnostics.forceatlas2_iterations ?? 0);
    setText("knowledgeLayoutRuntime", diagnostics.forceatlas2_runtime_ms ?? 0);
    setText("knowledgeBoundsX", `${number(bounds.min_x)} / ${number(bounds.max_x)}`);
    setText("knowledgeBoundsY", `${number(bounds.min_y)} / ${number(bounds.max_y)}`);
    setText("knowledgeOverlaps", diagnostics.overlapping_nodes ?? 0);
    setText("knowledgeIsolated", diagnostics.isolated_nodes ?? 0);
    setText("knowledgeDuplicatePositions", diagnostics.duplicate_positions ?? 0);
    console.info("[Pandorick Knowledge Graph]", {
      renderer: "SVG Fallback",
      webgl_available: Boolean(window.WebGLRenderingContext),
      sigma_initialized: false,
      graphology_loaded: Boolean(window.graphology),
      forceatlas2_started: Boolean(diagnostics.forceatlas2_started),
      forceatlas2_finished: Boolean(diagnostics.forceatlas2_finished),
      forceatlas2_iterations: diagnostics.forceatlas2_iterations || 0,
      layout_runtime_ms: diagnostics.forceatlas2_runtime_ms || 0,
      nodes: graph.node_count,
      edges: graph.edge_count,
      communities: diagnostics.communities,
      bounds: diagnostics.bounds,
      duplicate_positions: diagnostics.duplicate_positions,
      overlapping_nodes: diagnostics.overlapping_nodes,
      isolated_nodes: diagnostics.isolated_nodes,
    });
  }

  function number(value) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
    return Number(value).toFixed(2);
  }

  function time(value) {
    if (!value) return "-";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleTimeString();
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function showError(error) {
    setText("knowledgeGraphStatus", error.message || "Knowledge Graph Fehler");
  }

  window.PandorickLegacyKnowledgeGraph = { init };
  if (document.readyState === "loading") {
    window.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
}());
