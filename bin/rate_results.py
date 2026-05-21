#!/usr/bin/env python
"""Rate evaluator result JSON files in one flat directory."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rationale_benchmark.rater import RaterError, rate_results


def main() -> int:
  """Rate evaluator results and report artifact paths."""
  parser = argparse.ArgumentParser(
    description="Rate evaluator result JSON files in one flat directory.",
  )
  parser.add_argument("input_dir", help="Directory containing *-results.json files")
  args = parser.parse_args()

  try:
    result = rate_results(Path(args.input_dir))
  except RaterError as exc:
    print(f"error: {exc}", file=sys.stderr)
    return 1

  print(f"Wrote {result.analysis_json}")
  print(f"Wrote {result.visualization_html}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
