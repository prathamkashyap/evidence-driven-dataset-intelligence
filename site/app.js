const stageContent = [
  { title: "A task frames the decision.", description: "The evaluated system receives a structured TaskSpecification and a supplied pool. M8 reuses the same frozen 24-record pool for every task; it does not measure live search recall.", visual: ["TASK", "image classification", "POOL", "24 records"] },
  { title: "Normalize without losing the source.", description: "Source adapters map repository-specific metadata into canonical fields while keeping native values and provenance attached to the record.", visual: ["SOURCE", "native metadata", "CANONICAL", "dataset record"] },
  { title: "Evidence has a scope.", description: "The ledger keeps claims and observations distinct. Fingerprinting inspects a bounded sample; that observation does not become a claim about every record in the full dataset.", visual: ["LEDGER", "claim + observation", "SAMPLE", "bounded probe"] },
  { title: "Confirmed conflicts stop here.", description: "Three hard gates check confirmed modality clashes, prohibited license claims, and required anonymous access on a gated source. A missing modality record is not treated as a mismatch.", visual: ["CANDIDATE", "confirmed compatible", "GATE", "eligible"] },
  { title: "Rank, then choose a set.", description: "Eligible candidates receive fixed heuristic scores. The deterministic greedy selector adds a diversity contribution and excludes candidates identified as same-family mirrors of items already selected.", visual: ["SCORE", "heuristic terms", "SELECT", "up to k = 3"] },
  { title: "Keep the reasons attached.", description: "Recommendation cards retain scores, evidence identifiers, fingerprint scope, and reasons, so readers can inspect why an item was returned and what remains uncertain.", visual: ["CARD", "evidence IDs", "CAVEAT", "unknown stays visible"] }
];

const candidates = [
  { name: "Leaf Canopy Images", source: "Illustrative source A", modality: "image", evidence: "observed", fit: "task fit  ·  0.88" },
  { name: "Iris Measurements", source: "Illustrative source B", modality: "tabular", evidence: "observed", fit: "task fit  ·  0.94" },
  { name: "Field Notes Corpus", source: "Illustrative source C", modality: "text", evidence: "observed", fit: "task fit  ·  0.81" },
  { name: "Road Sign Frames", source: "Illustrative source D", modality: "image", evidence: "observed", fit: "task fit  ·  0.76" },
  { name: "Mixed Sensor Archive", source: "Illustrative source E", modality: "not established", evidence: "unknown", fit: "task fit  ·  —" }
];

const milestones = [
  ["M0", "Compute envelope", "Measure a local resource and access envelope to bound the later experiments."],
  ["M1", "Canonical schema", "Normalize multi-source records while retaining source provenance."],
  ["M2", "Retrieval baselines", "Compare lexical, dense, and hybrid methods on a small development benchmark."],
  ["M3", "Evidence ledger", "Represent evidence entries and their resolution with separate categorical states."],
  ["M4", "Bounded fingerprinting", "Inspect small samples and record descriptive content observations."],
  ["M5", "Task utility", "Estimate task fit and apply confirmed hard constraints before ranking."],
  ["M6", "Popularity audit", "Audit exposure and analyze a popularity-neutral exploration pool."],
  ["M7", "Set selection", "Compare heuristic scoring and family-aware greedy diversification."],
  ["M8", "Frozen benchmark", "Evaluate the integrated offline path, robustness, sensitivity, and an exploratory card pilot."]
];

const byId = (id) => document.getElementById(id);
const safeText = (value) => String(value).replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);

function makePipelineVisual(items) {
  const container = byId("pipeline-visual");
  container.innerHTML = `<div class="flow-chip">${safeText(items[0])}<b>${safeText(items[1])}</b></div><span class="flow-arrow" aria-hidden="true">→</span><div class="pool-dots"><i></i><i></i><i></i><i></i><i></i><i></i></div><span class="flow-arrow" aria-hidden="true">→</span><div class="flow-chip output">${safeText(items[2])}<b>${safeText(items[3])}</b></div>`;
}

function initPipeline() {
  const tabs = [...document.querySelectorAll(".pipeline-step")];
  const setStage = (index, focus = false) => {
    const item = stageContent[index];
    tabs.forEach((tab, i) => {
      tab.classList.toggle("active", i === index);
      tab.setAttribute("aria-selected", String(i === index));
      tab.tabIndex = i === index ? 0 : -1;
    });
    byId("stage-panel").setAttribute("aria-labelledby", tabs[index].id);
    byId("stage-label").textContent = `STAGE ${String(index + 1).padStart(2, "0")} / 06`;
    byId("stage-title").textContent = item.title;
    byId("stage-description").textContent = item.description;
    makePipelineVisual(item.visual);
    if (focus) tabs[index].focus();
  };
  tabs.forEach((tab, index) => {
    tab.addEventListener("click", () => setStage(index));
    tab.addEventListener("keydown", (event) => {
      let next = index;
      if (event.key === "ArrowDown" || event.key === "ArrowRight") next = (index + 1) % tabs.length;
      else if (event.key === "ArrowUp" || event.key === "ArrowLeft") next = (index - 1 + tabs.length) % tabs.length;
      else if (event.key === "Home") next = 0;
      else if (event.key === "End") next = tabs.length - 1;
      else return;
      event.preventDefault(); setStage(next, true);
    });
  });
}

function renderCandidates() {
  const required = byId("required-modality").value;
  const gated = byId("gate-toggle").checked;
  let matching = 0, excluded = 0, mismatchRetained = 0, unknown = 0;
  byId("candidate-list").innerHTML = candidates.map((candidate) => {
    const isUnknown = candidate.evidence === "unknown";
    const isMismatch = !isUnknown && candidate.modality !== required;
    const isExcluded = gated && isMismatch;
    if (isUnknown) unknown += 1;
    else if (isMismatch && isExcluded) excluded += 1;
    else if (isMismatch) mismatchRetained += 1;
    else matching += 1;
    const status = isUnknown ? "Unknown · needs evidence" : isExcluded ? "Excluded · confirmed mismatch" : isMismatch ? "Included · modality mismatch" : gated ? "Eligible · passes gate" : "Included · requirement matches";
    const classes = ["candidate-card", isUnknown ? "is-unknown" : "", isExcluded ? "is-excluded" : ""].filter(Boolean).join(" ");
    const modality = isUnknown ? "modality unknown" : `${candidate.modality} · observed`;
    return `<article class="${classes}"><div><b class="candidate-name">${safeText(candidate.name)}</b><small class="candidate-meta">${safeText(candidate.source)} · ${safeText(modality)}</small></div><span class="candidate-fit">${safeText(candidate.fit)}</span><span class="candidate-status">${safeText(status)}</span></article>`;
  }).join("");
  byId("pool-count").textContent = `${candidates.length} RECORDS`;
  byId("gate-summary").textContent = gated
    ? `${matching} eligible · ${excluded} excluded · ${unknown} unknown`
    : `${matching} match · ${mismatchRetained} mismatch retained · ${unknown} unknown`;
}

const observationCopy = {
  observed: "A bounded sample probe observed 32 records.",
  single_source_claim: "A repository metadata field claims the dataset contains images.",
  unsupported: "This sampling route is unavailable under the current source policy or capability. No content value is inferred.",
  failed: "A supported source request was attempted but encountered an operational failure. This is not evidence of absence.",
  unknown: "The modality property has not been established from available evidence."
};
const resolutionCopy = {
  corroborated: "Two evidence entries align on a claim; this describes their agreement, not calibrated certainty.",
  conflicting: "Evidence entries disagree, so the conflict remains visible for downstream decisions.",
  unresolved: "More than one entry exists, but the record has not been reconciled.",
  unknown: "There is not enough evidence to characterize agreement across entries."
};

function initEvidence() {
  document.querySelectorAll("[data-state]").forEach((button) => button.addEventListener("click", () => {
    document.querySelectorAll("[data-state]").forEach((item) => {
      item.classList.toggle("selected", item === button);
      item.setAttribute("aria-pressed", String(item === button));
    });
    byId("evidence-example").textContent = observationCopy[button.dataset.state];
  }));
  document.querySelectorAll("[data-resolution]").forEach((button) => button.addEventListener("click", () => {
    document.querySelectorAll("[data-resolution]").forEach((item) => {
      item.classList.toggle("selected", item === button);
      item.setAttribute("aria-pressed", String(item === button));
    });
    byId("evidence-explainer-text").textContent = resolutionCopy[button.dataset.resolution];
  }));
}

function initEquation() {
  const slider = byId("diversity-slider");
  const value = Number(slider.value);
  const update = () => {
    const current = Number(slider.value);
    byId("diversity-value").value = current.toFixed(2);
    byId("diversity-value").textContent = current.toFixed(2);
    byId("diversity-multiplier").textContent = `${current.toFixed(2)} × δ`;
    const term = current * 0.2;
    byId("diversity-term-value").textContent = term.toFixed(2);
    byId("diversity-fill").style.width = `${Math.min(100, term / 0.08 * 100)}%`;
    slider.style.setProperty("--range-progress", `${current / 0.4 * 100}%`);
  };
  slider.value = value;
  slider.addEventListener("input", update);
  update();
}

function svgLineChart(svg, series, maximum, selectedWeight, cssClass, label) {
  const width = 520, height = 185, left = 36, right = 12, top = 12, bottom = 30;
  const x = (index) => left + index * (width - left - right) / (series.length - 1);
  const y = (value) => top + (1 - value / maximum) * (height - top - bottom);
  const pointString = series.map((d, i) => `${x(i)},${y(d.value)}`).join(" ");
  const grid = [0, maximum / 2, maximum].map((n) => `<line class="gridline" x1="${left}" y1="${y(n)}" x2="${width - right}" y2="${y(n)}"/><text class="axis-label" x="2" y="${y(n) + 3}">${n.toFixed(n === 0 ? 0 : 2)}</text>`).join("");
  const labels = series.map((d, i) => `<text class="axis-label" text-anchor="middle" x="${x(i)}" y="${height - 7}">${d.weight.toFixed(2)}</text>`).join("");
  const points = series.map((d, i) => {
    const isSelected = d.weight === selectedWeight;
    return `<circle class="data-point ${isSelected ? "selected" : ""}" cx="${x(i)}" cy="${y(d.value)}" r="5" tabindex="0" role="button" data-weight="${d.weight.toFixed(2)}" aria-label="${label} at diversity weight ${d.weight.toFixed(2)}: ${d.value.toFixed(6)}" aria-valuetext="${d.value.toFixed(6)}" aria-pressed="${isSelected}"/>`;
  }).join("");
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.classList.toggle("diversity-series", cssClass === "diversity-series");
  svg.innerHTML = `${grid}<polyline class="series-line" points="${pointString}"/>${points}${labels}`;
}

function initCharts(data) {
  const chart = byId("ablation-chart");
  const detail = byId("ablation-detail");
  const setAblation = (index) => {
    const entry = data.ablation[index];
    chart.querySelectorAll(".bar-item").forEach((bar, i) => { bar.classList.toggle("selected", i === index); bar.setAttribute("aria-pressed", String(i === index)); });
    detail.querySelector(".detail-value").textContent = entry.value.toFixed(4);
    detail.querySelector("b").textContent = `${entry.name} · R${entry.rung}`;
    detail.querySelector("p").textContent = entry.components;
  };
  chart.innerHTML = data.ablation.map((entry, index) => `<button class="bar-item ${entry.rung === 8 ? "selected" : ""}" type="button" aria-label="Rung ${entry.rung}, ${safeText(entry.name)}, mean set utility ${entry.value.toFixed(4)}" aria-pressed="${entry.rung === 8}" data-index="${index}"><span class="bar-value">${entry.value.toFixed(2)}</span><span class="bar-shape" style="height:${entry.value * 146}px"></span><span class="bar-label">${safeText(entry.name)}</span></button>`).join("");
  chart.querySelectorAll(".bar-item").forEach((bar) => bar.addEventListener("click", () => setAblation(Number(bar.dataset.index))));
  const points = data.diversitySweep;
  let selectedWeight = 0.2;
  const updateTradeoff = () => {
    svgLineChart(byId("utility-chart"), points.map((item) => ({ weight: item.weight, value: item.utility })), 1, selectedWeight, "utility-series", "Mean utility");
    svgLineChart(byId("diversity-chart"), points.map((item) => ({ weight: item.weight, value: item.diversity })), 0.7, selectedWeight, "diversity-series", "Mean diversity");
    const selected = points.find((item) => item.weight === selectedWeight);
    byId("utility-selected").textContent = `λ ${selected.weight.toFixed(2)} · utility ${selected.utility.toFixed(6)}`;
    byId("diversity-selected").textContent = `λ ${selected.weight.toFixed(2)} · diversity ${selected.diversity.toFixed(6)}`;
    document.querySelectorAll(".line-chart .data-point").forEach((point) => {
      point.addEventListener("click", () => { selectedWeight = Number(point.dataset.weight); updateTradeoff(); });
      point.addEventListener("keydown", (event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); selectedWeight = Number(point.dataset.weight); updateTradeoff(); } });
    });
  };
  updateTradeoff();
  byId("task-table-body").innerHTML = data.taskAttribution.map((item) => `<tr><td>${safeText(item.task)}</td><td>${item.utilityAtDefault.toFixed(4)}</td><td>${item.diversityAtDefault.toFixed(4)}</td><td>${item.utilityAtHigh.toFixed(4)}</td><td>${item.diversityAtHigh.toFixed(4)}</td><td>${item.jaccard.toFixed(1)}</td></tr>`).join("");
  byId("sweep-table-body").innerHTML = points.map((item) => `<tr><td>${item.weight.toFixed(2)}</td><td>${item.utility.toFixed(6)}</td><td>${item.diversity.toFixed(6)}</td><td>${item.jaccard.toFixed(4)}</td></tr>`).join("");
}

function initTimeline() {
  const host = byId("timeline");
  host.innerHTML = milestones.map((item, index) => `<button type="button" class="milestone ${index === 8 ? "selected" : ""}" role="tab" aria-selected="${index === 8}" aria-label="${item[0]} ${item[1]}" data-index="${index}"><span class="mile-dot">${item[0]}</span><span class="mile-label">${item[0]}</span></button>`).join("");
  const activate = (index) => {
    host.querySelectorAll(".milestone").forEach((button, i) => { button.classList.toggle("selected", i === index); button.setAttribute("aria-selected", String(i === index)); });
    byId("timeline-detail").innerHTML = `<span class="mono">${milestones[index][0]} · ${safeText(milestones[index][1].toUpperCase())}</span><p>${safeText(milestones[index][2])}</p>`;
  };
  host.querySelectorAll(".milestone").forEach((button) => button.addEventListener("click", () => activate(Number(button.dataset.index))));
}

function initHeader() {
  const toggle = document.querySelector(".menu-toggle");
  const menu = byId("mobile-nav");
  toggle.addEventListener("click", () => {
    const expanded = toggle.getAttribute("aria-expanded") === "true";
    toggle.setAttribute("aria-expanded", String(!expanded)); menu.hidden = expanded;
  });
  menu.querySelectorAll("a").forEach((link) => link.addEventListener("click", () => { menu.hidden = true; toggle.setAttribute("aria-expanded", "false"); }));
  const progress = byId("reading-progress");
  const updateProgress = () => {
    const max = document.documentElement.scrollHeight - window.innerHeight;
    progress.style.width = `${max > 0 ? window.scrollY / max * 100 : 0}%`;
  };
  window.addEventListener("scroll", updateProgress, { passive: true }); updateProgress();
}

async function init() {
  initPipeline(); initHeader(); initEvidence(); initEquation(); initTimeline();
  byId("required-modality").addEventListener("change", renderCandidates);
  byId("gate-toggle").addEventListener("change", renderCandidates);
  renderCandidates();
  const response = await fetch("data/research.json");
  if (!response.ok) throw new Error("Could not load the versioned research data.");
  const data = await response.json();
  document.querySelector('[data-stat="datasets"]').textContent = data.benchmark.datasets;
  document.querySelector('[data-stat="tasks"]').textContent = data.benchmark.tasks;
  document.querySelector('[data-stat="pairs"]').textContent = data.benchmark.pairs;
  initCharts(data);
}

init().catch((error) => {
  console.error(error);
  const chart = byId("ablation-chart");
  if (chart) chart.innerHTML = `<p class="chart-subtitle">The interactive result data could not be loaded. Serve this directory over HTTP to view the charts. Source values are in <code>data/research.json</code>.</p>`;
});
