(function () {
  const COLORS = {
    brain: "#3ddc84",
    cluster: "#8ea4ff",
    project: "#eef3f6",
    market: "#39d5ff",
    crypto: "#39d5ff",
    stock: "#ffad42",
    stocks: "#ffad42",
    indicator: "#4f8cff",
    decision: "#b58cff",
    signal: "#f5c542",
    learning: "#3ddc84",
    pattern: "#ff8bb3",
    data_source: "#ffd75e",
    bot: "#9aa8b2",
    service: "#b8c2cc",
    infrastructure: "#9aa8b2",
    system: "#b8c2cc",
    error: "#ff6868",
    warning: "#f5c542",
    memory: "#67e8f9",
  };
  const REFRESH_MS = 25000;
  const GRAPH_BOUNDS = { minX: -1250, maxX: 1250, minY: -780, maxY: 780 };
  const CLUSTER_ANCHORS = {
    crypto: { x: -720, y: -260, label: "Crypto" },
    stocks: { x: 720, y: -260, label: "Stocks" },
    brain: { x: 0, y: 0, label: "Brain" },
    learning: { x: -430, y: 360, label: "Learning" },
    pattern: { x: 430, y: 360, label: "Pattern" },
    decision: { x: 0, y: -470, label: "Decision" },
    system: { x: 0, y: 520, label: "System" },
    data: { x: -910, y: 320, label: "Data" },
    misc: { x: 910, y: 320, label: "Other" },
  };

  const state = {
    graph: null,
    sigma: null,
    rendererGraph: null,
    payload: null,
    selected: null,
    mode: "overview",
    timer: null,
    minEdgeWeight: 0,
    fallbackActive: false,
    loading: false,
    layoutPositions: new Map(),
    draggedNode: null,
    viewMode: "2d",
    rotation3d: { x: -0.22, y: 0.38 },
    zoom3d: 0.54,
    pan3d: { x: 0, y: 0 },
    pointer3d: null,
  };

  const $ = (id) => document.getElementById(id);

  function init() {
    if (!$("knowledgeGraphSvg")) return;
    if (!supportsSigma()) {
      loadLegacyFallback("WebGL oder Sigma nicht verfuegbar. Fallback-Ansicht aktiv.").catch(showError);
      return;
    }
    setText("knowledgeRenderer", "Sigma laedt");
    replaceSvgWithContainer();
    bindControls();
    renderLegend();
    updateModeButtons();
    loadProjection("overview").catch(showError);
    state.timer = setInterval(() => loadProjection(state.mode, { soft: true }).catch(showError), REFRESH_MS);
    window.setTimeout(() => {
      const status = $("knowledgeGraphStatus");
      if (state.loading && !state.sigma) {
        state.loading = false;
        loadLegacyFallback("Sigma laedt zu lange. Fallback-Ansicht aktiv.").catch(showError);
        return;
      }
      if (!state.sigma && status && status.textContent === "Verbinde...") {
        loadLegacyFallback("Sigma konnte nicht initialisieren. Fallback-Ansicht aktiv.").catch(showError);
      }
    }, 15000);
  }

  function replaceSvgWithContainer() {
    const oldSvg = $("knowledgeGraphSvg");
    if (!oldSvg || oldSvg.tagName.toLowerCase() !== "svg") return;
    const container = document.createElement("div");
    container.id = "knowledgeGraphSvg";
    container.className = "knowledge-graph-canvas";
    container.setAttribute("role", "img");
    container.setAttribute("aria-label", "Pandorick Sigma Knowledge Graph");
    oldSvg.replaceWith(container);
  }

  function supportsSigma() {
    return Boolean(window.graphology && window.Sigma && hasWebGLContext());
  }

  function hasWebGLContext() {
    if (!window.WebGLRenderingContext) return false;
    const canvas = document.createElement("canvas");
    const context = canvas.getContext("webgl2") || canvas.getContext("webgl") || canvas.getContext("experimental-webgl");
    return Boolean(context);
  }

  async function loadLegacyFallback(message) {
    if (state.fallbackActive) return;
    state.fallbackActive = true;
    if (state.timer) window.clearInterval(state.timer);
    if (state.sigma) {
      state.sigma.kill();
      state.sigma = null;
    }
    restoreSvgContainer();
    setText("knowledgeGraphStatus", message);
    setText("knowledgeRenderer", "SVG Fallback");
    if (!$("knowledgeLegacyCss")) {
      const css = document.createElement("link");
      css.id = "knowledgeLegacyCss";
      css.rel = "stylesheet";
      css.href = "/knowledge_graph_legacy.css?v=sigma-engine-2";
      document.head.appendChild(css);
    }
    if (window.PandorickLegacyKnowledgeGraph) {
      window.PandorickLegacyKnowledgeGraph.init();
      return;
    }
    await new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = "/knowledge_graph_legacy.js?v=sigma-engine-2";
      script.onload = resolve;
      script.onerror = () => reject(new Error("Knowledge Graph Fallback konnte nicht geladen werden"));
      document.body.appendChild(script);
    });
  }

  function restoreSvgContainer() {
    const current = $("knowledgeGraphSvg");
    if (!current || current.tagName.toLowerCase() === "svg") return;
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.id = "knowledgeGraphSvg";
    svg.setAttribute("class", "knowledge-graph-svg");
    svg.setAttribute("role", "img");
    svg.setAttribute("aria-label", "Pandorick Knowledge Graph");
    current.replaceWith(svg);
  }

  function bindControls() {
    $("refreshKnowledgeGraph").addEventListener("click", () => loadProjection(state.mode).catch(showError));
    $("fitKnowledgeGraph").addEventListener("click", fitCamera);
    $("resetKnowledgeGraph").addEventListener("click", () => loadProjection("overview").catch(showError));
    $("knowledgeOverviewMode").addEventListener("click", () => loadProjection("overview").catch(showError));
    $("knowledgeFullMode").addEventListener("click", () => loadProjection("full").catch(showError));
    $("knowledge2DMode").addEventListener("click", () => setGraphViewMode("2d"));
    $("knowledge3DMode").addEventListener("click", () => setGraphViewMode("3d"));
    $("searchKnowledgeGraph").addEventListener("click", search);
    $("knowledgeGraphSearch").addEventListener("keydown", (event) => {
      if (event.key === "Enter") search();
      if (event.key === "Escape") loadProjection("overview").catch(showError);
    });
    $("knowledgeGraphTypeFilter").addEventListener("change", renderCurrentPayload);
    $("knowledgeGraphGroupFilter").addEventListener("change", renderCurrentPayload);
    $("knowledgeMinEdgeWeight").addEventListener("input", () => {
      state.minEdgeWeight = Number($("knowledgeMinEdgeWeight").value || 0);
      setText("knowledgeMinEdgeWeightValue", state.minEdgeWeight.toFixed(2).replace(/\.00$/, ""));
      if (state.mode === "full") {
        loadProjection("full", { soft: true }).catch(showError);
      } else {
        renderCurrentPayload();
      }
    });
    $("knowledgeGraphNeighborsOnly").addEventListener("change", () => {
      if (state.selected && $("knowledgeGraphNeighborsOnly").checked) {
        loadProjection("neighborhood", { nodeId: state.selected }).catch(showError);
      } else {
        loadProjection("overview").catch(showError);
      }
    });
    $("toggleKnowledgeFullscreen").addEventListener("click", toggleFullscreen);
    window.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        state.selected = null;
        $("knowledgeGraphNeighborsOnly").checked = false;
        loadProjection("overview").catch(showError);
      }
    });
    window.addEventListener("resize", () => {
      if (state.sigma) state.sigma.refresh();
    });
  }

  async function loadProjection(mode, options = {}) {
    state.loading = true;
    let url = "/api/v1/graph/overview";
    if (mode === "cluster" && options.clusterId) {
      url = `/api/v1/graph/cluster/${encodeURIComponent(options.clusterId)}`;
    }
    if (mode === "neighborhood" && options.nodeId) {
      url = `/api/v1/graph/node/${encodeURIComponent(options.nodeId)}`;
    }
    if (mode === "full") {
      url = `/api/v1/graph/full?min_edge_weight=${encodeURIComponent(state.minEdgeWeight)}`;
    }
    try {
      const payload = await requestJson(url);
      state.mode = mode;
      updateModeButtons();
      state.payload = normalizeProjection(payload);
      populateFilters(state.payload.nodes);
      renderCurrentPayload();
      if (!options.soft) fitCamera();
    } finally {
      state.loading = false;
    }
  }

  function normalizeProjection(payload) {
    if (payload.node && Array.isArray(payload.neighbors)) {
      const byId = new Map((payload.nodes || []).map((node) => [node.id, node]));
      byId.set(payload.node.id, payload.node);
      payload.neighbors.forEach((node) => byId.set(node.id, node));
      payload.nodes = Array.from(byId.values());
    }
    return payload;
  }

  function renderCurrentPayload() {
    if (!state.payload) return;
    const filtered = applyFilters(state.payload);
    if (state.viewMode === "3d") {
      renderKnowledgeGraph3D(filtered);
    } else {
      renderSigma(filtered);
    }
    renderStats(filtered);
    renderDetails(state.selected ? findNode(filtered, state.selected) : null);
  }

  function setGraphViewMode(mode) {
    state.viewMode = mode === "3d" ? "3d" : "2d";
    const twoD = $("knowledge2DMode");
    const threeD = $("knowledge3DMode");
    if (twoD) twoD.classList.toggle("active", state.viewMode === "2d");
    if (threeD) threeD.classList.toggle("active", state.viewMode === "3d");
    renderCurrentPayload();
  }

  function applyFilters(payload) {
    const type = $("knowledgeGraphTypeFilter").value;
    const group = $("knowledgeGraphGroupFilter").value;
    let nodes = payload.nodes || [];
    if (type) nodes = nodes.filter((node) => node.type === type);
    if (group) nodes = nodes.filter((node) => node.group === group || node.community === group);
    const ids = new Set(nodes.map((node) => node.id));
    const edges = (payload.edges || []).filter((edge) => {
      return ids.has(edge.source) && ids.has(edge.target) && Number(edge.weight || 0) >= state.minEdgeWeight;
    });
    return { ...payload, nodes, edges };
  }

  function renderSigma(payload) {
    const container = $("knowledgeGraphSvg");
    if (!window.graphology || !window.Sigma) {
      showError(new Error("Sigma/Graphology nicht geladen. Legacy-Fallback verfuegbar."));
      return;
    }
    if (state.sigma) {
      state.sigma.kill();
      state.sigma = null;
    }
    container.innerHTML = "";
    const graph = new window.graphology.Graph({ multi: false, type: "undirected" });
    const nodes = payload.nodes || [];
    const edges = payload.edges || [];
    const layout = buildClusteredLayout(nodes, edges);

    nodes.forEach((node) => {
      const color = nodeColorFromData(node);
      const visual = layout.get(node.id) || {};
      const size = visual.size || visualNodeSize(node);
      const label = String(node.label || node.id);
      const labelVisible = shouldRenderSigmaLabel(node, visual);
      graph.addNode(node.id, {
        label: labelVisible ? label : "",
        displayLabel: labelVisible ? label : "",
        labelVisible,
        fullLabel: label,
        x: visual.x,
        y: visual.y,
        size,
        baseSize: size,
        color,
        baseColor: color,
        nodeType: node.type,
        group: node.group,
        community: node.community,
        cluster: visual.cluster,
        degree: Number(node.degree || 0),
        importance: Number(node.importance || 0),
        important: Boolean(visual.important),
        hidden: false,
      });
    });
    edges.forEach((edge) => {
      if (!graph.hasNode(edge.source) || !graph.hasNode(edge.target) || graph.hasEdge(edge.source, edge.target)) return;
      const color = edgeColor(edge);
      const size = edgeSize(edge);
      graph.addUndirectedEdge(edge.source, edge.target, {
        size,
        baseSize: size,
        color,
        baseColor: color,
        relation: edge.relation,
        weight: edge.weight,
        visualWeight: edge.visual_weight,
        crossCluster: Boolean(edge.cross_cluster),
      });
    });

    state.rendererGraph = graph;
    try {
      state.sigma = new window.Sigma(graph, container, {
        allowInvalidContainer: true,
        defaultEdgeType: "line",
        defaultNodeType: "circle",
        renderEdgeLabels: false,
        labelDensity: 0.08,
        labelGridCellSize: 90,
        labelRenderedSizeThreshold: 10,
        minCameraRatio: 0.08,
        maxCameraRatio: 8,
        enableEdgeEvents: false,
      });
    } catch (error) {
      loadLegacyFallback("Sigma konnte nicht starten. Fallback-Ansicht aktiv.").catch(showError);
      return;
    }
    state.sigma.on("enterNode", ({ node }) => highlight(node));
    state.sigma.on("leaveNode", () => clearHighlight());
    state.sigma.on("clickNode", ({ node }) => {
      state.selected = node;
      const attrs = graph.getNodeAttributes(node);
      renderDetails(findNode(payload, node));
      highlight(node);
      focusCameraOnNode(attrs, 520);
    });
    state.sigma.on("doubleClickNode", ({ node }) => {
      const attrs = graph.getNodeAttributes(node);
      focusCameraOnNode(attrs, 620);
    });
    bindSigmaDragging();
    setText("knowledgeGraphStatus", `${payload.mode || state.mode}: ${nodes.length} Knoten, ${edges.length} Kanten`);
    setText("knowledgeRenderer", "Sigma WebGL");
    logDiagnostics(payload, "Sigma WebGL");
  }

  function renderKnowledgeGraph3D(payload) {
    replaceSvgWithContainer();
    if (state.sigma) {
      state.sigma.kill();
      state.sigma = null;
    }
    const container = $("knowledgeGraphSvg");
    const nodes = payload.nodes || [];
    const edges = payload.edges || [];
    const layout = buildClusteredLayout(nodes, edges);
    const projected = projectLayout3D(nodes, layout, container);
    container.className = "knowledge-graph-canvas knowledge-graph-3d";
    container.innerHTML = `
      <div class="knowledge-3d-stage">
        <svg class="knowledge-3d-edges" aria-hidden="true"></svg>
        <div class="knowledge-3d-nodes"></div>
        <div class="knowledge-3d-axis">3D Knowledge Space</div>
      </div>
    `;
    const edgeLayer = container.querySelector(".knowledge-3d-edges");
    const nodeLayer = container.querySelector(".knowledge-3d-nodes");
    const renderedEdges = [];
    edges.forEach((edge) => {
      const source = projected.get(edge.source);
      const target = projected.get(edge.target);
      if (!source || !target) return;
      renderedEdges.push(edge);
      const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
      line.setAttribute("x1", source.x);
      line.setAttribute("y1", source.y);
      line.setAttribute("x2", target.x);
      line.setAttribute("y2", target.y);
      line.setAttribute("class", `knowledge-3d-edge ${edge.cross_cluster ? "cross" : ""}`);
      line.setAttribute("stroke-width", String(edgeSize(edge)));
      edgeLayer.appendChild(line);
    });
    nodes
      .slice()
      .sort((a, b) => (projected.get(a.id)?.scale || 0) - (projected.get(b.id)?.scale || 0))
      .forEach((node) => {
        const point = projected.get(node.id);
        if (!point) return;
        const button = document.createElement("button");
        button.type = "button";
        button.className = `knowledge-3d-node cluster-${point.cluster}`;
        button.dataset.nodeId = node.id;
        button.style.left = `${point.x}px`;
        button.style.top = `${point.y}px`;
        button.style.width = `${point.size}px`;
        button.style.height = `${point.size}px`;
        button.style.background = `radial-gradient(circle at 35% 30%, #ffffff, ${nodeColorFromData(node)} 28%, rgba(8, 12, 17, 0.88) 74%)`;
        button.style.opacity = String(point.opacity);
        button.style.zIndex = String(point.zIndex);
        button.title = String(node.label || node.id);
        button.innerHTML = `<span>${escapeHtml(shortLabel(node))}</span>`;
        button.addEventListener("mouseenter", () => highlight3DNode(container, node.id, renderedEdges));
        button.addEventListener("mouseleave", () => clear3DHighlight(container));
        button.addEventListener("click", () => {
          state.selected = node.id;
          renderDetails(node);
          focus3DNode(point);
          highlight3DNode(container, node.id, renderedEdges);
        });
        nodeLayer.appendChild(button);
      });
    bind3DControls(container);
    setText("knowledgeGraphStatus", `${payload.mode || state.mode}: ${nodes.length} Knoten, ${edges.length} Kanten, 3D aktiv`);
    setText("knowledgeRenderer", "3D Web");
    logDiagnostics(payload, "3D Web");
  }

  function projectLayout3D(nodes, layout, container) {
    const width = Math.max(720, container.clientWidth || 1120);
    const height = Math.max(560, container.clientHeight || 680);
    const centerX = width / 2 + state.pan3d.x;
    const centerY = height / 2 + state.pan3d.y;
    const sinX = Math.sin(state.rotation3d.x);
    const cosX = Math.cos(state.rotation3d.x);
    const sinY = Math.sin(state.rotation3d.y);
    const cosY = Math.cos(state.rotation3d.y);
    const projected = new Map();
    nodes.forEach((node) => {
      const point = layout.get(node.id);
      if (!point) return;
      const x1 = point.x * cosY - point.z * sinY;
      const z1 = point.x * sinY + point.z * cosY;
      const y1 = point.y * cosX - z1 * sinX;
      const z2 = point.y * sinX + z1 * cosX;
      const perspective = 1050 / (1050 + z2);
      const scale = perspective * state.zoom3d;
      projected.set(node.id, {
        x: centerX + x1 * scale,
        y: centerY + y1 * scale,
        z: z2,
        zIndex: Math.round(5000 - z2),
        opacity: clamp(0.38 + perspective * 0.56, 0.32, 1),
        size: Math.max(11, point.size * 2.4 * perspective),
        cluster: point.cluster,
      });
    });
    return projected;
  }

  function bind3DControls(container) {
    container.onwheel = (event) => {
      event.preventDefault();
      const delta = event.deltaY > 0 ? -0.045 : 0.045;
      state.zoom3d = clamp(state.zoom3d + delta, 0.28, 1.35);
      renderCurrentPayload();
    };
    container.onpointerdown = (event) => {
      if (event.target.closest(".knowledge-3d-node")) return;
      container.setPointerCapture(event.pointerId);
      state.pointer3d = { x: event.clientX, y: event.clientY, pan: event.shiftKey };
    };
    container.onpointermove = (event) => {
      if (!state.pointer3d) return;
      const dx = event.clientX - state.pointer3d.x;
      const dy = event.clientY - state.pointer3d.y;
      state.pointer3d.x = event.clientX;
      state.pointer3d.y = event.clientY;
      if (state.pointer3d.pan) {
        state.pan3d.x += dx;
        state.pan3d.y += dy;
      } else {
        state.rotation3d.y += dx * 0.006;
        state.rotation3d.x = clamp(state.rotation3d.x + dy * 0.004, -1.05, 1.05);
      }
      renderCurrentPayload();
    };
    container.onpointerup = () => {
      state.pointer3d = null;
    };
    container.onpointercancel = () => {
      state.pointer3d = null;
    };
  }

  function highlight3DNode(container, nodeId, edges) {
    const connected = new Set([nodeId]);
    edges.forEach((edge) => {
      if (edge.source === nodeId) connected.add(edge.target);
      if (edge.target === nodeId) connected.add(edge.source);
    });
    container.querySelectorAll(".knowledge-3d-node").forEach((node) => {
      const focused = connected.has(node.dataset.nodeId);
      node.classList.toggle("focus", node.dataset.nodeId === nodeId);
      node.classList.toggle("neighbor", focused && node.dataset.nodeId !== nodeId);
      node.classList.toggle("dim", !focused);
    });
    container.querySelectorAll(".knowledge-3d-edge").forEach((edge, index) => {
      const source = edges[index]?.source;
      const target = edges[index]?.target;
      edge.classList.toggle("focus", source === nodeId || target === nodeId);
      edge.classList.toggle("dim", source !== nodeId && target !== nodeId);
    });
  }

  function clear3DHighlight(container) {
    container.querySelectorAll(".knowledge-3d-node, .knowledge-3d-edge").forEach((node) => {
      node.classList.remove("focus", "neighbor", "dim");
    });
  }

  function focus3DNode(point) {
    state.pan3d.x += ($("knowledgeGraphSvg").clientWidth || 1120) / 2 - point.x;
    state.pan3d.y += ($("knowledgeGraphSvg").clientHeight || 680) / 2 - point.y;
    state.zoom3d = clamp(state.zoom3d + 0.08, 0.28, 1.35);
    renderCurrentPayload();
  }

  function shortLabel(node) {
    const label = String(node.label || node.id);
    if (label.length <= 12) return label;
    return `${label.slice(0, 10)}...`;
  }

  function buildClusteredLayout(nodes, edges) {
    const degree = new Map();
    edges.forEach((edge) => {
      degree.set(edge.source, (degree.get(edge.source) || 0) + 1);
      degree.set(edge.target, (degree.get(edge.target) || 0) + 1);
    });
    const clusters = new Map();
    nodes.forEach((node) => {
      const cluster = clusterKey(node);
      if (!clusters.has(cluster)) clusters.set(cluster, []);
      clusters.get(cluster).push(node);
    });
    const layout = new Map();
    clusters.forEach((clusterNodes, cluster) => {
      const anchor = CLUSTER_ANCHORS[cluster] || CLUSTER_ANCHORS.misc;
      const sorted = clusterNodes.slice().sort((a, b) => {
        const scoreA = Number(a.importance || 0) + (degree.get(a.id) || 0);
        const scoreB = Number(b.importance || 0) + (degree.get(b.id) || 0);
        return scoreB - scoreA || String(a.id).localeCompare(String(b.id));
      });
      sorted.forEach((node, index) => {
        const nodeDegree = degree.get(node.id) || Number(node.degree || 0);
        const important = isImportantNode(node, nodeDegree, index);
        const angle = index * 2.399963229728653 + seeded(node.id, 0) * 0.025;
        const ring = Math.floor(Math.sqrt(index + 1));
        const radius = important && index === 0 ? 0 : 95 + ring * 58 + seeded(node.id, 1) * 3;
        const target = {
          x: clamp(anchor.x + Math.cos(angle) * radius, GRAPH_BOUNDS.minX, GRAPH_BOUNDS.maxX),
          y: clamp(anchor.y + Math.sin(angle) * radius * 0.72, GRAPH_BOUNDS.minY, GRAPH_BOUNDS.maxY),
        };
        const previous = state.layoutPositions.get(node.id);
        const stable = previous
          ? {
              x: clamp(previous.x * 0.82 + target.x * 0.18, GRAPH_BOUNDS.minX, GRAPH_BOUNDS.maxX),
              y: clamp(previous.y * 0.82 + target.y * 0.18, GRAPH_BOUNDS.minY, GRAPH_BOUNDS.maxY),
            }
          : target;
        state.layoutPositions.set(node.id, stable);
        layout.set(node.id, {
          ...stable,
          z: clusterDepth(cluster, index),
          cluster,
          degree: nodeDegree,
          important,
          size: visualNodeSize(node, nodeDegree, important),
        });
      });
    });
    relaxClusterForces(layout, nodes, edges);
    layout.forEach((position, id) => {
      state.layoutPositions.set(id, { x: position.x, y: position.y });
    });
    pruneOldLayoutPositions(nodes);
    return layout;
  }

  function clusterDepth(cluster, index) {
    const depth = {
      crypto: 180,
      stocks: 180,
      brain: 20,
      learning: -260,
      pattern: -210,
      decision: 120,
      system: -120,
      data: -80,
      misc: -180,
    };
    return (depth[cluster] || 0) + seeded(`${cluster}:${index}`, 2) * 12;
  }

  function relaxClusterForces(layout, nodes, edges) {
    const activeNodes = nodes.filter((node) => layout.has(node.id)).slice(0, 420);
    const activeIds = new Set(activeNodes.map((node) => node.id));
    const activeEdges = edges.filter((edge) => activeIds.has(edge.source) && activeIds.has(edge.target)).slice(0, 900);
    for (let iteration = 0; iteration < 14; iteration += 1) {
      activeNodes.forEach((node) => {
        const position = layout.get(node.id);
        const anchor = CLUSTER_ANCHORS[position.cluster] || CLUSTER_ANCHORS.misc;
        position.x += (anchor.x - position.x) * 0.012;
        position.y += (anchor.y - position.y) * 0.012;
      });
      for (let a = 0; a < activeNodes.length; a += 1) {
        for (let b = a + 1; b < activeNodes.length; b += 1) {
          const aNode = activeNodes[a];
          const bNode = activeNodes[b];
          const aPos = layout.get(aNode.id);
          const bPos = layout.get(bNode.id);
          const dx = bPos.x - aPos.x || 0.01;
          const dy = bPos.y - aPos.y || 0.01;
          const distance = Math.sqrt(dx * dx + dy * dy);
          const sameCluster = aPos.cluster === bPos.cluster;
          const minDistance = (sameCluster ? 92 : 138) + aPos.size + bPos.size;
          if (distance >= minDistance) continue;
          const push = (minDistance - distance) / distance * 0.18;
          const pushX = dx * push;
          const pushY = dy * push;
          aPos.x -= pushX;
          aPos.y -= pushY;
          bPos.x += pushX;
          bPos.y += pushY;
        }
      }
      activeEdges.forEach((edge) => {
        const source = layout.get(edge.source);
        const target = layout.get(edge.target);
        if (!source || !target) return;
        const dx = target.x - source.x || 0.01;
        const dy = target.y - source.y || 0.01;
        const distance = Math.sqrt(dx * dx + dy * dy);
        const sameCluster = source.cluster === target.cluster;
        const targetDistance = sameCluster ? 175 : 310;
        const pull = (distance - targetDistance) / distance * (sameCluster ? 0.018 : 0.007);
        const pullX = dx * pull;
        const pullY = dy * pull;
        source.x += pullX;
        source.y += pullY;
        target.x -= pullX;
        target.y -= pullY;
      });
      layout.forEach((position) => {
        position.x = clamp(position.x, GRAPH_BOUNDS.minX, GRAPH_BOUNDS.maxX);
        position.y = clamp(position.y, GRAPH_BOUNDS.minY, GRAPH_BOUNDS.maxY);
      });
    }
  }

  function clusterKey(node) {
    const haystack = `${node.type || ""} ${node.group || ""} ${node.community || ""} ${node.id || ""} ${node.label || ""}`.toLowerCase();
    if (haystack.includes("crypto") || haystack.includes("btcusdt") || haystack.includes("ethusdt") || haystack.includes("xrpusdt")) return "crypto";
    if (haystack.includes("stock") || haystack.includes("aapl") || haystack.includes("msft") || haystack.includes("nvda") || haystack.includes("tsla") || haystack.includes("spcx")) return "stocks";
    if (haystack.includes("brain") || haystack.includes("memory")) return "brain";
    if (haystack.includes("learning") || haystack.includes("learn")) return "learning";
    if (haystack.includes("pattern") || haystack.includes("indicator")) return "pattern";
    if (haystack.includes("decision") || haystack.includes("signal")) return "decision";
    if (haystack.includes("data") || haystack.includes("source") || haystack.includes("history")) return "data";
    if (haystack.includes("service") || haystack.includes("system") || haystack.includes("bot") || haystack.includes("error") || haystack.includes("warning")) return "system";
    return "misc";
  }

  function isImportantNode(node, degree, clusterIndex) {
    const type = String(node.type || "").toLowerCase();
    return clusterIndex === 0 || degree >= 6 || ["brain", "project", "cluster", "market", "system"].includes(type);
  }

  function visualNodeSize(node, degree = Number(node.degree || 0), important = false) {
    const rawSize = Number(node.size || 8);
    const importance = Number(node.importance || 0);
    const boost = Math.min(9, Math.log2(Math.max(1, degree + importance)) * 1.9);
    const type = String(node.type || "").toLowerCase();
    const typeBoost = ["brain", "project", "cluster", "market", "system"].includes(type) ? 4 : 0;
    return Math.max(5, Math.min(25, rawSize * 0.82 + boost + typeBoost + (important ? 1.5 : 0)));
  }

  function shouldRenderSigmaLabel(node, visual) {
    if (node.label_visible) return true;
    return Boolean(visual.important);
  }

  function pruneOldLayoutPositions(nodes) {
    const live = new Set(nodes.map((node) => node.id));
    Array.from(state.layoutPositions.keys()).forEach((id) => {
      if (!live.has(id)) state.layoutPositions.delete(id);
    });
  }

  function highlight(nodeId) {
    const graph = state.rendererGraph;
    if (!graph || !state.sigma) return;
    const neighbors = new Set(graph.neighbors(nodeId));
    neighbors.add(nodeId);
    graph.forEachNode((node) => {
      graph.setNodeAttribute(node, "hidden", false);
      graph.setNodeAttribute(node, "color", neighbors.has(node) ? nodeColor(node) : "rgba(90, 101, 112, 0.34)");
      graph.setNodeAttribute(node, "size", neighbors.has(node) ? graph.getNodeAttribute(node, "baseSize") * 1.1 : graph.getNodeAttribute(node, "baseSize") * 0.82);
      graph.setNodeAttribute(node, "label", neighbors.has(node) ? graph.getNodeAttribute(node, "fullLabel") : "");
    });
    graph.forEachEdge((edge, attrs, source, target) => {
      const focused = neighbors.has(source) && neighbors.has(target);
      graph.setEdgeAttribute(edge, "hidden", false);
      graph.setEdgeAttribute(edge, "color", focused ? "rgba(93, 182, 255, 0.72)" : "rgba(80, 92, 105, 0.08)");
      graph.setEdgeAttribute(edge, "size", focused ? attrs.baseSize * 1.45 : Math.max(0.15, attrs.baseSize * 0.55));
    });
    state.sigma.refresh();
  }

  function bindSigmaDragging() {
    if (!state.sigma || !state.rendererGraph) return;
    const sigma = state.sigma;
    const graph = state.rendererGraph;
    sigma.on("downNode", ({ node }) => {
      state.draggedNode = node;
      graph.setNodeAttribute(node, "highlighted", true);
      if (sigma.getMouseCaptor && sigma.getMouseCaptor()) {
        sigma.getMouseCaptor().disable();
      }
    });
    sigma.getMouseCaptor().on("mousemovebody", (event) => {
      if (!state.draggedNode) return;
      const position = sigma.viewportToGraph(event);
      const bounded = {
        x: clamp(position.x, GRAPH_BOUNDS.minX, GRAPH_BOUNDS.maxX),
        y: clamp(position.y, GRAPH_BOUNDS.minY, GRAPH_BOUNDS.maxY),
      };
      graph.setNodeAttribute(state.draggedNode, "x", bounded.x);
      graph.setNodeAttribute(state.draggedNode, "y", bounded.y);
      state.layoutPositions.set(state.draggedNode, bounded);
      sigma.refresh();
    });
    sigma.getMouseCaptor().on("mouseup", stopNodeDrag);
    sigma.getMouseCaptor().on("mouseupbody", stopNodeDrag);
    function stopNodeDrag() {
      if (!state.draggedNode) return;
      graph.removeNodeAttribute(state.draggedNode, "highlighted");
      state.draggedNode = null;
      if (sigma.getMouseCaptor && sigma.getMouseCaptor()) {
        sigma.getMouseCaptor().enable();
      }
    }
  }

  function focusCameraOnNode(attrs, duration = 500) {
    if (!state.sigma || !attrs) return;
    state.sigma.getCamera().animate(
      { x: attrs.x, y: attrs.y, ratio: 0.42 },
      { duration }
    );
  }

  function clearHighlight() {
    const graph = state.rendererGraph;
    if (!graph || !state.sigma) return;
    graph.forEachNode((node, attrs) => {
      graph.setNodeAttribute(node, "color", nodeColor(node));
      graph.setNodeAttribute(node, "size", attrs.baseSize);
      graph.setNodeAttribute(node, "label", attrs.labelVisible ? attrs.fullLabel : "");
    });
    graph.forEachEdge((edge, attrs) => {
      graph.setEdgeAttribute(edge, "hidden", false);
      graph.setEdgeAttribute(edge, "color", attrs.baseColor || "rgba(160, 174, 188, 0.18)");
      graph.setEdgeAttribute(edge, "size", attrs.baseSize || 0.5);
    });
    state.sigma.refresh();
  }

  function nodeColor(nodeId) {
    const attrs = state.rendererGraph.getNodeAttributes(nodeId);
    return attrs.baseColor || COLORS[attrs.nodeType] || COLORS[attrs.group] || "#b8c2cc";
  }

  function nodeColorFromData(node) {
    return COLORS[node.type] || COLORS[node.group] || "#b8c2cc";
  }

  function edgeSize(edge) {
    const visual = Number(edge.visual_weight || edge.weight || 1);
    return Math.max(0.18, Math.min(3.0, visual * 0.42));
  }

  function edgeColor(edge) {
    const opacity = Number(edge.visual_opacity || (edge.cross_cluster ? 0.08 : 0.16));
    return `rgba(160, 174, 188, ${Math.max(0.04, Math.min(0.30, opacity)).toFixed(2)})`;
  }

  async function search() {
    const query = $("knowledgeGraphSearch").value.trim();
    if (!query) return;
    const payload = await requestJson(`/api/v1/graph/search?q=${encodeURIComponent(query)}`);
    if (!payload.nodes || !payload.nodes.length) {
      setText("knowledgeGraphStatus", "Kein Treffer");
      return;
    }
    const first = payload.nodes[0];
    state.selected = first.id;
    await loadProjection("neighborhood", { nodeId: first.id });
    window.setTimeout(() => {
      if (!state.rendererGraph || !state.rendererGraph.hasNode(first.id)) return;
      focusCameraOnNode(state.rendererGraph.getNodeAttributes(first.id), 650);
      highlight(first.id);
    }, 80);
  }

  function populateFilters(nodes) {
    populateSelect("knowledgeGraphTypeFilter", unique(nodes.map((node) => node.type)), "Alle Typen");
    populateSelect("knowledgeGraphGroupFilter", unique(nodes.flatMap((node) => [node.group, node.community]).filter(Boolean)), "Alle Cluster");
  }

  function populateSelect(id, values, label) {
    const select = $(id);
    const previous = select.value;
    select.innerHTML = "";
    const empty = document.createElement("option");
    empty.value = "";
    empty.textContent = label;
    select.appendChild(empty);
    values.forEach((value) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = value;
      select.appendChild(option);
    });
    select.value = values.includes(previous) ? previous : "";
  }

  function fitCamera() {
    if (!state.sigma) return;
    state.sigma.getCamera().animatedReset({ duration: 650 });
  }

  function updateModeButtons() {
    const overview = $("knowledgeOverviewMode");
    const full = $("knowledgeFullMode");
    if (overview) overview.classList.toggle("active", state.mode === "overview");
    if (full) full.classList.toggle("active", state.mode === "full");
  }

  function renderStats(payload) {
    setText("knowledgeNodeCount", payload.node_count ?? (payload.nodes || []).length);
    setText("knowledgeEdgeCount", payload.edge_count ?? (payload.edges || []).length);
    setText("knowledgeVersion", payload.version ?? "-");
    setText("knowledgeUpdated", time(payload.generated_at));
    renderDiagnostics(payload);
  }

  function renderDiagnostics(payload) {
    const diagnostics = payload.diagnostics || {};
    const bounds = diagnostics.bounds || {};
    setText("knowledgeProjection", diagnostics.projection || payload.mode || state.mode);
    setText("knowledgeCommunities", diagnostics.communities ?? "-");
    setText("knowledgeFa2Iterations", diagnostics.forceatlas2_iterations ?? 0);
    setText("knowledgeLayoutRuntime", diagnostics.forceatlas2_runtime_ms ?? 0);
    setText("knowledgeBoundsX", `${number(bounds.min_x)} / ${number(bounds.max_x)}`);
    setText("knowledgeBoundsY", `${number(bounds.min_y)} / ${number(bounds.max_y)}`);
    setText("knowledgeOverlaps", diagnostics.overlapping_nodes ?? 0);
    setText("knowledgeIsolated", diagnostics.isolated_nodes ?? 0);
    setText("knowledgeDuplicatePositions", diagnostics.duplicate_positions ?? 0);
  }

  function logDiagnostics(payload, renderer) {
    const diagnostics = payload.diagnostics || {};
    console.info("[Pandorick Knowledge Graph]", {
      renderer,
      webgl_available: Boolean(window.WebGLRenderingContext),
      sigma_initialized: Boolean(state.sigma),
      graphology_loaded: Boolean(window.graphology),
      forceatlas2_started: Boolean(diagnostics.forceatlas2_started),
      forceatlas2_finished: Boolean(diagnostics.forceatlas2_finished),
      forceatlas2_iterations: diagnostics.forceatlas2_iterations || 0,
      layout_runtime_ms: diagnostics.forceatlas2_runtime_ms || 0,
      nodes: payload.node_count,
      edges: payload.edge_count,
      communities: diagnostics.communities,
      bounds: diagnostics.bounds,
      duplicate_positions: diagnostics.duplicate_positions,
      overlapping_nodes: diagnostics.overlapping_nodes,
      isolated_nodes: diagnostics.isolated_nodes,
    });
  }

  function renderDetails(node) {
    const panel = $("knowledgeGraphDetails");
    if (!node) {
      panel.className = "details empty";
      panel.textContent = state.mode === "overview" ? "Knoten anklicken fuer Nachbarschaft" : "Noch kein Knoten ausgewaehlt";
      return;
    }
    panel.className = "details";
    const rows = [
      ["Name", node.label],
      ["Typ", node.type],
      ["Cluster", node.group],
      ["Community", node.community],
      ["Status", node.status],
      ["Health", node.health],
      ["Degree", node.degree],
      ["Size", node.size],
      ["Confidence", node.confidence === undefined ? "-" : `${Number(node.confidence).toFixed(2)} %`],
      ["Update", time(node.last_updated)],
    ];
    panel.innerHTML = `<div class="graph-detail-grid">${rows.map(([k, v]) => `<span>${escapeHtml(k)}</span><strong>${escapeHtml(v ?? "-")}</strong>`).join("")}</div>`;
  }

  function renderLegend() {
    const legend = $("knowledgeGraphLegend");
    legend.innerHTML = "";
    Object.entries(COLORS).forEach(([type, color]) => {
      const row = document.createElement("div");
      row.className = "knowledge-legend-row";
      row.innerHTML = "<span class=\"knowledge-legend-dot\"></span><span></span>";
      row.children[0].style.background = color;
      row.children[1].textContent = type;
      legend.appendChild(row);
    });
  }

  function toggleFullscreen() {
    document.querySelector(".knowledge-panel").classList.toggle("fullscreen");
    window.setTimeout(() => {
      if (state.sigma) state.sigma.refresh();
    }, 120);
  }

  function findNode(payload, id) {
    return (payload.nodes || []).find((node) => node.id === id);
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

  function seeded(id, salt) {
    let hash = salt + 7;
    String(id).split("").forEach((char) => {
      hash = (hash * 31 + char.charCodeAt(0)) >>> 0;
    });
    return ((hash % 2000) / 100) - 10;
  }

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, Number(value)));
  }

  function setText(id, value) {
    const node = $(id);
    if (node) node.textContent = value === null || value === undefined || value === "" ? "-" : value;
  }

  function time(value) {
    if (!value) return "-";
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? value : date.toLocaleTimeString();
  }

  function number(value) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
    return Number(value).toFixed(2);
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

  if (document.readyState === "loading") {
    window.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
}());
