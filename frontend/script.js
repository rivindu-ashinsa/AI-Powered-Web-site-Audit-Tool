const BACKEND_BASE_URL = "https://ai-powered-web-site-audit-tool.onrender.com";

function esc(value) {
  const stringValue = String(value == null ? "" : value);
  return stringValue
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function metricCard(label, value, toneClass) {
  return (
    '<div class="rounded-xl border border-slate-700 bg-slate-950/60 p-4">' +
      '<p class="text-xs uppercase tracking-wide text-slate-400">' + esc(label) + '</p>' +
      '<p class="mt-2 text-2xl font-extrabold ' + toneClass + '">' + esc(value) + '</p>' +
    '</div>'
  );
}

function metricWideCard(label, value) {
  return (
    '<div class="rounded-xl border border-slate-700 bg-slate-950/60 p-4 sm:col-span-2 lg:col-span-4">' +
      '<p class="text-xs uppercase tracking-wide text-slate-400">' + esc(label) + '</p>' +
      '<p class="mt-2 text-sm md:text-base font-semibold text-slate-200 break-all leading-6">' + esc(value || "N/A") + '</p>' +
    '</div>'
  );
}

function insightCard(title, text) {
  return (
    '<article class="rounded-xl border border-slate-700 bg-slate-950/60 p-4">' +
      '<h3 class="text-sm uppercase tracking-wide text-cyan-300 font-semibold">' + esc(title) + '</h3>' +
      '<p class="mt-2 text-slate-200 leading-6">' + esc(text || "No insight generated.") + '</p>' +
    '</article>'
  );
}

function recommendationCard(item, index) {
  const priority = (item.priority || "medium").toString().toLowerCase();
  const badge = priority === "high"
    ? "bg-rose-500/20 text-rose-300 border-rose-400/40"
    : priority === "low"
      ? "bg-emerald-500/20 text-emerald-300 border-emerald-400/40"
      : "bg-amber-500/20 text-amber-300 border-amber-400/40";

  return (
    '<article class="rounded-xl border border-slate-700 bg-slate-950/60 p-4">' +
      '<div class="flex flex-wrap items-center gap-2 mb-3">' +
        '<span class="text-xs font-semibold px-2 py-1 rounded-md border ' + badge + '">' + esc(priority.toUpperCase()) + '</span>' +
        '<span class="text-xs text-slate-400">Recommendation ' + esc(index + 1) + '</span>' +
      '</div>' +
      '<p class="text-slate-100"><span class="font-semibold text-slate-300">Issue:</span> ' + esc(item.issue || "") + '</p>' +
      '<p class="text-slate-100 mt-2"><span class="font-semibold text-slate-300">Action:</span> ' + esc(item.action || "") + '</p>' +
      '<p class="text-slate-300 mt-2"><span class="font-semibold text-slate-400">Rationale:</span> ' + esc(item.rationale || "") + '</p>' +
    '</article>'
  );
}

async function runAudit() {
  const url = document.getElementById("urlInput").value.trim();
  const loadingWrap = document.getElementById("loadingWrap");
  const errorText = document.getElementById("errorText");
  const results = document.getElementById("results");
  const analyzeBtn = document.getElementById("analyzeBtn");
  const metricsGrid = document.getElementById("metricsGrid");
  const insightsGrid = document.getElementById("insightsGrid");
  const recommendationsList = document.getElementById("recommendationsList");

  if (!url) {
    errorText.textContent = "Please enter a valid URL.";
    errorText.classList.remove("hidden");
    return;
  }

  errorText.classList.add("hidden");
  loadingWrap.classList.remove("hidden");
  results.classList.add("hidden");
  analyzeBtn.disabled = true;

  try {
    let backendBase;
    try {
      backendBase = new URL(BACKEND_BASE_URL).origin;
    } catch (_error) {
      throw new Error("Frontend config error: BACKEND_BASE_URL is invalid.");
    }

    const endpoint = `${backendBase}/audit?url=${encodeURIComponent(url)}`;
    const response = await fetch(endpoint, { method: "GET" });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Audit request failed.");
    }

    const metrics = data.metrics || {};
    const insights = data.ai_insights || {};
    const recommendations = data.recommendations || [];
    const headingCounts = metrics.heading_counts || {};

    metricsGrid.innerHTML =
      metricWideCard("Final URL", metrics.url || "N/A") +
      metricCard("Word Count", metrics.word_count || 0, "text-cyan-300") +
      metricCard("CTA Count", metrics.cta_count || 0, "text-blue-300") +
      metricCard("Internal Links", metrics.internal_links || 0, "text-emerald-300") +
      metricCard("External Links", metrics.external_links || 0, "text-amber-300") +
      metricCard("H1", headingCounts.h1 || 0, "text-fuchsia-300") +
      metricCard("H2", headingCounts.h2 || 0, "text-fuchsia-300") +
      metricCard("H3", headingCounts.h3 || 0, "text-fuchsia-300") +
      metricCard("Images", metrics.images || 0, "text-indigo-300") +
      metricCard("Missing Alt %", (metrics.images_missing_alt_pct || 0) + "%", "text-rose-300") +
      metricCard("Meta Title", metrics.meta_title ? "Present" : "Missing", metrics.meta_title ? "text-emerald-300" : "text-rose-300") +
      metricCard("Meta Description", metrics.meta_description ? "Present" : "Missing", metrics.meta_description ? "text-emerald-300" : "text-rose-300");

    insightsGrid.innerHTML =
      insightCard("SEO Structure", insights.seo_structure) +
      insightCard("Messaging Clarity", insights.messaging_clarity) +
      insightCard("CTA Usage", insights.cta_usage) +
      insightCard("Content Depth", insights.content_depth) +
      insightCard("UX Concerns", insights.ux_concerns);

    recommendationsList.innerHTML = "";
    if (recommendations.length === 0) {
      recommendationsList.innerHTML = '<p class="text-slate-400">No recommendations generated.</p>';
    } else {
      recommendations.forEach(function (item, index) {
        recommendationsList.innerHTML += recommendationCard(item, index);
      });
    }

    results.classList.remove("hidden");
  } catch (error) {
    errorText.textContent = (error && error.message) ? error.message : "Unexpected error.";
    errorText.classList.remove("hidden");
  } finally {
    loadingWrap.classList.add("hidden");
    analyzeBtn.disabled = false;
  }
}

document.getElementById("analyzeBtn").addEventListener("click", runAudit);
