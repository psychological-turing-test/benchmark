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
    h3 {
      margin: 0 0 12px;
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
    .selector-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 12px;
    }
    button {
      border: 1px solid #b8c4d6;
      border-radius: 6px;
      background: #ffffff;
      color: #1f2937;
      cursor: pointer;
      font: inherit;
      padding: 6px 10px;
    }
    label {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 0;
    }
    .charts {
      display: grid;
      grid-template-columns: minmax(0, 1fr);
      gap: 20px;
    }
    .panel {
      background: #ffffff;
      border: 1px solid #dbe3ef;
      border-radius: 8px;
      padding: 16px;
    }
    .metric-chart-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
      gap: 20px;
      margin-top: 16px;
    }
    .questionnaire-panel {
      border: 1px solid #e5eaf2;
      border-radius: 8px;
      padding: 16px;
      background: #f8fafc;
    }
    .questionnaire-risky-choice-framing {
      background: #eefaf6;
      border-color: #b7ead8;
    }
    .questionnaire-decision-premise {
      background: #fff7ed;
      border-color: #fed7aa;
    }
    .metric-bars-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 12px;
    }
    .metric-chart-card {
      border: 1px solid #e5eaf2;
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.9);
      padding: 12px;
      min-width: 0;
    }
    .metric-chart-card:focus {
      border-color: #2563eb;
      box-shadow: 0 0 0 2px #bfdbfe;
      outline: none;
    }
    .metric-chart-title {
      display: flex;
      gap: 8px;
      align-items: baseline;
      font-weight: 700;
      margin-bottom: 6px;
    }
    .metric-acronym {
      color: #1d4ed8;
      font-variant-caps: all-small-caps;
      letter-spacing: 0;
      white-space: nowrap;
    }
    .metric-note {
      color: #475467;
      font-size: 12px;
      line-height: 1.4;
      margin: 0 0 10px;
    }
    .metric-bar-row {
      display: grid;
      grid-template-columns: minmax(110px, 0.9fr) minmax(120px, 1.4fr) 86px;
      gap: 8px;
      align-items: center;
      margin-top: 8px;
      font-size: 12px;
    }
    .metric-zero-marker-row {
      display: grid;
      grid-template-columns: minmax(110px, 0.9fr) minmax(120px, 1.4fr) 86px;
      gap: 8px;
      align-items: end;
      margin-top: 4px;
      font-size: 11px;
      color: #475467;
    }
    .metric-zero-marker-track {
      position: relative;
      height: 14px;
    }
    .metric-zero-marker {
      position: absolute;
      transform: translateX(-50%);
      font-weight: 700;
      line-height: 1;
    }
    .metric-bar-label {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .metric-bar-track {
      position: relative;
      height: 18px;
      border-radius: 4px;
      background: #eef3f9;
      overflow: hidden;
    }
    .metric-bar-zero {
      position: absolute;
      left: 50%;
      top: 0;
      bottom: 0;
      border-left: 1px solid #98a2b3;
    }
    .metric-bar-absolute-zero {
      position: absolute;
      top: 0;
      bottom: 0;
      border-left: 2px dashed #475467;
    }
    .metric-bar-fill {
      position: absolute;
      top: 2px;
      bottom: 2px;
      border-radius: 4px;
    }
    .metric-bar-value {
      color: #344054;
      text-align: right;
      white-space: nowrap;
    }
    .table-group {
      margin-top: 16px;
      overflow-x: auto;
    }
    .table-group h3 {
      margin-bottom: 8px;
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
    .pas-column {
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
    @media (max-width: 820px) {
      .charts,
      .metric-bars-grid {
        grid-template-columns: 1fr;
      }
      .metric-bar-row {
        grid-template-columns: 1fr;
      }
      .metric-bar-value {
        text-align: left;
      }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <h1>Rater Analysis</h1>
      <div id="selector-actions" class="selector-actions"></div>
      <div id="model-selector" class="selector"></div>
    </header>
    <section class="charts">
      <div class="panel">
        <h2>Overall ratings</h2>
        <svg id="bar-chart" role="img" aria-label="Overall ratings bar chart"></svg>
      </div>
    </section>
    <section class="panel">
      <h2>Behavioral metric bars</h2>
      <div id="metric-charts" class="metric-chart-grid"></div>
    </section>
    <section class="panel">
      <h2>Questionnaire metric tables</h2>
      <div id="comparison-tables"></div>
    </section>
  </main>
  <script>
    window.__RATER_ANALYSIS__ = __ANALYSIS_JSON__;
    const state = { data: window.__RATER_ANALYSIS__, selected: new Set() };
    const HUMAN_BASELINE_LABEL = "Human baseline";
    const colors = ["#2563eb", "#dc2626", "#059669", "#7c3aed", "#ea580c"];
    const humanColor = "#111827";
    const QUESTIONNAIRE_METRICS = {
      "risky-choice-framing": {
        displayName: "RiskyChoiceFraming",
        metrics: [
          {
            key: "fes",
            acronym: "FES",
            name: "Framing Effect Susceptibility",
            note: "Mean increase in risky-choice rate under negative framing versus positive framing. Around 0 means frame-neutral; positive values indicate the classic reflection direction; negative values indicate a reverse framing effect.",
            scale: "signed",
            max: 1,
          },
          {
            key: "rc",
            acronym: "RC",
            name: "Reflection Consistency",
            note: "Fraction of scenarios matching risk-averse gains and risk-seeking losses. It measures how often the canonical pattern appears, while FES measures the size of the framing effect.",
            scale: "positive",
            max: 1,
          },
          {
            key: "ms_life",
            acronym: "MS-L",
            name: "Magnitude Sensitivity (life)",
            note: "Slope of risky-choice rate over life magnitude. Negative values mean larger stakes make the agent more conservative; values near 0 are scope-insensitive; positive values mean larger stakes make the agent more risk-seeking.",
            scale: "signed",
            max: 0.2,
          },
          {
            key: "kg",
            acronym: "KG",
            name: "Kinship Gradient",
            note: "Change in risky-choice rate as affected family-member count increases. Positive values mean denser kin share pushes toward the all-or-nothing risky plan; near 0 means kin composition is decision-irrelevant; negative values mean more kin makes choices more conservative.",
            scale: "signed",
            max: 1,
          },
          {
            key: "igb",
            acronym: "IGB",
            name: "In-group Bias",
            note: "Human-minus-alien risky-choice gap, averaged across frames. Large absolute values mean choices depend on subject identity; values near 0 are identity-neutral. Negative human-reference values indicate more conservative choices toward humans than aliens.",
            scale: "signed",
            max: 1,
          },
          {
            key: "cdc",
            acronym: "CDC",
            name: "Cross-Domain Coherence",
            note: "Similarity of mean risky-choice rates across lives, kin, painting, and dollar domains. Values near 1 mean behavior is consistent across domains; values near 0 mean behavior varies sharply by value carrier. High or low is descriptive rather than inherently correct.",
            scale: "positive",
            max: 1,
          },
          {
            key: "rd",
            acronym: "RD",
            name: "Response Determinism",
            note: "How close item-level choices are to deterministic rather than maximally stochastic. Values near 1 mean near-deterministic per-item choices; values near 0 mean maximally stochastic responses. High RD can make FES, MS, and KG estimates more brittle.",
            scale: "positive",
            max: 1,
          },
        ],
      },
      "decision-premise": {
        displayName: "DecisionPremise",
        metrics: [
          {
            key: "frp",
            acronym: "FRP",
            name: "Fairness Randomization Preference",
            note: "Preference for random selection over deterministic allocation in fairness items. Around 0 means a strong deterministic-allocation preference; around 1 means a strong random-selection preference. The human reference is about 0.30.",
            scale: "positive",
            max: 1,
          },
          {
            key: "sam",
            acronym: "SAM",
            name: "Self-Age Modulation",
            note: "How participant-age premise changes the old-versus-young Plan-B gap. Positive values mean the age-premise gap is stronger under the middle-aged-participant prompt; near 0 means participant age does not modulate the gap; negative values mean the gap is stronger under the young-participant prompt. The human reference is about 0.43.",
            scale: "signed",
            max: 1,
          },
          {
            key: "kp",
            acronym: "KP",
            name: "Kinship Premium",
            note: "Plan-B increase for family-member scenarios versus anonymous same-size groups. Positive values mean kinship increases Plan-B choice; near 0 means kinship is decision-irrelevant; negative values mean kinship makes the agent more conservative. The human reference is about 0.21.",
            scale: "signed",
            max: 1,
          },
          {
            key: "sc",
            acronym: "SC",
            name: "Scale Conservatism",
            note: "Small-group versus large-group Plan-B shift under the same premise. Positive values mean more Plan-B choices for the smaller anonymous group; near 0 means group size does not affect Plan-B choice; negative values mean more Plan-B choices for the larger group. The human reference is about 0.17.",
            scale: "signed",
            max: 1,
          },
          {
            key: "gpr",
            acronym: "GPR",
            name: "Gamble Payoff Responsiveness",
            note: "Plan-B increase when the gamble payoff improves. Positive values mean the agent chooses Plan B more often when its payoff improves; near 0 means insensitivity to the improved gamble; negative values mean movement against the expected-value improvement. The human reference is about 0.16.",
            scale: "signed",
            max: 1,
          },
          {
            key: "sbs",
            acronym: "SBS",
            name: "Sure-Benefit Sensitivity",
            note: "Plan-B reduction when the sure option improves. Positive values mean the stronger sure option suppresses Plan-B choice; near 0 means the improved sure outcome is ignored; negative values mean more Plan-B choice despite the stronger sure option. The human reference is about 0.28.",
            scale: "signed",
            max: 1,
          },
        ],
      },
    };

    state.data.models.forEach((model) => state.selected.add(model.llm_id));
    render();

    function render() {
      renderSelectorActions();
      renderSelector();
      const models = selectedModels();
      renderBarChart(models);
      renderBehavioralProfiles(models);
      renderMetricTables(models);
    }

    function selectedModels() {
      return modelsByDisplayName().filter((model) => state.selected.has(model.llm_id));
    }

    function modelsByDisplayName() {
      return [...state.data.models].sort((left, right) =>
        left.display_name.localeCompare(right.display_name)
      );
    }

    function renderSelectorActions() {
      const root = document.getElementById("selector-actions");
      root.innerHTML = "";
      root.append(
        selectorButton("Select all", () => {
          state.data.models.forEach((model) => state.selected.add(model.llm_id));
          render();
        }),
        selectorButton("Deselect all", () => {
          state.selected.clear();
          render();
        })
      );
    }

    function selectorButton(text, onClick) {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = text;
      button.addEventListener("click", onClick);
      return button;
    }

    function renderSelector() {
      const root = document.getElementById("model-selector");
      root.innerHTML = "";
      modelsByDisplayName().forEach((model) => {
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
      const metrics = ["pas"];
      const width = 760;
      const barStart = 360;
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
              x="${barStart}"
              y="${y}"
              width="${barWidth}"
              height="16"
              fill="${colors[modelIndex % colors.length]}"
            ></rect>
            <text x="${barStart + 5 + barWidth}" y="${y + 12}" font-size="11">
              ${value.toFixed(2)}
            </text>
          `);
          y += rowHeight;
        });
      });
    }

    function renderBehavioralProfiles(models) {
      const root = document.getElementById("metric-charts");
      root.innerHTML = "";
      const ids = questionnaireIds();
      if (ids.length === 0) {
        root.innerHTML = `<p class="empty">No questionnaire metrics available.</p>`;
        return;
      }
      ids.forEach((questionnaireId) => {
        root.append(renderQuestionnaireMetricPanel(questionnaireId, models));
      });
    }

    function renderQuestionnaireMetricPanel(questionnaireId, models) {
      const metadata = QUESTIONNAIRE_METRICS[questionnaireId];
      const panel = document.createElement("article");
      panel.className = [
        "questionnaire-panel",
        `questionnaire-${cssSafeId(questionnaireId)}`,
      ].join(" ");

      const title = document.createElement("h3");
      title.textContent = questionnaireDisplayName(questionnaireId);
      panel.append(title);

      if (!metadata) {
        const empty = document.createElement("p");
        empty.className = "empty";
        empty.textContent = "No metric metadata is configured for this questionnaire.";
        panel.append(empty);
        return panel;
      }

      const humanProfile = humanBehavioralProfile(questionnaireId);
      const modelSeries = models
        .map((model, index) => ({
          label: model.display_name,
          color: colors[index % colors.length],
          profile: modelBehavioralProfile(questionnaireId, model),
        }))
        .filter((series) => series.profile !== null);
      const series = [
        ...(humanProfile === null ? [] : [{
          label: HUMAN_BASELINE_LABEL,
          color: humanColor,
          profile: humanProfile,
        }]),
        ...modelSeries,
      ];

      if (series.length === 0) {
        const empty = document.createElement("p");
        empty.className = "empty";
        empty.textContent = "Behavioral profile metrics are not available.";
        panel.append(empty);
        return panel;
      }

      const charts = document.createElement("div");
      charts.className = "metric-bars-grid";
      metadata.metrics.forEach((metric) => {
        charts.append(renderMetricBarChart(metric, series));
      });
      panel.append(charts);
      return panel;
    }

    function renderMetricBarChart(metric, series) {
      const card = document.createElement("section");
      card.className = "metric-chart-card";
      card.tabIndex = 0;
      card.title = metric.note;
      card.setAttribute("aria-label", metricNoteText(metric));
      card.innerHTML = `
        <div class="metric-chart-title">
          <span class="metric-acronym">${escapeHtml(metric.acronym)}</span>
          <span>${escapeHtml(metric.name)}</span>
        </div>
        <p class="metric-note">
          <strong>Interpretation:</strong> ${escapeHtml(metric.note)}
        </p>
      `;
      const scale = baselineMetricScale(metric, series);
      card.append(renderAbsoluteZeroMarker(scale));
      series.forEach((item) => {
        card.append(renderMetricBarRow(metric, item, scale));
      });
      return card;
    }

    function renderAbsoluteZeroMarker(scale) {
      const absoluteZero = absoluteZeroPosition(scale);
      const row = document.createElement("div");
      row.className = "metric-zero-marker-row";
      row.innerHTML = `
        <span></span>
        <div class="metric-zero-marker-track">
          <span
            class="metric-zero-marker"
            style="left: ${absoluteZero}%;"
          >0</span>
        </div>
        <span></span>
      `;
      return row;
    }

    function renderMetricBarRow(metric, item, scale) {
      const value = item.profile[metric.key];
      const signedDifference = signedBaselineDifference(value, scale);
      const ratio = baselineMetricRatio(value, scale);
      const fill = barFillStyle(ratio);
      const absoluteZero = absoluteZeroPosition(scale);
      const row = document.createElement("div");
      row.className = "metric-bar-row";
      row.title = [
        `${item.label} ${metric.acronym}: ${formatMetricValue(value)}`,
        `signed difference from human baseline: ${formatMetricValue(signedDifference)}`,
      ].join("; ");
      row.innerHTML = `
        <div class="metric-bar-label">${escapeHtml(item.label)}</div>
        <div class="metric-bar-track">
          <span class="metric-bar-zero" title="Human baseline difference: 0"></span>
          <span
            class="metric-bar-absolute-zero"
            title="Absolute metric value: 0"
            style="left: ${absoluteZero}%;"
          ></span>
          <span
            class="metric-bar-fill"
            style="left: ${fill.left}%; width: ${fill.width}%; background: ${item.color};"
          ></span>
        </div>
        <div class="metric-bar-value">
          ${formatMetricValue(value)} (${formatMetricValue(signedDifference)})
        </div>
      `;
      return row;
    }

    function barFillStyle(ratio) {
      const center = 50;
      const bounded = clamp(ratio, -1, 1);
      const end = center + bounded * center;
      return {
        left: Math.min(center, end),
        width: Math.abs(end - center),
      };
    }

    function absoluteZeroPosition(scale) {
      return 50 + baselineMetricRatio(0, scale) * 50;
    }

    function renderMetricTables(models) {
      const root = document.getElementById("comparison-tables");
      root.innerHTML = "";
      const ids = questionnaireIds();
      if (ids.length === 0) {
        root.innerHTML = `<p class="empty">No questionnaire metrics available.</p>`;
        return;
      }
      ids.forEach((questionnaireId) => {
        root.append(renderQuestionnaireMetricTable(questionnaireId, models));
      });
    }

    function renderQuestionnaireMetricTable(questionnaireId, models) {
      const metadata = QUESTIONNAIRE_METRICS[questionnaireId];
      const group = document.createElement("div");
      group.className = "table-group";
      const title = document.createElement("h3");
      title.textContent = questionnaireDisplayName(questionnaireId);
      group.append(title);

      if (!metadata) {
        const empty = document.createElement("p");
        empty.className = "empty";
        empty.textContent = "No metric metadata is configured for this questionnaire.";
        group.append(empty);
        return group;
      }

      const humanProfile = humanBehavioralProfile(questionnaireId);
      const rows = [];
      rows.push(metricTableRow(HUMAN_BASELINE_LABEL, null, humanProfile, metadata));
      models.forEach((model) => {
        const questionnaire = model.questionnaires[questionnaireId];
        if (!questionnaire) {
          return;
        }
        rows.push(metricTableRow(
          model.display_name,
          questionnaire,
          modelBehavioralProfile(questionnaireId, model),
          metadata,
        ));
      });

      group.insertAdjacentHTML("beforeend", `
        <table>
          <thead>
            <tr>
              <th>Display name</th>
              <th class="pas-column">PAS</th>
              <th>BAS</th>
              <th>FAS</th>
              ${metadata.metrics.map((metric) => `
                <th title="${escapeHtml(metric.note)}">
                  ${escapeHtml(metric.acronym)}
                </th>
              `).join("")}
            </tr>
          </thead>
          <tbody>${rows.join("")}</tbody>
        </table>
      `);
      return group;
    }

    function metricTableRow(label, questionnaire, profile, metadata) {
      const metricCells = metadata.metrics.map((metric) => `
        <td title="${escapeHtml(metric.name)}">
          ${formatMetricValue(profile?.[metric.key])}
        </td>
      `).join("");
      return `
        <tr>
          <td>${escapeHtml(label)}</td>
          <td class="pas-column">${formatRatingValue(questionnaire?.pas)}</td>
          <td>${formatRatingValue(questionnaire?.bas)}</td>
          <td>${formatRatingValue(questionnaire?.fas)}</td>
          ${metricCells}
        </tr>
      `;
    }

    function questionnaireIds() {
      const ids = new Set();
      state.data.models.forEach((model) => {
        Object.keys(model.questionnaires).forEach((questionnaireId) => {
          ids.add(questionnaireId);
        });
      });
      const configured = Object.keys(QUESTIONNAIRE_METRICS).filter((id) =>
        ids.has(id)
      );
      const unknown = [...ids].filter((id) => !(id in QUESTIONNAIRE_METRICS));
      return [...configured, ...unknown.sort()];
    }

    function questionnaireDisplayName(questionnaireId) {
      return QUESTIONNAIRE_METRICS[questionnaireId]?.displayName ?? questionnaireId;
    }

    function humanBehavioralProfile(questionnaireId) {
      for (const model of state.data.models) {
        const profile = behavioralProfile(
          questionnaireId,
          model.questionnaires[questionnaireId],
          "human",
        );
        if (profile !== null) {
          return profile;
        }
      }
      return null;
    }

    function modelBehavioralProfile(questionnaireId, model) {
      return behavioralProfile(
        questionnaireId,
        model.questionnaires[questionnaireId],
        "llm",
      );
    }

    function behavioralProfile(questionnaireId, questionnaire, agent) {
      const metrics = questionnaire?.details?.behavioral_tendency_metrics;
      if (!metrics) {
        return null;
      }
      if (questionnaireId === "risky-choice-framing") {
        return metrics[agent]?.profile ?? null;
      }
      if (questionnaireId === "decision-premise") {
        return metrics.profile?.[agent] ?? null;
      }
      return metrics.profile?.[agent] ?? metrics[agent]?.profile ?? null;
    }

    function baselineMetricScale(metric, series) {
      const humanSeries = series.find((item) => item.label === HUMAN_BASELINE_LABEL);
      const humanValue = humanSeries?.profile[metric.key];
      const relativeDenominator = Math.abs(numberOrZero(humanValue));
      const denominator = relativeDenominator >= 0.05
        ? relativeDenominator
        : metric.max ?? 1;
      const normalizedValues = series.map((item) =>
        normalizedMetricValue(item.profile[metric.key], {
          denominator,
          humanValue: numberOrZero(humanValue),
        })
      );
      const max = Math.max(
        1,
        ...normalizedValues.map((value) => Math.abs(numberOrZero(value))),
      );
      return {
        denominator,
        humanValue: numberOrZero(humanValue),
        max,
      };
    }

    function normalizedMetricValue(value, scale) {
      if (!Number.isFinite(value) || scale.denominator === 0) {
        return 0;
      }
      return (value - scale.humanValue) / scale.denominator;
    }

    function signedBaselineDifference(value, scale) {
      if (!Number.isFinite(value)) {
        return NaN;
      }
      return value - scale.humanValue;
    }

    function baselineMetricRatio(value, scale) {
      if (!Number.isFinite(value)) {
        return 0;
      }
      const normalized = normalizedMetricValue(value, scale);
      return clamp(normalized / scale.max, -1, 1);
    }

    function metricNoteText(metric) {
      return `${metric.acronym} - ${metric.name}: ${metric.note}`;
    }

    function cssSafeId(value) {
      return String(value).replace(/[^a-z0-9-]/gi, "-").toLowerCase();
    }

    function formatRatingValue(value) {
      if (!Number.isFinite(value)) {
        return "&mdash;";
      }
      return value.toFixed(2);
    }

    function formatMetricValue(value) {
      if (!Number.isFinite(value)) {
        return "&mdash;";
      }
      return value.toFixed(3);
    }

    function formatNormalizedValue(value) {
      if (!Number.isFinite(value)) {
        return "&mdash;";
      }
      return value.toFixed(2);
    }

    function numberOrZero(value) {
      return Number.isFinite(value) ? value : 0;
    }

    function clamp(value, min, max) {
      return Math.max(min, Math.min(max, value));
    }

    function escapeHtml(value) {
      return String(value).replace(/[&<>"']/g, (character) => ({
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
