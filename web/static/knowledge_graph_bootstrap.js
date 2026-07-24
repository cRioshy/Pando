(function () {
  function $(id) {
    return document.getElementById(id);
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

  function setStatus(text) {
    const status = $("knowledgeGraphStatus");
    if (status) status.textContent = text;
  }

  function setText(id, value) {
    const node = $(id);
    if (node) node.textContent = value;
  }

  function loadLegacy() {
    if (window.PandorickLegacyKnowledgeGraph) {
      window.PandorickLegacyKnowledgeGraph.init();
      return;
    }
    if (!$("knowledgeLegacyCss")) {
      const css = document.createElement("link");
      css.id = "knowledgeLegacyCss";
      css.rel = "stylesheet";
      css.href = "/knowledge_graph_legacy.css?v=sigma-engine-2";
      document.head.appendChild(css);
    }
    const script = document.createElement("script");
    script.src = "/knowledge_graph_legacy.js?v=sigma-engine-3";
    script.onload = function () {
      if (window.PandorickLegacyKnowledgeGraph) {
        window.PandorickLegacyKnowledgeGraph.init();
      }
    };
    script.onerror = function () {
      setStatus("Knowledge Graph Fallback konnte nicht geladen werden");
    };
    document.body.appendChild(script);
  }

  function watchdog() {
    const status = $("knowledgeGraphStatus");
    const nodes = $("knowledgeNodeCount");
    const canvas = document.querySelector("#knowledgeGraphSvg canvas");
    const renderedLegacyNodes = document.querySelectorAll("#knowledgeGraphSvg .kg-node").length;
    const stillConnecting = !status || status.textContent === "Verbinde...";
    const sigmaLoading = $("knowledgeRenderer") && $("knowledgeRenderer").textContent === "Sigma laedt";
    const noRenderedGraph = !canvas && renderedLegacyNodes === 0 && (!nodes || nodes.textContent === "0");
    if (sigmaLoading) return;
    if (!stillConnecting && !noRenderedGraph) return;
    restoreSvgContainer();
    setStatus("WebGL/Sigma nicht verfuegbar. Fallback-Ansicht aktiv.");
    setText("knowledgeRenderer", "SVG Fallback");
    console.info("[Pandorick Knowledge Graph]", {
      renderer: "SVG Fallback",
      webgl_available: Boolean(window.WebGLRenderingContext),
      sigma_initialized: Boolean(window.Sigma),
      graphology_loaded: Boolean(window.graphology),
      forceatlas2_started: false,
      forceatlas2_finished: false,
    });
    loadLegacy();
  }

  window.setTimeout(watchdog, 20000);
}());
