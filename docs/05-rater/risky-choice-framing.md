# RiskyChoiceFraming Behavioral Tendency Metrics

## 1. Overview

The BAS / FAS / PAS scores defined in [rating.md](rating.md) measure how closely an LLM's outputs **match** human results ("how human-like is the output"). This document supplements those with a set of **Behavioral Tendency Metrics (BTMs)** that characterize the intrinsic decision-making profile of a single agent (an LLM or a human sample) on the RiskyChoiceFraming questionnaire.

These metrics satisfy two properties:

- **agent-intrinsic**: they depend only on the agent's own response distribution and require no comparison against a human baseline to be computed;
- **comparable**: identical formulas can be applied to LLM and human samples, enabling side-by-side comparison.

Notation:

- Each scenario provides both a positive-framing (P) and a negative-framing (N) item;
- For any item $i$, let $r_i \in [0, 1]$ denote the agent's probability of choosing the risky option (Plan B); for a single LLM this is estimated from multiple samples;
- Let $r_i^{P}, r_i^{N}$ denote the risky-choice rate on the P and N versions of the same scenario;
- Scenario families $\mathcal{S}$ follow the questionnaire's natural grouping: `life` (6/60/600/6000), `kin` (1/2/3/6), `Human/Alien`, `painting` (6/60/600/6000), `dollar` (6/60/600/6000).

---

## 2. Framing Effect Susceptibility (FES)

### 2.1 Definition

For each scenario, define the local framing effect:

$$
\mathrm{FE}_i = r_i^{N} - r_i^{P}
$$

Per classical prospect theory, humans on average produce $\mathrm{FE}_i > 0$ (more risk-seeking under losses). Aggregating across scenarios:

$$
\mathrm{FES} = \frac{1}{|\mathcal{S}|} \sum_{i \in \mathcal{S}} \mathrm{FE}_i \in [-1, 1]
$$

### 2.2 Interpretation

- $\mathrm{FES} \approx 0$: agent is insensitive to P/N wording ("frame-neutral");
- $\mathrm{FES} > 0$: classic Kahneman–Tversky reflection direction;
- $\mathrm{FES} < 0$: reverse framing effect (rare, useful as an anomaly signal).

### 2.3 Reflection Consistency (RC)

Captures the fraction of scenarios on which the agent reproduces the canonical "risk-averse in gains, risk-seeking in losses" pattern:

$$
\mathrm{RC} = \frac{1}{|\mathcal{S}|} \sum_{i \in \mathcal{S}} \mathbb{1}\!\left[r_i^{P} < 0.5 \;\wedge\; r_i^{N} > 0.5\right] \in [0, 1]
$$

FES vs RC: FES measures **magnitude**, RC measures **frequency**. An agent may have high FES but low RC (a few scenarios contributing most of the framing effect), or vice versa.

---

## 3. Magnitude Sensitivity (MS)

The questionnaire spans 4 orders of magnitude ($10^0$ → $10^3$, $m \in \{6, 60, 600, 6000\}$) within `life`, `painting`, and `dollar`. For each domain $d$ and framing $f \in \{P, N\}$, treat the risky-choice rate as a function of $\log_{10}(m)$ and take the slope:

$$
\mathrm{MS}_{d,f} = \mathrm{slope}\!\left(\log_{10}(m_k),\; r_{d,f,k}\right), \quad k = 1, \dots, 4
$$

Aggregate across framings:

$$
\mathrm{MS}_{d} = \frac{\mathrm{MS}_{d,P} + \mathrm{MS}_{d,N}}{2}
$$

### Interpretation

- $\mathrm{MS}_{d} < 0$: larger scale → more conservative (matches the human trend on `life` — e.g. P-life drops monotonically from 0.64 at 6 lives to 0.41 at 6000);
- $\mathrm{MS}_{d} \approx 0$: scope-insensitive;
- $\mathrm{MS}_{d} > 0$: larger scale → more risk-seeking.

Also report the **cross-domain MS spectrum** $\big(\mathrm{MS}_{\text{life}}, \mathrm{MS}_{\text{painting}}, \mathrm{MS}_{\text{dollar}}\big)$ to test whether the agent shows a consistent scope direction across different value carriers.

---

## 4. Kinship Gradient (KG)

In the `kin` subset, the number of affected family members rises from 1 to 6 (1/6 → 1 of a fixed 6-person group). Define:

$$
\mathrm{KG}_{f} = \mathrm{slope}\!\left(k,\; r_{\text{kin}, f, k}\right), \quad k \in \{1, 2, 3, 6\}
$$

$$
\mathrm{KG} = \frac{\mathrm{KG}_{P} + \mathrm{KG}_{N}}{2}
$$

### Interpretation

- $\mathrm{KG} > 0$: a denser kin share pushes the agent toward the "all-or-nothing" risky plan (rejecting a guaranteed partial loss);
- $\mathrm{KG} \approx 0$: kin composition is decision-irrelevant (inconsistent with kin-selection theory);
- $\mathrm{KG} < 0$: more kin → more conservative.

KG is orthogonal to MS: MS varies total stake, while KG varies the **relational density** between the decision-maker and the affected subjects.

---

## 5. In-group Bias (IGB)

Using the `Human vs Alien` pair, for each framing:

$$
\mathrm{IGB}_{f} = r_{\text{Human}, f} - r_{\text{Alien}, f}
$$

$$
\mathrm{IGB} = \frac{\mathrm{IGB}_{P} + \mathrm{IGB}_{N}}{2}
$$

### Interpretation

- Large $|\mathrm{IGB}|$: the agent's choice depends on the identity of the affected subjects, indicating in-/out-group differentiation;
- $\mathrm{IGB} \approx 0$: identity-neutral.

The human baselines for P-Human and P-Alien are 0.36 and 0.52 respectively, giving $\mathrm{IGB}^{P}_{\text{human-sample}} = -0.16$ (humans are **more conservative** when humans themselves are the affected party) — a useful reference value.

---

## 6. Cross-Domain Coherence (CDC)

Let $\bar{r}_d$ be the agent's mean risky-choice rate within domain $d$ (across `lives`, `kin`, `painting`, `dollar`). Define:

$$
\mathrm{CDC} = 1 - \frac{\mathrm{std}\!\left(\{\bar{r}_d\}_d\right)}{0.5}
$$

(0.5 is the upper bound on the std of a distribution on $[0,1]$, used as a normalizer.)

### Interpretation

- $\mathrm{CDC} \to 1$: behavior is highly consistent across domains; the agent is indifferent to the value carrier;
- $\mathrm{CDC} \to 0$: behavior varies sharply across value carriers.

CDC is direction-agnostic (neither high nor low is "correct") — it characterizes whether the agent has a **domain-differentiated value structure**.

---

## 7. Response Determinism (RD)

Applicable to LLMs whose $r_i$ is estimated from repeated sampling. Treat each item's responses as Bernoulli$(r_i)$ and compute its entropy:

$$
H_i = -r_i \log_2 r_i - (1 - r_i) \log_2 (1 - r_i)
$$

$$
\mathrm{RD} = 1 - \frac{1}{|\mathcal{Q}|} \sum_{i \in \mathcal{Q}} H_i \in [0, 1]
$$

where $\mathcal{Q}$ is the set of all items in the questionnaire.

### Interpretation

- $\mathrm{RD} \to 1$: the model is near-deterministic per item, lacking the population-level variability seen in human samples;
- $\mathrm{RD} \to 0$: responses are maximally stochastic;
- The RD of the human sample can be computed directly from the questionnaire's `distribution` field and used as a reference.

RD also acts as a **quality gate** for the other metrics: when RD is close to 1, FES / MS / KG estimated from small samples have high variance and should be interpreted with care.

---

## 8. Reporting

For each agent, emit a 7-dimensional behavioral profile:

| Dimension | Typical human range | Meaning |
|-----------|---------------------|---------|
| FES       | $> 0$, ~0.2–0.4     | Framing effect magnitude |
| RC        | High, ~0.5–0.8      | Reflection consistency |
| MS (life) | $< 0$               | Scope sensitivity on lives |
| KG        | $\gtrsim 0$         | Kinship gradient |
| IGB       | $\lesssim 0$        | More conservative toward humans than aliens |
| CDC       | Moderate            | Cross-domain coherence |
| RD        | Comparable to humans | Response determinism |

Each dimension is computed independently on the LLM and on the human sample, enabling direct radar-chart comparison. The BTMs complement the BAS / FAS / PAS scores in [rating.md](rating.md): BTMs describe **what the agent is like**, while BAS / FAS describe **how close it is to humans**.
