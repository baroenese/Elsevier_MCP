/* Elsevier MCP Web UI — jQuery + Tailwind v4 (browser build), no build step. */
/* global $, Chart */
"use strict";

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const $status = (id, msg, isError) => {
  const $el = $("#" + id).removeClass("status-error").text(msg || "");
  if (isError) $el.addClass("status-error");
};

const fmt = (n) => Number(n ?? 0).toLocaleString();

function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

const prefersDark = () => window.matchMedia("(prefers-color-scheme: dark)").matches;

// ---------------------------------------------------------------- tabs
$(".tab").on("click", function () {
  const active = [
    "text-zinc-900", "dark:text-zinc-100", "border-orange-600", "dark:border-orange-500",
  ];
  const idle = ["text-zinc-500", "dark:text-zinc-400", "hover:text-zinc-900", "dark:hover:text-zinc-100"];
  $(".tab").removeClass([...active, ...idle].join(" "));
  $(this).addClass((active).join(" "));
  $(".tab").not(this).addClass(idle.join(" "));
  $(".panel").addClass("hidden");
  $("#tab-" + $(this).data("tab")).removeClass("hidden");
});
$(".tab").not(".tab[data-tab=search]").addClass("text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100");
$(".tab[data-tab=search]").addClass("text-zinc-900 dark:text-zinc-100 border-orange-600 dark:border-orange-500");

// ---------------------------------------------------------------- health badge
function refreshHealth() {
  $.getJSON("/api/health").done((h) => {
    $("#footer-version").text(h.version);
    $("#config-path").text(h.config_file);
    const $badge = $("#health-badge");
    if (h.api_key_set) {
      $badge.attr("class", "rounded-full px-3 py-1 text-xs font-medium bg-emerald-100 text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-400")
        .text("API key: " + h.api_key_source);
    } else {
      $badge.attr("class", "rounded-full px-3 py-1 text-xs font-medium bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-400")
        .text("No API key. Open Settings.");
    }
    renderStatusList(h);
  });
}

function renderStatusList(h) {
  const rows = [
    ["Server version", esc(h.version)],
    ["API key configured", h.api_key_set ? "yes (" + esc(h.api_key_source) + ")" : "no"],
    ["Institutional token", h.insttoken_set ? "yes" : "no"],
    ["Config file", "<code class='code'>" + esc(h.config_file) + "</code>"],
    ["MCP stdio server", "<code class='code'>elsevier-mcp-server</code>, unchanged, for AI clients"],
  ];
  $("#status-list").html(
    rows.map(([k, v]) => "<dt class='text-zinc-500 dark:text-zinc-400'>" + k + "</dt><dd>" + v + "</dd>").join("")
  );
}

// ---------------------------------------------------------------- skeletons
const skeletonRows = (cols, rows = 5) =>
  Array.from({ length: rows }, () =>
    "<tr>" + Array.from({ length: cols }, () => "<td class='td'><div class='skeleton w-full'></div></td>").join("") + "</tr>"
  ).join("");

const showEmpty = (id, show, errorText) => {
  const $empty = $("#" + id).toggleClass("hidden", !show);
  if (errorText) $empty.find("p").first().text(errorText);
};

// ---------------------------------------------------------------- search
$("#search-form").on("submit", function (ev) {
  ev.preventDefault();
  const $btn = $(this).find("button[type=submit]").prop("disabled", true);
  $status("search-status", "Searching...");
  $("#search-empty").addClass("hidden");
  $("#search-table tbody").html(skeletonRows(6));

  $.ajax({
    url: "/api/search",
    method: "POST",
    contentType: "application/json",
    data: JSON.stringify({
      query: $("#search-query").val(),
      author: $("#search-author").val() || null,
      year: $("#search-year").val() || null,
      open_access: $("#search-oa").prop("checked"),
      count: parseInt($("#search-count").val(), 10),
    }),
  })
    .done((res) => {
      if (!res.success) {
        $status("search-status", res.error, true);
        $("#search-table tbody").empty();
        showEmpty("search-empty", true, res.error);
        return;
      }
      $status("search-status", "Done.");
      $("#search-summary").html(
        "<strong class='text-zinc-900 dark:text-zinc-100'>" + fmt(res.total_results) + "</strong> papers found, showing top " +
        res.papers.length + " by citations. Query: <code class='code'>" + esc(res.query) + "</code>"
      );
      renderPapers(res.papers);
    })
    .fail((xhr) => {
      const err = (xhr.responseJSON && xhr.responseJSON.error) || xhr.statusText;
      $status("search-status", err, true);
      $("#search-table tbody").empty();
      showEmpty("search-empty", true, err);
    })
    .always(() => $btn.prop("disabled", false));
});

function renderPapers(papers) {
  if (!papers.length) {
    $("#search-table tbody").empty();
    showEmpty("search-empty", true, "No results found.");
    return;
  }
  const rows = papers.map((p, i) => `
    <tr class="rowlink" data-eid="${esc(p.eid)}" data-doi="${esc(p.doi)}">
      <td class="td tabular-nums text-zinc-500">${i + 1}</td>
      <td class="td max-w-[320px] font-medium text-zinc-900 dark:text-zinc-100">${esc(p.title)}</td>
      <td class="td text-zinc-600 dark:text-zinc-400">${esc(p.authors)}</td>
      <td class="td text-zinc-600 dark:text-zinc-400">${esc(p.journal)}</td>
      <td class="td tabular-nums">${esc(String(p.year || "")).slice(0, 4)}</td>
      <td class="td tabular-nums text-right">${fmt(p.citations)}</td>
    </tr>`).join("");
  $("#search-table tbody").html(rows);
  $("#search-empty").addClass("hidden");
}

$("#search-table").on("click", "tr.rowlink", function () {
  const eid = $(this).data("eid");
  const doi = $(this).data("doi");
  if (!eid && !doi) return;
  openAbstractModal(eid, doi);
});

// ---------------------------------------------------------------- abstract modal
function openAbstractModal(eid, doi) {
  $("#modal-body").html("<div class='space-y-3'><div class='skeleton w-3/4 h-6'></div><div class='skeleton w-1/2 h-4'></div><div class='skeleton w-full'></div><div class='skeleton w-full'></div><div class='skeleton w-5/6'></div></div>");
  $("#modal-backdrop").removeClass("hidden");

  $.ajax({
    url: "/api/abstract",
    method: "POST",
    contentType: "application/json",
    data: JSON.stringify({ eid: eid || null, doi: doi || null }),
  })
    .done((res) => {
      if (!res.success) {
        $("#modal-body").html("<p class='status status-error'>" + esc(res.error) + "</p>");
        return;
      }
      const p = res.paper;
      const link = p.doi
        ? " <a class='link' href='https://doi.org/" + esc(p.doi) + "' target='_blank' rel='noopener'>doi.org/" + esc(p.doi) + "</a>"
        : "";
      $("#modal-body").html(`
        <h2 class="mr-8 text-lg font-semibold text-zinc-900 dark:text-zinc-100">${esc(p.title)}</h2>
        <p class="hint mt-1 mb-4">${esc(p.authors)}. ${esc(p.journal)}, ${esc(String(p.year || "")).slice(0, 4)}.
           ${fmt(p.citations)} citations.${link}</p>
        <p class="whitespace-pre-wrap text-sm leading-relaxed">${esc(p.abstract)}</p>`);
    })
    .fail((xhr) => {
      const err = (xhr.responseJSON && xhr.responseJSON.error) || xhr.statusText;
      $("#modal-body").html("<p class='status status-error'>" + esc(err) + "</p>");
    });
}

$("#modal-close").on("click", () => $("#modal-backdrop").addClass("hidden"));
$("#modal-backdrop").on("click", function (ev) {
  if (ev.target === this) $(this).addClass("hidden");
});
$(document).on("keydown", (ev) => {
  if (ev.key === "Escape") $("#modal-backdrop").addClass("hidden");
});

// ---------------------------------------------------------------- trends
let trendsChart = null;
let lastTrends = null;

$("#trends-form").on("submit", function (ev) {
  ev.preventDefault();
  const $btn = $(this).find("button[type=submit]").prop("disabled", true);
  $status("trends-status", "Analyzing...");
  $("#trends-empty").addClass("hidden");
  $("#trends-table tbody").html(skeletonRows(3));

  $.ajax({
    url: "/api/trends",
    method: "POST",
    contentType: "application/json",
    data: JSON.stringify({
      field: $("#trends-field").val(),
      start_year: parseInt($("#trends-start").val(), 10),
      end_year: parseInt($("#trends-end").val(), 10),
    }),
  })
    .done((res) => {
      if (!res.success) {
        $status("trends-status", res.error, true);
        $("#trends-table tbody").empty();
        showEmpty("trends-empty", true, res.error);
        return;
      }
      $status("trends-status", "Done.");
      $("#trends-summary").html(
        "<strong class='text-zinc-900 dark:text-zinc-100'>" + fmt(res.total_papers) + "</strong> papers on " +
        "<em>" + esc(res.field) + "</em> across " + Object.keys(res.yearly_papers).length + " years."
      );
      lastTrends = res;
      renderTrends(res.yearly_papers, res.growth_rates);
    })
    .fail((xhr) => {
      const err = (xhr.responseJSON && xhr.responseJSON.error) || xhr.statusText;
      $status("trends-status", err, true);
      $("#trends-table tbody").empty();
      showEmpty("trends-empty", true, err);
    })
    .always(() => $btn.prop("disabled", false));
});

function renderTrends(yearlyPapers, growthRates) {
  const years = Object.keys(yearlyPapers).sort();
  const counts = years.map((y) => yearlyPapers[y]);

  const accent = cssVar(prefersDark() ? "--color-orange-500" : "--color-orange-600") || "#ea580c";
  const grid = cssVar(prefersDark() ? "--color-zinc-800" : "--color-zinc-200") || "#e4e4e7";
  const text = cssVar("--color-zinc-500") || "#71717a";

  if (trendsChart) trendsChart.destroy();
  trendsChart = new Chart($("#trends-chart"), {
    type: "line",
    data: {
      labels: years,
      datasets: [{
        label: "Papers per year",
        data: counts,
        borderColor: accent,
        backgroundColor: accent + "22",
        fill: true,
        tension: 0.25,
        pointRadius: 4,
        pointBackgroundColor: accent,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: grid }, ticks: { color: text } },
        y: { beginAtZero: true, grid: { color: grid }, ticks: { color: text } },
      },
    },
  });

  const rows = years.map((y, i) => {
    const growthKey = i > 0 ? years[i - 1] + "-" + y : null;
    const growth = growthKey && growthKey in growthRates ? growthRates[growthKey] : null;
    const growthHtml = growth === null ? "<span class='text-zinc-400'>-</span>"
      : "<span class='" + (growth >= 0
          ? "text-emerald-700 dark:text-emerald-400"
          : "text-red-600 dark:text-red-400") + " tabular-nums font-medium'>" +
        (growth >= 0 ? "+" : "") + growth + "%</span>";
    return "<tr><td class='td tabular-nums'>" + esc(y) + "</td><td class='td tabular-nums text-right'>" +
      fmt(yearlyPapers[y]) + "</td><td class='td text-right'>" + growthHtml + "</td></tr>";
  });
  $("#trends-table tbody").html(rows);
  $("#trends-empty").toggleClass("hidden", years.length > 0);
}

// Re-render the chart with matching colors when the system theme flips.
window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
  if (lastTrends) renderTrends(lastTrends.yearly_papers, lastTrends.growth_rates);
});

// ---------------------------------------------------------------- journals
const compareQueries = new Set();

$("#journal-form").on("submit", function (ev) {
  ev.preventDefault();
  fetchJournal($("#journal-query").val().trim());
});

function fetchJournal(q) {
  if (!q) return;
  $status("journal-status", "Fetching metrics...");
  $("#journal-result").html(skeletonCard());
  const isIssn = q.replace(/-/g, "").length === 8 && !q.includes(" ");
  const url = "/api/journal-metrics?" + (isIssn ? "issn=" : "query=") + encodeURIComponent(q);

  $.getJSON(url)
    .done((res) => {
      if (!res.success) {
        $status("journal-status", res.error, true);
        $("#journal-result").empty();
        return;
      }
      $status("journal-status", "Done.");
      renderJournalCard(res.journal);
    })
    .fail((xhr) => {
      const err = (xhr.responseJSON && xhr.responseJSON.error) || xhr.statusText;
      $status("journal-status", err, true);
      $("#journal-result").empty();
    });
}

const skeletonCard = () => `
  <div class="card p-5 space-y-4">
    <div class="skeleton h-6 w-1/2"></div>
    <div class="skeleton h-4 w-1/3"></div>
    <div class="grid grid-cols-2 gap-3 sm:grid-cols-5">
      ${Array.from({ length: 5 }, () => "<div class='metric-tile'><div class='skeleton h-7 w-12'></div><div class='skeleton mt-2 h-3 w-16'></div></div>").join("")}
    </div>
  </div>`;

function journalCardHtml(j, full) {
  const cs = j.citescore || {};
  const sjr = j.sjr || {};
  const snip = j.snip || {};
  const q = String(j.best_quartile || "").toLowerCase();
  const meta = [
    esc(j.publisher),
    "ISSN " + (esc(j.issn) || "-"),
    j.eissn ? "eISSN " + esc(j.eissn) : null,
    j.open_access ? "Open Access" : null,
  ].filter(Boolean).join(". ");
  return `
    <div class="card p-5">
      <h3 class="text-[15px] font-semibold text-zinc-900 dark:text-zinc-100">${esc(j.title)}</h3>
      <p class="hint mt-0.5 mb-4">${meta}</p>
      <div class="grid grid-cols-2 gap-3 sm:grid-cols-5">
        <div class="metric-tile"><div class="metric-value">${cs.current ?? "-"}</div><div class="metric-label">CiteScore${cs.year ? " " + esc(cs.year) : ""}</div></div>
        <div class="metric-tile"><div class="metric-value">${cs.tracker ?? "-"}</div><div class="metric-label">Tracker${cs.tracker_year ? " " + esc(cs.tracker_year) : ""}</div></div>
        <div class="metric-tile"><div class="metric-value">${sjr.value ?? "-"}</div><div class="metric-label">SJR${sjr.year ? " " + esc(sjr.year) : ""}</div></div>
        <div class="metric-tile"><div class="metric-value">${snip.value ?? "-"}</div><div class="metric-label">SNIP${snip.year ? " " + esc(snip.year) : ""}</div></div>
        <div class="metric-tile"><div class="text-2xl font-bold"><span class="qtag ${q === "q1" ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-400" : "bg-orange-100 text-orange-800 dark:bg-orange-500/15 dark:text-orange-400"}">${esc(j.best_quartile) || "-"}</span></div><div class="metric-label">Best quartile</div></div>
      </div>
      ${full ? renderSubjectRankings(j.subject_rankings) : ""}
    </div>`;
}

function renderJournalCard(j) {
  $("#journal-result").html(journalCardHtml(j, true));
}

function renderSubjectRankings(rankings) {
  if (!rankings || !rankings.length) return "";
  const rows = rankings.map((r) => {
    const q = String(r.quartile).toLowerCase();
    return `
      <tr>
        <td class="td"><code class="code">${esc(r.subject_code)}</code></td>
        <td class="td tabular-nums">#${esc(r.rank)}</td>
        <td class="td tabular-nums">${r.percentile}</td>
        <td class="td"><span class="qtag ${q === "q1" ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-400" : "bg-orange-100 text-orange-800 dark:bg-orange-500/15 dark:text-orange-400"}">${esc(r.quartile)}</span></td>
      </tr>`;
  }).join("");
  return `
    <div class="mt-4 overflow-x-auto">
      <table class="w-full">
        <thead><tr><th class="th">Subject</th><th class="th">Rank</th><th class="th">Percentile</th><th class="th">Quartile</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
}

// ----- comparison -----
$("#journal-add-compare").on("click", () => {
  const q = $("#journal-query").val().trim();
  if (!q || compareQueries.has(q) || compareQueries.size >= 4) return;
  compareQueries.add(q);
  renderCompareChips();
});

function renderCompareChips() {
  const chips = [...compareQueries].map((q) =>
    `<span class="chip">${esc(q)}<button type="button" data-q="${esc(q)}" aria-label="Remove" class="text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200">&times;</button></span>`).join("");
  $("#compare-list").html(chips);
}

$("#compare-list").on("click", "button", function () {
  compareQueries.delete($(this).data("q"));
  renderCompareChips();
});

$("#journal-run-compare").on("click", function () {
  const $btn = $(this).prop("disabled", true);
  if (!compareQueries.size) { $btn.prop("disabled", false); return; }
  $status("journal-status", "Comparing...");
  $("#compare-result").html(skeletonCard() + skeletonCard());

  $.ajax({
    url: "/api/journal-compare",
    method: "POST",
    contentType: "application/json",
    data: JSON.stringify({ queries: [...compareQueries] }),
  })
    .done((res) => {
      const ok = (res.journals || []).filter((j) => j.success);
      if (!ok.length) {
        $status("journal-status", res.journals[0].error, true);
        $("#compare-result").empty();
        return;
      }
      $status("journal-status", "Done.");
      $("#compare-result").html(ok.map((j) => journalCardHtml(j.journal, false)).join(""));
    })
    .fail((xhr) => {
      const err = (xhr.responseJSON && xhr.responseJSON.error) || xhr.statusText;
      $status("journal-status", err, true);
      $("#compare-result").empty();
    })
    .always(() => $btn.prop("disabled", false));
});

// ---------------------------------------------------------------- settings
$("#settings-form").on("submit", function (ev) {
  ev.preventDefault();
  const payload = {};
  if ($("#cfg-api-key").val()) payload.api_key = $("#cfg-api-key").val();
  if ($("#cfg-insttoken").val()) payload.insttoken = $("#cfg-insttoken").val();
  if (!Object.keys(payload).length) {
    $status("settings-status", "Nothing to save. Enter a key first.", true);
    return;
  }
  $status("settings-status", "Saving...");
  $.ajax({
    url: "/api/config",
    method: "POST",
    contentType: "application/json",
    data: JSON.stringify(payload),
  })
    .done((res) => {
      if (!res.success) { $status("settings-status", res.error, true); return; }
      $status("settings-status", "Saved.");
      $("#cfg-api-key, #cfg-insttoken").val("");
      refreshHealth();
    })
    .fail((xhr) => {
      const err = (xhr.responseJSON && xhr.responseJSON.error) || xhr.statusText;
      $status("settings-status", err, true);
    });
});

$("#cfg-clear").on("click", () => {
  $.ajax({
    url: "/api/config",
    method: "POST",
    contentType: "application/json",
    data: JSON.stringify({ api_key: "", insttoken: "" }),
  })
    .done(() => {
      $status("settings-status", "Saved credentials cleared.");
      refreshHealth();
    })
    .fail((xhr) => {
      const err = (xhr.responseJSON && xhr.responseJSON.error) || xhr.statusText;
      $status("settings-status", err, true);
    });
});

function loadTools() {
  $.getJSON("/api/tools").done((res) => {
    const rows = (res.tools || []).map((t) =>
      `<tr><td class="td whitespace-nowrap"><code class="code">${esc(t.name)}</code></td><td class="td text-zinc-600 dark:text-zinc-400">${esc(t.description)}</td></tr>`).join("");
    $("#tools-table tbody").html(rows);
  });
}

// ---------------------------------------------------------------- init
refreshHealth();
loadTools();
