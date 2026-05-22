"""Static HTML visualization for rater analysis output."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_visualization_html(path: Path, payload: dict[str, Any]) -> None:
  """Write the dependency-free analysis visualization page."""
  data = _script_json(payload)
  path.write_text(_HTML.replace("__ANALYSIS_JSON__", data), encoding="utf-8")


def _script_json(payload: dict[str, Any]) -> str:
  return (
    json.dumps(payload, sort_keys=True)
    .replace("<", "\\u003c")
    .replace(">", "\\u003e")
    .replace("&", "\\u0026")
  )


_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Rater Analysis</title>
  <style>
    :root {
      color-scheme: light;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, sans-serif;
      background: #f6f8fb;
      color: #1f2937;
    }
    body {
      margin: 0;
      padding: 24px;
    }
    main {
      max-width: 1200px;
      margin: 0 auto;
    }
    h1, h2 {
      margin: 0;
      letter-spacing: 0;
    }
    header, section {
      margin-bottom: 20px;
    }
    .selector {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 8px 16px;
      margin-top: 12px;
    }
    label {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 0;
    }
    .charts {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 20px;
    }
    .panel {
      background: #ffffff;
      border: 1px solid #dbe3ef;
      border-radius: 8px;
      padding: 16px;
    }
    svg {
      width: 100%;
      min-height: 280px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      background: #ffffff;
    }
    th, td {
      border-bottom: 1px solid #e5eaf2;
      padding: 8px;
      text-align: left;
      vertical-align: top;
    }
    th {
      font-weight: 700;
      background: #eef3f9;
    }
    .srs-column {
      background: #fff4d6;
    }
    .rating-high {
      font-weight: 700;
    }
    .rating-low {
      text-decoration: underline;
      text-underline-offset: 3px;
    }
    .empty {
      color: #667085;
      padding: 24px 0;
    }
  </style>
</head>
<body>
  <main>
    <header>
      <h1>Rater Analysis</h1>
      <div id="model-selector" class="selector"></div>
    </header>
    <section class="charts">
      <div class="panel">
        <h2>Overall ratings</h2>
        <svg id="bar-chart" role="img" aria-label="Overall ratings bar chart"></svg>
      </div>
      <div class="panel">
        <h2>Individual scores</h2>
        <svg
          id="radar-chart"
          role="img"
          aria-label="Individual scores radar chart"
        ></svg>
      </div>
    </section>
    <section class="panel">
      <h2>Comparison table</h2>
      <div id="comparison-table"></div>
    </section>
  </main>
  <script>
    window.__RATER_ANALYSIS__ = __ANALYSIS_JSON__;
    const state = { data: window.__RATER_ANALYSIS__, selected: new Set() };
    const colors = ["#2563eb", "#dc2626", "#059669", "#7c3aed", "#ea580c"];

    state.data.models.forEach((model) => state.selected.add(model.llm_id));
    render();

    function render() {
      renderSelector();
      const models = selectedModels();
      renderBarChart(models);
      renderRadarChart(models);
      renderTable(models);
    }

    function selectedModels() {
      return state.data.models.filter((model) => state.selected.has(model.llm_id));
    }

    function renderSelector() {
      const root = document.getElementById("model-selector");
      root.innerHTML = "";
      state.data.models.forEach((model) => {
        const label = document.createElement("label");
        const input = document.createElement("input");
        input.type = "checkbox";
        input.checked = state.selected.has(model.llm_id);
        input.addEventListener("change", () => {
          if (input.checked) {
            state.selected.add(model.llm_id);
          } else {
            state.selected.delete(model.llm_id);
          }
          render();
        });
        label.append(input, model.display_name);
        root.append(label);
      });
    }

    function renderBarChart(models) {
      const svg = document.getElementById("bar-chart");
      svg.innerHTML = "";
      if (models.length === 0) {
        svg.innerHTML = `
          <text x="10" y="32" class="empty">
            Select at least one model.
          </text>
        `;
        return;
      }
      const metrics = ["srs"];
      const width = 540;
      const rowHeight = 28;
      const height = 40 + models.length * metrics.length * rowHeight;
      svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
      let y = 28;
      models.forEach((model, modelIndex) => {
        metrics.forEach((metric) => {
          const value = model[metric];
          const barWidth = Math.max(1, value * 3.2);
          const label = escapeHtml(`${model.display_name} ${metric.toUpperCase()}`);
          svg.insertAdjacentHTML("beforeend", `
            <text x="0" y="${y + 12}" font-size="11">${label}</text>
            <rect
              x="190"
              y="${y}"
              width="${barWidth}"
              height="16"
              fill="${colors[modelIndex % colors.length]}"
            ></rect>
            <text x="${195 + barWidth}" y="${y + 12}" font-size="11">
              ${value.toFixed(2)}
            </text>
          `);
          y += rowHeight;
        });
      });
    }

    function renderRadarChart(models) {
      const svg = document.getElementById("radar-chart");
      svg.innerHTML = "";
      if (models.length === 0) {
        svg.innerHTML = `
          <text x="10" y="32" class="empty">
            Select at least one model.
          </text>
        `;
        return;
      }
      const axes = Array.from(new Set(models.flatMap((model) =>
        Object.keys(model.questionnaires).flatMap((name) => [
          `${name} BAS`,
          `${name} VAS`,
        ])
      )));
      const center = 160;
      const radius = 110;
      svg.setAttribute("viewBox", "0 0 340 320");
      axes.forEach((axis, index) => {
        const angle = (Math.PI * 2 * index / axes.length) - Math.PI / 2;
        const x = center + Math.cos(angle) * radius;
        const y = center + Math.sin(angle) * radius;
        svg.insertAdjacentHTML("beforeend", `
          <line
            x1="${center}"
            y1="${center}"
            x2="${x}"
            y2="${y}"
            stroke="#d0d7e2"
          ></line>
          <text x="${x}" y="${y}" font-size="10">${escapeHtml(axis)}</text>
        `);
      });
      models.forEach((model, modelIndex) => {
        const points = axes.map((axis, index) => {
          const metric = axis.endsWith(" BAS") ? "bas" : "vas";
          const name = axis.slice(0, -4);
          const value = model.questionnaires[name]?.[metric] ?? 0;
          const angle = (Math.PI * 2 * index / axes.length) - Math.PI / 2;
          const scaled = radius * value / 100;
          const x = center + Math.cos(angle) * scaled;
          const y = center + Math.sin(angle) * scaled;
          return `${x},${y}`;
        }).join(" ");
        svg.insertAdjacentHTML("beforeend", `
          <polygon
            points="${points}"
            fill="${colors[modelIndex % colors.length]}33"
            stroke="${colors[modelIndex % colors.length]}"
            stroke-width="2"
          ></polygon>
        `);
      });
    }

    function renderTable(models) {
      const root = document.getElementById("comparison-table");
      if (models.length === 0) {
        root.innerHTML = `<p class="empty">Select at least one model.</p>`;
        return;
      }
      const tableExtrema = {
        srs: columnExtrema(models, "srs"),
        bas: columnExtrema(models, "bas"),
        vas: columnExtrema(models, "vas"),
      };
      const rows = models.map((model) => `
        <tr>
          <td>${escapeHtml(model.display_name)}</td>
          <td class="srs-column">
            ${formatRatingCell(model.srs, tableExtrema.srs, true)}
          </td>
          <td>${formatRatingCell(model.bas, tableExtrema.bas, false)}</td>
          <td>${formatRatingCell(model.vas, tableExtrema.vas, false)}</td>
          <td>${Object.entries(model.questionnaires).map(([name, rating]) => {
            return [
              `${escapeHtml(name)}: SRS ${rating.srs.toFixed(2)}`,
              `BAS ${rating.bas.toFixed(2)}`,
              `VAS ${rating.vas.toFixed(2)}`,
            ].join(", ");
          }).join("<br>")}</td>
        </tr>
      `).join("");
      root.innerHTML = `
        <table>
          <thead>
            <tr>
              <th>Display name</th>
              <th class="srs-column">SRS</th>
              <th>BAS</th>
              <th>VAS</th>
              <th>Questionnaires</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      `;
    }

    function columnExtrema(models, key) {
      const values = models.map((model) => model[key]);
      return {
        high: Math.max(...values),
        low: Math.min(...values),
      };
    }

    function formatRatingCell(value, extrema, isSrs) {
      const classes = [];
      if (value === extrema.high) {
        classes.push("rating-high");
      }
      if (value === extrema.low) {
        classes.push("rating-low");
      }
      if (isSrs) {
        classes.push("srs-value");
      }
      return `<span class="${classes.join(" ")}">${value.toFixed(2)}</span>`;
    }

    function escapeHtml(value) {
      return value.replace(/[&<>"']/g, (character) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      }[character]));
    }
  </script>
</body>
</html>
"""
