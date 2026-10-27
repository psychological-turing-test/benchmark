"""Recompute the paper's descriptive audit without querying any models.

Run with the bundled Python runtime and ``-B``. Only data_audit.json is written;
the source results, questionnaires, and implementation remain unchanged.
"""

from __future__ import annotations

import hashlib
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from rationale_benchmark.rater.analysis import build_analysis_payload
from rationale_benchmark.rater.loader import discover_result_files, load_results
from rationale_benchmark.rater.models import EvaluatorQuestionResult
from rationale_benchmark.rater.scoring import score_questionnaire

SCORE_KEYS = ("bas", "vas", "srs")
AGE_IDS = {"1-Py-old", "2-Py-young", "1-Pm-old", "2-Pm-young"}


def describe(values: list[float]) -> dict[str, float]:
  """Describe variation across the model configurations, not sampling error."""
  return {
    "mean": statistics.mean(values),
    "min": min(values),
    "max": max(values),
    "sd_across_configurations": statistics.stdev(values),
  }


def distribution(entry: dict[str, Any]) -> dict[str, float]:
  """Return the recorded option proportions."""
  return {r["option"]: r["percentage"] for r in entry["responses"]}


def scores(entry: Any) -> dict[str, float]:
  """Extract BAS, VAS, and SRS from a dictionary or rating object."""
  if isinstance(entry, dict):
    return {key: entry[key] for key in SCORE_KEYS}
  return {key: getattr(entry, key) for key in SCORE_KEYS}


def dp_scores(items: list[dict[str, Any]]) -> dict[str, float]:
  """Calculate current DecisionPremise scores from item Plan-B rates."""
  errors = [abs(i["llm"][0] - i["human"][0]) for i in items]
  bas = 100 * (1 - statistics.mean(errors))
  vas = max(0.0, 100 * (1 - math.sqrt(statistics.mean(e * e for e in errors))))
  return {"bas": bas, "vas": vas, "srs": (bas + vas) / 2}


def raw_run_summary(source_name: str) -> dict[str, Any]:
  """Inspect matching local logs without exporting response or header text."""
  matches = list((PROJECT_ROOT / "results").glob(f"*/{source_name}"))
  if not matches:
    return {"available": False}
  result_path = matches[0]
  result: dict[str, Any] = {
    "available": True,
    "directory": str(result_path.parent.relative_to(PROJECT_ROOT)),
  }
  artifact = PROJECT_ROOT / "artifacts" / source_name
  local_rows = json.loads(result_path.read_text())
  artifact_rows = json.loads(artifact.read_text())
  result["result_bytes_identical"] = artifact.read_bytes() == result_path.read_bytes()
  for item in local_rows:
    for model in item["llms"]:
      model["llm_id"] = model["llm_id"].replace(
        "aliyun_openai_compatible/", "aliyun/"
      )
  result["results_equal_after_provider_prefix_normalization"] = (
    local_rows == artifact_rows
  )
  for file_name, payload_key in (
    ("responses.jsonl", "response"),
    ("metadata.jsonl", "metadata"),
  ):
    path = result_path.parent / file_name
    if not path.exists():
      continue
    records = [json.loads(line) for line in path.read_text().splitlines() if line]
    model_counts = Counter(r["llm_id"] for r in records)
    keys: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    times = [r["query_time"] for r in records]
    provider_keys: set[str] = set()
    recorded_settings: dict[str, set[str]] = defaultdict(set)
    attempts = 0
    retried = 0
    validation_errors = 0
    formatting_repairs: Counter[str] = Counter()
    question_entries = 0
    for record in records:
      keys[(record["llm_id"], record["population_index"])].append(record)
      for section in record.get(payload_key, {}).get("sections", []):
        for question in section["questions"]:
          question_entries += 1
          aa = question.get("attempts", [])
          attempts += len(aa)
          retried += len(aa) > 1
          for attempt in aa:
            validation_errors += bool(attempt.get("validation_error"))
            metadata = attempt.get("provider_metadata", {})
            provider_keys.update(metadata)
            repair = metadata.get("aliyun_json_formatting")
            if isinstance(repair, dict):
              formatting_repairs[str(repair.get("model", "unknown"))] += 1
            for setting in (
              "temperature", "top_p", "seed", "max_tokens",
              "enable_thinking", "thinking_budget", "reasoning_effort",
            ):
              if setting in metadata:
                recorded_settings[setting].add(str(metadata[setting]))
    repeated = [group for group in keys.values() if len(group) > 1]
    result[file_name] = {
      "records": len(records),
      "records_per_model": dict(model_counts),
      "query_time_range": [min(times), max(times)],
      "top_level_error_entries": sum(len(r["errors"]) for r in records),
      "question_entries": question_entries,
      "reused_model_population_keys": len(repeated),
      "identical_repeated_records": sum(g[0] == g[1] for g in repeated),
      "same_timestamp_repeated_records": sum(
        g[0]["query_time"] == g[1]["query_time"] for g in repeated
      ),
      "provider_metadata_keys": sorted(provider_keys),
      "recorded_request_settings": {
        k: sorted(v) for k, v in recorded_settings.items()
      },
      "recorded_attempts": attempts,
      "questions_with_multiple_attempts": retried,
      "attempts_with_validation_errors": validation_errors,
      "auxiliary_json_formatting_attempts_by_model": dict(formatting_repairs),
    }
  return result


def main() -> None:
  """Write a reproducible quantitative audit for the current paper snapshot."""
  artifacts = PROJECT_ROOT / "artifacts"
  source_paths = discover_result_files(artifacts)
  old = json.loads((artifacts / "analysis.json").read_text())
  loaded = load_results(artifacts)
  computed = build_analysis_payload([p.name for p in source_paths], loaded)
  groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
  human: dict[tuple[str, str], dict[str, Any]] = {}
  sources = []
  source_items = []
  count_errors = []
  for path in source_paths:
    rows = json.loads(path.read_text())
    sample_sizes = []
    for row in rows:
      qid, item_id = row["questionnaire_id"], row["question_id"]
      human_key = (qid, item_id)
      if human_key in human:
        assert human[human_key]["human"] == row["human"]
      human[human_key] = row
      source_items.append({
        "source_file": path.name,
        "questionnaire_id": qid,
        "question_id": item_id,
        "human": row["human"],
        "llms": row["llms"],
      })
      for model in row["llms"]:
        group = {"source_file": path.name, **model}
        groups[(qid, item_id, model["llm_id"])].append(group)
        sample_sizes.append(model["population"])
        if sum(r["count"] for r in model["responses"]) != model["population"]:
          count_errors.append([path.name, item_id, model["llm_id"], "count"])
        if any(
          abs(r["count"] / model["population"] - r["percentage"]) > 1e-9
          for r in model["responses"]
        ):
          count_errors.append([path.name, item_id, model["llm_id"], "proportion"])
    sources.append({
      "file": path.name,
      "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
      "questionnaire_id": rows[0]["questionnaire_id"],
      "items": len(rows),
      "model_configurations": len({m["llm_id"] for r in rows for m in r["llms"]}),
      "distribution_cells": len(sample_sizes),
      "recorded_response_count": sum(sample_sizes),
      "item_sample_size_histogram": dict(sorted(Counter(sample_sizes).items())),
      "raw_run": raw_run_summary(path.name),
    })

  model_table = []
  score_differences = []
  for original, model in zip(old["models"], computed["models"]):
    assert original["llm_id"] == model["llm_id"]
    model_id = model["llm_id"]
    table_row = {
      "llm_id": model_id,
      "display_name": model["display_name"],
      "overall": scores(model),
      "questionnaires": {},
    }
    for qid, task in model["questionnaires"].items():
      metric_data = task["details"]["behavioral_tendency_metrics"]
      if qid == "decision-premise":
        profiles = metric_data["profile"]
      else:
        profiles = {agent: metric_data[agent]["profile"] for agent in ("human", "llm")}
      item_ns = {
        item: sum(x["population"] for x in entries)
        for (q, item, m), entries in groups.items()
        if q == qid and m == model_id
      }
      table_row["questionnaires"][qid] = {
        **scores(task),
        "profiles": profiles,
        "item_recorded_sample_sizes": item_ns,
        "item_sample_size_range": [min(item_ns.values()), max(item_ns.values())],
        "summed_recorded_responses": sum(item_ns.values()),
      }
      for key in SCORE_KEYS:
        delta = task[key] - original["questionnaires"][qid][key]
        if abs(delta) > 1e-9:
          score_differences.append([model_id, qid, key, delta])
    model_table.append(table_row)
  ranking = sorted(model_table, key=lambda m: m["overall"]["srs"], reverse=True)
  for rank, row in enumerate(ranking, 1):
    row["overall_srs_rank"] = rank

  summary = {}
  for scope in ("overall", "decision-premise", "risky-choice-framing"):
    summary[scope] = {}
    for key in SCORE_KEYS:
      values = [
        m["overall"][key] if scope == "overall"
        else m["questionnaires"][scope][key]
        for m in model_table
      ]
      summary[scope][key] = describe(values)
  metric_summary = {}
  for qid in ("decision-premise", "risky-choice-framing"):
    profiles = [m["questionnaires"][qid]["profiles"] for m in model_table]
    metric_summary[qid] = {
      key: {
        "human": profiles[0]["human"][key],
        **describe([p["llm"][key] for p in profiles]),
      }
      for key in profiles[0]["human"]
    }
  magnitude_summary = {}
  for domain in ("life", "painting", "dollar"):
    magnitude_summary[domain] = {}
    for component in ("p", "n", "mean"):
      metrics = [
        m["questionnaires"]["risky-choice-framing"]["details"]
        ["behavioral_tendency_metrics"]
        for m in computed["models"]
      ]
      magnitude_summary[domain][component] = {
        "human": metrics[0]["human"]["ms"][domain][component],
        **describe([d["llm"]["ms"][domain][component] for d in metrics]),
      }

  excluded_age = []
  for model in computed["models"]:
    dp = model["questionnaires"]["decision-premise"]
    retained = [i for i in dp["details"]["bas_items"] if i["label"] not in AGE_IDS]
    assert len(retained) == 11
    revised = dp_scores(retained)
    framing = model["questionnaires"]["risky-choice-framing"]
    overall = {k: (revised[k] + framing[k]) / 2 for k in SCORE_KEYS}
    excluded_age.append({
      "llm_id": model["llm_id"],
      "original_decision_premise": scores(dp),
      "revised_decision_premise": revised,
      "revised_overall": overall,
      "overall_srs_change": overall["srs"] - model["srs"],
    })
  for rank, row in enumerate(
    sorted(excluded_age, key=lambda r: r["revised_overall"]["srs"], reverse=True), 1
  ):
    row["revised_overall_rank"] = rank
  revised_lookup = {m["llm_id"]: m for m in excluded_age}
  revised_mode_deltas = []
  for base in (
    "aliyun/deepseek-v4-pro", "aliyun/glm-5.1",
    "aliyun/qwen3.5-plus", "aliyun/qwen3.6-plus",
  ):
    no_thinking = revised_lookup[f"{base} (0)"]
    thinking = revised_lookup[f"{base} (-1)"]
    revised_mode_deltas.append({
      "base_model_id": base,
      "decision_premise_srs_no_thinking_minus_thinking": (
        no_thinking["revised_decision_premise"]["srs"]
        - thinking["revised_decision_premise"]["srs"]
      ),
      "overall_srs_no_thinking_minus_thinking": (
        no_thinking["revised_overall"]["srs"]
        - thinking["revised_overall"]["srs"]
      ),
    })

  duplicate_cells = []
  for (qid, item, model), entries in groups.items():
    if len(entries) < 2:
      continue
    arithmetic = {
      option: statistics.mean(distribution(e)[option] for e in entries)
      for option in distribution(entries[0])
    }
    count_pooled = {
      option: sum(
        next(r["count"] for r in e["responses"] if r["option"] == option)
        for e in entries
      ) / sum(e["population"] for e in entries)
      for option in arithmetic
    }
    duplicate_cells.append({
      "questionnaire_id": qid,
      "question_id": item,
      "llm_id": model,
      "source_sample_sizes": [e["population"] for e in entries],
      "source_proportions": [distribution(e) for e in entries],
      "source_equal_distribution_mean": arithmetic,
      "count_pooled_distribution": count_pooled,
      "plan_b_difference_count_pooled_minus_source_mean": (
        count_pooled["B"] - arithmetic["B"]
      ),
    })
  duplicate_model = "aliyun/deepseek-v4-pro (-1)"
  original_duplicate = next(
    m for m in computed["models"] if m["llm_id"] == duplicate_model
  )
  pooled_scores = {}
  constant_a_scores = {}
  for qid in ("decision-premise", "risky-choice-framing"):
    pooled_results = []
    constant_results = []
    for (q, item), row in human.items():
      if q != qid:
        continue
      entries = groups[(q, item, duplicate_model)]
      denominator = sum(e["population"] for e in entries)
      pooled = {
        option: sum(
          next(r["count"] for r in e["responses"] if r["option"] == option)
          for e in entries
        ) / denominator
        for option in ("A", "B")
      }
      arguments = ("audit", qid, row["section_name"], item, distribution(row["human"]))
      pooled_results.append(
        EvaluatorQuestionResult(*arguments, {duplicate_model: pooled})
      )
      constant_results.append(
        EvaluatorQuestionResult(*arguments, {"constant-A": {"A": 1.0, "B": 0.0}})
      )
    pooled_scores[qid] = scores(
      score_questionnaire(qid, duplicate_model, pooled_results)
    )
    constant_a_scores[qid] = scores(
      score_questionnaire(qid, "constant-A", constant_results)
    )
  pooled_overall = {
    k: statistics.mean(t[k] for t in pooled_scores.values()) for k in SCORE_KEYS
  }
  constant_a_scores["overall"] = {
    k: statistics.mean(t[k] for t in constant_a_scores.values()) for k in SCORE_KEYS
  }

  audit = {
    "description": "Descriptive audit of the existing snapshot; no new model calls.",
    "analysis_version": old["version"],
    "verification": {
      "recomputed_score_differences_above_1e_9": score_differences,
      "source_count_or_proportion_errors": count_errors,
      "human_distributions_consistent_across_sources": True,
    },
    "dataset": {
      "source_files": len(sources),
      "questionnaire_item_instances": len(human),
      "model_configurations": len(model_table),
      "base_model_identifiers": len({m["llm_id"].split(" (")[0] for m in model_table}),
      "unique_model_item_cells": len(groups),
      "source_distribution_cells": sum(len(v) for v in groups.values()),
      "summed_recorded_model_responses": sum(
        e["population"] for v in groups.values() for e in v
      ),
      "raw_response_records": sum(
        s["raw_run"]["responses.jsonl"]["records"] for s in sources
      ),
      "raw_question_entries": sum(
        s["raw_run"]["responses.jsonl"]["question_entries"] for s in sources
      ),
      "raw_error_entries": sum(
        s["raw_run"]["responses.jsonl"]["top_level_error_entries"]
        for s in sources
      ),
      "human_items": [
        {
          "questionnaire_id": qid,
          "question_id": item,
          "section_name": row["section_name"],
          **row["human"],
        }
        for (qid, item), row in human.items()
      ],
    },
    "source_files": sources,
    "score_summary": summary,
    "metric_summary": metric_summary,
    "magnitude_sensitivity_summary": magnitude_summary,
    "model_table": model_table,
    "sensitivity": {
      "exclude_four_age_items": {
        "excluded_question_ids": sorted(AGE_IDS),
        "retained_decision_premise_items": 11,
        "models": excluded_age,
        "mode_pair_deltas": revised_mode_deltas,
        "score_summary": {
          scope: {
            k: describe([m[scope][k] for m in excluded_age])
            for k in SCORE_KEYS
          }
          for scope in ("revised_decision_premise", "revised_overall")
        },
      },
      "duplicate_count_pooling": {
        "llm_id": duplicate_model,
        "source_equal_distribution_scores": {
          q: scores(t) for q, t in original_duplicate["questionnaires"].items()
        },
        "count_pooled_scores": pooled_scores,
        "source_equal_distribution_overall": scores(original_duplicate),
        "count_pooled_overall": pooled_overall,
        "overall_srs_change": pooled_overall["srs"] - original_duplicate["srs"],
        "duplicate_cells": duplicate_cells,
      },
      "constant_A_baseline": constant_a_scores,
    },
    "caveats": [
      "Model counts distinguish 19 configurations from 13 base model identifiers.",
      (
        "Recorded per-item response counts vary; 50 is a config default, "
        "not a uniform observed n."
      ),
      (
        "Summing item-level human n does not identify the number of "
        "independent participants."
      ),
      (
        "Human source metadata identifies an internal workbook, not full "
        "study provenance or sampling design."
      ),
      (
        "DecisionPremise VAS compares raw Plan-B rates (RMSE), not "
        "psychological slopes or contrasts."
      ),
      (
        "RiskyChoiceFraming VAS compares frame differences in [-1,1], "
        "divides Euclidean distance by sqrt(18), and clamps to [0,100]; "
        "sqrt(18) is not the theoretical maximum distance between such vectors."
      ),
      "Neither VAS formula establishes shared internal psychological mechanisms.",
      (
        "Current Py/Pm matched prompts and instructions are identical; "
        "age labels only occur in section names, which current prompt "
        "rendering does not send to models. Historical request payloads "
        "are not recorded."
      ),
      (
        "FRP English wording says selected to be saved, without "
        "explicitly specifying random selection."
      ),
      (
        "Repeated DeepSeek-v4-pro thinking distributions are averaged "
        "equally across source files, not count-pooled; the numeric "
        "effect here is small."
      ),
      (
        "DecisionPremise Qwen3.5-plus thinking has two response batches "
        "with reused population indices and distinct times; the second "
        "batch lacks matching metadata records."
      ),
      (
        "Raw provider metadata does not record temperature, top_p, seed, "
        "output-token limit, or actual thinking request settings; current "
        "config cannot establish historical settings."
      ),
      (
        "The nine unsuffixed Qwen configurations have no explicit "
        "thinking-mode label in their result IDs."
      ),
      (
        "DecisionPremise thinking metadata records 792 auxiliary "
        "qwen3.6-flash JSON-formatting attempts in its first batch; "
        "original-choice preservation through this repair is not verified."
      ),
      (
        "Across-configuration means weight model configurations equally "
        "and include correlated model families; reported SD is "
        "descriptive variation, not a confidence interval."
      ),
      (
        "No item-level paired or repeated-measures human sampling "
        "information is available for inferential analysis."
      ),
      (
        "Constant-A is a deliberately simple diagnostic baseline added "
        "by offline reanalysis, not a newly run model."
      ),
      (
        "SBS implementation b_P minus b_Pu agrees with weaker versus "
        "stronger sure outcomes; the current documentation also describes "
        "P-to-Pu as an improvement in Plan A."
      ),
    ],
    "source_item_distributions": source_items,
  }
  output = PROJECT_ROOT / "paper" / "data_audit.json"
  output.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
  print(f"Wrote {output}")
  print(json.dumps({
    "dataset": {k: v for k, v in audit["dataset"].items() if k != "human_items"},
    "verification": audit["verification"],
    "duplicate_pooling_overall_srs_change": (
      audit["sensitivity"]["duplicate_count_pooling"]["overall_srs_change"]
    ),
    "constant_A_baseline": constant_a_scores,
    "age_excluded_top_three": sorted(
      excluded_age, key=lambda m: m["revised_overall"]["srs"], reverse=True
    )[:3],
  }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
  main()
