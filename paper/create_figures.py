"""Create the paper's four grayscale figures from the verified offline audit.

Use bundled Python with PYTHONPATH=/private/tmp/llm-rationale-paper-packages.
Outputs are editable SVG, vector PDF, 600-dpi PNG, CSV, and a figure manifest.
"""

from __future__ import annotations

import csv
import json
import math
import os
import random
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/llm-rationale-plot-cache")

import matplotlib

matplotlib.use("Agg")

from fontTools.ttLib import TTCollection
from matplotlib import font_manager
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, Rectangle

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "paper" / "figures"
AUDIT = ROOT / "paper" / "data_audit.json"
FONT_ROOT = Path("/System/Library/Fonts/Supplemental")
WIDTH = 6.4
DPI = 600
BLACK = "0.10"
GRAY = "0.62"
LIGHT = "0.87"


def prepare_style() -> None:
  """Register Songti regular and Times New Roman with publication settings."""
  extracted = Path("/private/tmp/llm-rationale-songti-regular.ttf")
  collection = TTCollection(FONT_ROOT / "Songti.ttc")
  collection.fonts[6].save(extracted)
  collection.close()
  font_manager.fontManager.addfont(str(extracted))
  for name in (
    "Times New Roman.ttf", "Times New Roman Bold.ttf",
    "Times New Roman Italic.ttf", "Times New Roman Bold Italic.ttf",
  ):
    font_manager.fontManager.addfont(str(FONT_ROOT / name))
  plt.rcParams.update({
    "font.family": ["Times New Roman", "Songti SC"],
    "font.size": 9,
    "axes.labelsize": 9,
    "axes.titlesize": 10,
    "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5,
    "legend.fontsize": 8.5,
    "axes.linewidth": 0.65,
    "axes.edgecolor": BLACK,
    "axes.labelcolor": BLACK,
    "text.color": BLACK,
    "xtick.color": BLACK,
    "ytick.color": BLACK,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "xtick.major.size": 3,
    "ytick.major.size": 3,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",
    "svg.hashsalt": "llm-rationale-benchmark-paper",
  })


def write_csv(name: str, rows: list[dict[str, Any]]) -> None:
  """Save the exact figure data with stable columns and full precision."""
  fields = list(dict.fromkeys(key for row in rows for key in row))
  with (OUTPUT / f"{name}.csv").open("w", newline="", encoding="utf-8-sig") as out:
    writer = csv.DictWriter(out, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)


def save_figure(fig: Any, name: str) -> dict[str, Any]:
  """Save fixed-size figure outputs without changing layout by tight cropping."""
  outputs = {}
  for extension in ("svg", "pdf", "png"):
    path = OUTPUT / f"{name}.{extension}"
    options: dict[str, Any] = {}
    if extension == "svg":
      options["metadata"] = {"Date": None, "Creator": "类人决策评测工具"}
    elif extension == "pdf":
      options["metadata"] = {"CreationDate": None, "ModDate": None}
    fig.savefig(path, dpi=DPI, **options)
    outputs[extension] = str(path.relative_to(ROOT))
  width, height = fig.get_size_inches()
  plt.close(fig)
  return {
    "files": outputs,
    "data_csv": f"paper/figures/{name}.csv",
    "width_inches": float(width),
    "height_inches": float(height),
    "png_dpi": DPI,
  }


def workflow() -> dict[str, Any]:
  """Draw the six-step workflow in a two-row serpentine arrangement."""
  fig = plt.figure(figsize=(WIDTH, 3.0))
  ax = fig.add_axes([0.025, 0.04, 0.95, 0.93])
  ax.set(xlim=(0, 1), ylim=(0, 1))
  ax.axis("off")
  steps = [
    (1, 0, 0, "研究问题", "目标人群与应用情境\n选择分布或条件效应"),
    (2, 0, 1, "材料与对照", "等价题项与操纵检查\n核对人类参照"),
    (3, 0, 2, "施测设计", "固定提示与比较条件\n确定重复次数"),
    (4, 1, 2, "回答检查", "有效分母与缺失模式\n明确排除规则"),
    (5, 1, 1, "行为比较", "单题比例与条件差分\n对齐分数与简单基线"),
    (6, 1, 0, "解释与新研究", "跨材料和批次复核\n形成可检验假设"),
  ]
  xs = [0.16, 0.50, 0.84]
  ys = [0.75, 0.28]
  box_w, box_h = 0.275, 0.34
  rows = []
  centers = []
  for step, row, col, title, details in steps:
    x, y = xs[col], ys[row]
    centers.append((x, y))
    ax.add_patch(Rectangle(
      (x - box_w / 2, y - box_h / 2), box_w, box_h,
      facecolor="white", edgecolor=BLACK, linewidth=0.8,
    ))
    ax.text(x, y + 0.087, f"{step}  {title}", ha="center", va="center", fontsize=10)
    ax.text(x, y - 0.047, details, ha="center", va="center", fontsize=8.8,
            linespacing=1.5)
    rows.append({
      "step": step, "row": row + 1, "column": col + 1,
      "title": title, "details": details.replace("\n", "；"),
    })
  for i in range(5):
    x1, y1 = centers[i]
    x2, y2 = centers[i + 1]
    if y1 == y2:
      direction = 1 if x2 > x1 else -1
      start = (x1 + direction * (box_w / 2 + 0.007), y1)
      end = (x2 - direction * (box_w / 2 + 0.007), y2)
    else:
      start = (x1, y1 - box_h / 2 - 0.012)
      end = (x2, y2 + box_h / 2 + 0.012)
    ax.add_patch(FancyArrowPatch(
      start, end, arrowstyle="-|>", mutation_scale=11,
      linewidth=0.85, color=BLACK,
    ))
  write_csv("workflow", rows)
  return {
    **save_figure(fig, "workflow"),
    "number": 1,
    "caption": (
      "图1　类人决策研究的设计与解释流程。从目标人群与研究问题出发，"
      "安排材料对照与施测，检查回答后比较分布和条件效应，"
      "并通过跨材料及批次验证形成后续假设。"
    ),
    "datasets": ["概念流程图；不编码经验样本量或效应量"],
    "source_files": [
      "paper/manuscript.md",
    ],
  }


def wilson(count: int, sample_size: int) -> tuple[float, float]:
  """Return a marginal two-sided 95 percent Wilson score interval."""
  z = 1.959963984540054
  p = count / sample_size
  denominator = 1 + z * z / sample_size
  center = (p + z * z / (2 * sample_size)) / denominator
  half = z * math.sqrt(
    p * (1 - p) / sample_size + z * z / (4 * sample_size * sample_size)
  ) / denominator
  lower = 0.0 if count == 0 else max(0.0, center - half)
  upper = 1.0 if count == sample_size else min(1.0, center + half)
  return lower, upper


def framing(audit: dict[str, Any]) -> dict[str, Any]:
  """Plot the tutorial's single-source 600-life example with Wilson intervals."""
  choices = [
    ("human", "人类参考", "risky-choice-framing-aliyun-results.json"),
    (
      "aliyun/deepseek-v4-pro (0)", "deepseek-v4-pro (0)",
      "risky-choice-framing-thinking-results.json",
    ),
    (
      "aliyun/qwen3.5-plus", "qwen3.5-plus",
      "risky-choice-framing-aliyun-results.json",
    ),
    (
      "aliyun/qwen3.6-max-preview", "qwen3.6-max-preview",
      "risky-choice-framing-aliyun-results.json",
    ),
  ]
  frames = [
    ("P", "5-P-600life", "正框架", -0.14, "o", "white"),
    ("N", "6-N-600life", "负框架", 0.14, "s", BLACK),
  ]
  fig = plt.figure(figsize=(WIDTH, 3.10))
  ax = fig.add_axes([0.10, 0.245, 0.88, 0.665])
  rows = []
  labels = []
  for x, (model_id, label, source_file) in enumerate(choices):
    ns = []
    for frame, item_id, _, offset, marker, fill in frames:
      item = next(
        r for r in audit["source_item_distributions"]
        if r["source_file"] == source_file and r["question_id"] == item_id
      )
      if model_id == "human":
        entry = item["human"]
      else:
        matches = [
          r for r in audit["source_item_distributions"]
          if r["questionnaire_id"] == "risky-choice-framing"
          and r["question_id"] == item_id
          and any(m["llm_id"] == model_id for m in r["llms"])
        ]
        assert len(matches) == 1, "Intervals require a single source per model."
        entry = next(m for m in item["llms"] if m["llm_id"] == model_id)
      count = next(r["count"] for r in entry["responses"] if r["option"] == "B")
      n = entry["population"]
      p = count / n
      low, high = wilson(count, n)
      ns.append(n)
      ax.errorbar(
        x + offset, p, yerr=[[p - low], [high - p]],
        fmt=marker, color=BLACK, markerfacecolor=fill,
        markeredgecolor=BLACK, markersize=5.1, markeredgewidth=0.85,
        elinewidth=0.85, capsize=3, capthick=0.85, zorder=3,
      )
      rows.append({
        "group": label, "llm_id": model_id, "frame": frame,
        "question_id": item_id, "source_file": source_file,
        "plan_b_count": count, "effective_n": n, "plan_b_rate": p,
        "wilson_95_lower": low, "wilson_95_upper": high,
      })
    assert ns[0] == ns[1]
    labels.append(f"{label}\nn = {ns[0]}")
  handles = [
    Line2D([], [], linestyle="none", marker=marker, markersize=5,
           markerfacecolor=fill, markeredgecolor=BLACK, label=label)
    for _, _, label, _, marker, fill in frames
  ]
  ax.legend(handles=handles, loc="upper left", frameon=False, ncol=2,
            bbox_to_anchor=(0.0, 1.14), handletextpad=0.5, columnspacing=1.7)
  ax.set(xticks=range(4), xticklabels=labels, xlim=(-0.5, 3.5),
         ylim=(-0.025, 1.02), yticks=[0, 0.2, 0.4, 0.6, 0.8, 1.0])
  ax.set_ylabel("B 选择率", labelpad=8)
  ax.tick_params(axis="x", length=0, pad=9)
  ax.yaxis.grid(True, color=LIGHT, linewidth=0.45, zorder=0)
  write_csv("framing", rows)
  return {
    **save_figure(fig, "framing"),
    "number": 2,
    "caption": (
      "图2　600人疾病题在正负框架下的B选择率。点为有效回答比例，误差线"
      "为逐条件95% Wilson区间；n为每一框架条件的有效回答数。所选模型配置"
      "在该任务均仅出现于单一源文件。区间以条件内回答可视作独立同分布"
      "二项样本为前提，不是框架差值的配对区间，不用于判定人机差异显著性。"
      "配置(0)为非思考；无后缀配置不补推其历史思考设置。"
    ),
    "datasets": rows,
    "source_files": sorted({r["source_file"] for r in rows}),
    "interval_method": {
      "name": "Wilson score interval", "confidence_level": 0.95,
      "z": 1.959963984540054, "unit": "condition-specific B count / effective n",
      "assumption": "Independent identically distributed Bernoulli responses",
      "not_estimated": ["paired framing-effect interval", "significance tests"],
    },
  }


def profiles(audit: dict[str, Any]) -> dict[str, Any]:
  """Show five supported DecisionPremise profiles and all 19 configurations."""
  dimensions = [
    ("frp", "选择程序偏好 FRP"),
    ("kp", "亲缘溢价 KP"),
    ("sc", "规模保守性 SC"),
    ("gpr", "概率收益响应 GPR"),
    ("sbs", "确定收益敏感性 SBS"),
  ]
  fig = plt.figure(figsize=(WIDTH, 3.0))
  ax = fig.add_axes([0.275, 0.21, 0.70, 0.65])
  rng = random.Random(20260527)
  rows = []
  for row, (key, _) in enumerate(dimensions):
    y = 4 - row
    summary = audit["metric_summary"]["decision-premise"][key]
    ax.plot([summary["mean"], summary["human"]], [y, y],
            color="0.76", linewidth=0.7, zorder=1)
    for model in audit["model_table"]:
      value = model["questionnaires"]["decision-premise"]["profiles"]["llm"][key]
      jitter = rng.uniform(-0.15, 0.15)
      ax.scatter(value, y + jitter, s=13, color=GRAY, alpha=0.8,
                 linewidths=0, zorder=2)
      rows.append({
        "metric": key.upper(), "agent_type": "model_configuration",
        "llm_id": model["llm_id"], "value": value,
        "plotted_y": y + jitter,
      })
    ax.scatter(summary["mean"], y, s=32, color=BLACK, marker="o", zorder=4)
    ax.scatter(summary["human"], y, s=43, facecolors="white",
               edgecolors=BLACK, marker="D", linewidths=1.0, zorder=4)
    for agent, value in (("model_mean", summary["mean"]),
                         ("human_reference", summary["human"])):
      rows.append({
        "metric": key.upper(), "agent_type": agent,
        "llm_id": "", "value": value, "plotted_y": y,
      })
  ax.axvline(0, color="0.35", linewidth=0.7, linestyle=(0, (2, 3)), zorder=0)
  ax.set(yticks=range(5), yticklabels=[label for _, label in reversed(dimensions)],
         ylim=(-0.5, 4.5), xlim=(-0.065, 0.34),
         xticks=[-0.05, 0, 0.1, 0.2, 0.3])
  ax.set_xlabel("指标值（B 选择率或条件差分）", labelpad=7)
  ax.tick_params(axis="y", length=0, pad=9)
  ax.spines["left"].set_visible(False)
  handles = [
    Line2D([], [], linestyle="none", marker="o", markersize=4,
           markerfacecolor=GRAY, markeredgecolor=GRAY, label="模型配置（19）"),
    Line2D([], [], linestyle="none", marker="o", markersize=5,
           markerfacecolor=BLACK, markeredgecolor=BLACK, label="模型均值"),
    Line2D([], [], linestyle="none", marker="D", markersize=5,
           markerfacecolor="white", markeredgecolor=BLACK, label="人类参考"),
  ]
  fig.legend(handles=handles, loc="upper center", frameon=False,
             bbox_to_anchor=(0.62, 0.995), ncol=3, columnspacing=1.4,
             handletextpad=0.4)
  write_csv("profiles", rows)
  return {
    **save_figure(fig, "profiles"),
    "number": 3,
    "caption": (
      "图3　决策前提任务的五项行为指标。灰点为19个模型配置，深色圆点为"
      "配置等权均值，空心菱形为人类参考值。纵向微移只用于显示重叠点；"
      "横向散布反映配置差异，不是模型总体的抽样置信区间。FRP按材料"
      "保守称为选择程序偏好；作答者自身年龄操纵未进入当前提示，因此不展示SAM。"
    ),
    "datasets": {
      "questionnaire": "decision-premise", "configurations": 19,
      "metrics": [key.upper() for key, _ in dimensions],
      "model_average": "equal configuration weights",
      "jitter": {"axis": "y only", "seed": 20260527, "range": [-0.15, 0.15]},
      "intervals": "none; configuration spread is descriptive",
    },
    "source_files": [
      "decision-premise-aliyun-results.json",
      "decision-premise-deepseek-results.json",
      "decision-premise-thinking-results.json",
    ],
  }


def short_label(model_id: str) -> str:
  """Return distinct compact identifiers for the sensitivity figure."""
  label = model_id.removeprefix("aliyun/")
  label = label.replace("deepseek-", "DS-")
  label = label.replace("qwen", "Q").replace("glm-", "GLM-")
  label = label.replace("-a10b", "").replace("-a3b", "").replace("-a17b", "")
  label = label.replace("-preview", "")
  label = label.replace("122b", "122B").replace("397b", "397B")
  label = label.replace("35b", "35B")
  label = label.replace(" (-1)", " / T").replace(" (0)", " / NT")
  return label


def sensitivity(audit: dict[str, Any]) -> dict[str, Any]:
  """Compare item exclusion and duplicate weighting without magnifying noise."""
  fig = plt.figure(figsize=(WIDTH, 4.8))
  ax = fig.add_axes([0.225, 0.105, 0.425, 0.79])
  table_ax = fig.add_axes([0.705, 0.105, 0.275, 0.79])
  table_ax.set(xlim=(0, 1), ylim=(0, 1))
  table_ax.axis("off")
  archived = {m["llm_id"]: m for m in audit["model_table"]}
  revised = audit["sensitivity"]["exclude_four_age_items"]["models"]
  ordered = sorted(revised, key=lambda m: archived[m["llm_id"]]["overall_pas_rank"])
  rows = []
  labels = []
  for index, item in enumerate(ordered):
    y = 18 - index
    model_id = item["llm_id"]
    before = archived[model_id]["overall"]["pas"]
    after = item["revised_overall"]["pas"]
    ax.plot([before, after], [y, y], color="0.65", linewidth=1.2, zorder=1)
    ax.scatter(before, y, s=25, facecolors="white", edgecolors=GRAY,
               linewidths=0.85, marker="o", zorder=3)
    ax.scatter(after, y, s=23, color=BLACK, marker="D", zorder=4)
    label = short_label(model_id)
    labels.append(label)
    rows.append({
      "panel": "A", "llm_id": model_id, "short_label": label,
      "score_scope": "overall", "archived_pas": before,
      "alternative_pas": after, "delta_pas": after - before,
      "archived_rank": archived[model_id]["overall_pas_rank"],
      "alternative_rank": item["revised_overall_rank"],
      "alternative_rule": "exclude four Py/Pm age-labelled items",
    })
  ax.set(yticks=range(19), yticklabels=list(reversed(labels)),
         ylim=(-0.7, 18.7), xlim=(47, 67), xticks=[50, 55, 60, 65])
  ax.set_xlabel("等权总 PAS", labelpad=8)
  ax.tick_params(axis="y", length=0, pad=6, labelsize=8.2)
  ax.spines["left"].set_visible(False)
  ax.xaxis.grid(True, color=LIGHT, linewidth=0.45, zorder=0)
  ax.set_title("(A) 题项构成", loc="left", pad=25, fontsize=10)
  handles = [
    Line2D([], [], linestyle="none", marker="o", markersize=4.5,
           markerfacecolor="white", markeredgecolor=GRAY, label="存档评分"),
    Line2D([], [], linestyle="none", marker="D", markersize=4,
           markerfacecolor=BLACK, markeredgecolor=BLACK, label="移除4年龄题"),
  ]
  ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(-0.025, 1.0),
            frameon=False, ncol=2, handletextpad=0.4, columnspacing=0.8,
            fontsize=8.1)
  table_ax.text(0, 1.083, "(B) 汇总权重", fontsize=10, va="bottom")
  table_ax.text(0, 0.99, "DeepSeek-v4-pro（T）", fontsize=9, va="top")
  table_ax.text(0, 0.929, "源文件等权 → 按计数合并", fontsize=8.5, va="top")
  duplicate = audit["sensitivity"]["duplicate_count_pooling"]
  scopes = [
    ("decision-premise", "决策前提", 0.80),
    ("risky-choice-framing", "风险框架", 0.59),
    ("overall", "等权总分", 0.38),
  ]
  for scope, label, y in scopes:
    if scope == "overall":
      old = duplicate["source_equal_distribution_overall"]
      new = duplicate["count_pooled_overall"]
    else:
      old = duplicate["source_equal_distribution_scores"][scope]
      new = duplicate["count_pooled_scores"][scope]
    delta = new["pas"] - old["pas"]
    delta_text = "0.000000" if abs(delta) < 0.0000005 else f"{delta:+.6f}"
    table_ax.text(0, y, label, fontsize=9, va="top")
    table_ax.text(0, y - 0.063, f"{old['pas']:.6f} → {new['pas']:.6f}",
                  fontsize=8.7, va="top")
    table_ax.text(0, y - 0.119, f"Δ PAS = {delta_text}", fontsize=8.7, va="top")
    table_ax.plot([0, 1], [y - 0.165, y - 0.165], color=LIGHT, linewidth=0.6)
    rows.append({
      "panel": "B", "llm_id": duplicate["llm_id"],
      "short_label": "DS-v4-pro / T", "score_scope": scope,
      "archived_pas": old["pas"], "alternative_pas": new["pas"],
      "delta_pas": delta, "alternative_rule": "pool source answer counts",
      "archived_bas": old["bas"], "alternative_bas": new["bas"],
      "archived_fas": old["fas"], "alternative_fas": new["fas"],
    })
  table_ax.text(0, 0.143, "原评分标度为0–100\n未放大小差异；总体排序不变",
                fontsize=8.4, va="top", linespacing=1.6)
  write_csv("sensitivity", rows)
  return {
    **save_figure(fig, "sensitivity"),
    "number": 4,
    "caption": (
      "图4　题项构成与跨文件汇总规则的事后敏感性分析。A：空心圆为存档"
      "全量评分，深色菱形为移除决策前提四年龄题后重算的等权总PAS；"
      "模型按原总分排序，移除题项改变测量范围，不能补救原操纵。"
      "B：DeepSeek-v4-pro思考配置按源分布等权与按有效计数合并的PAS比较；"
      "差异以原0–100分标度列示，未放大微小变化。T和NT分别表示配置中"
      "显式标记的思考与非思考；无后缀配置不推断其模式。"
    ),
    "datasets": {
      "panel_A": "19 configurations; original 15-item versus retained 11-item DP",
      "panel_A_equal_task_weights": True,
      "panel_B": duplicate["llm_id"],
      "panel_B_rule": "source equal distribution mean versus pooled answer counts",
      "intervals": "none; deterministic post hoc reanalysis",
      "short_label_mapping": {
        m["llm_id"]: short_label(m["llm_id"]) for m in audit["model_table"]
      },
    },
    "source_files": [s["file"] for s in audit["source_files"]],
  }


def main() -> None:
  """Build all figures and their machine-readable publication manifest."""
  OUTPUT.mkdir(parents=True, exist_ok=True)
  prepare_style()
  audit = json.loads(AUDIT.read_text())
  figures = {
    "workflow": workflow(),
    "framing": framing(audit),
    "profiles": profiles(audit),
    "sensitivity": sensitivity(audit),
  }
  manifest = {
    "source_audit": "paper/data_audit.json",
    "figure_data_provenance": "CSV values retain unrounded source precision",
    "style": {
      "background": "white", "palette": "grayscale",
      "chinese_font": "Songti SC Regular, Songti.ttc face 6",
      "latin_font": "Times New Roman",
      "minimum_font_points": 8.1,
      "width_inches": WIDTH, "png_dpi": DPI,
      "svg_text": "editable text with registered fonts",
      "pdf": "vector artwork with embedded TrueType fonts",
    },
    "figures": figures,
  }
  path = OUTPUT / "figure_manifest.json"
  path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
  print(json.dumps({
    name: {"files": data["files"], "caption": data["caption"]}
    for name, data in figures.items()
  }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
  main()
