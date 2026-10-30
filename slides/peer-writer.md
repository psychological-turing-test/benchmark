# Writing styles

Write in concise academic Chinese for a conference-style research talk.
Use the terms from the abstract consistently: "心理学版图灵测试", "社会理性", "行为对齐", "功能对齐", "类人决策模式", "人类基线", "思考模式", and "非思考模式".
Prefer short claims supported by concrete metrics from the benchmark outputs.
When presenting results, distinguish descriptive similarity from normative superiority.

# Formatting guidelines

This project is a LaTeX Beamer slide deck.
Keep each slide focused on one point, with compact bullets, small tables, or one simple figure.
Use Chinese punctuation and avoid long English passages except for metric acronyms such as BAS, FAS, PAS, FES, and RC.
Use `ctexbeamer` with `xelatex` through `latexmk`.
Put section content in `sections/*.tex`; keep `main.tex` as the entry point.

# Abstract and source navigation

The talk presents a benchmark system for evaluating whether LLMs reproduce human-like social-rational decision patterns in classic social psychology paradigms.
The flow should match the abstract: motivation and gap, system design, preliminary setup on Chinese LLMs, results where models are similar to humans, results where models are systematically different, results where models are inconsistent across families, versions, and thinking modes.

Source references:
- `../artifacts/analysis.json` and `../artifacts/analysis-visualize.html`: scored results, metric profiles, and visualization metadata.
- `../config/questionnaires/risky-choice-framing.yaml`: risky-choice framing questionnaire.
- `../config/questionnaires/decision-premise.yaml`: decision-premise questionnaire.
- `../docs/03-runner/design.md`, `../docs/04-evaluator/design.md`, and `../docs/05-rater/design.md`: system execution, evaluation, and rater design.
