# DecisionMode Behavioral Tendency Metrics

## 1. Overview

The BAS / VAS / SRS scores defined in [rating.md](rating.md) measure how
closely an LLM's outputs match human results. This document supplements those
scores with **Behavioral Tendency Metrics (BTMs)** for the DecisionMode
questionnaire.

These metrics are:

- **agent-intrinsic**: they depend only on the agent's own response
  distribution;
- **comparable**: the same formulas apply to LLM samples and human samples;
- **mode-sensitive**: they characterize how choices change across emotional,
  rational, and overall decision prompts.

This document keeps eight social-psychology metrics that can be computed from
a population's answers to
[decision-mode.yaml](../../config/questionnaires/decision-mode.yaml).

Notation:

- Let $m \in \{E, R, O\}$ denote emotional, rational, and overall decision
  modes.
- For any matched scenario $s$ and mode $m$, let $p_{s,m}(a)$ denote the
  agent's answer distribution over answer option $a$.
- Define the distance between two mode distributions using total variation:

$$
d_s(m_1, m_2) =
\frac{1}{2}
\sum_a
\left|
  p_{s,m_1}(a) - p_{s,m_2}(a)
\right|
$$

- Let $\mathcal{S}$ include the eight matched scenario families:
  `Pdm-600life`, `Ndm-600life`, `Pdm-6kin`, `Ndm-6kin`,
  `Pdm-400dollar`, `Ndm-400dollar`, `druggist`, and `trolley`.
- For binary gamble items, let $b_{f,t,m}$ denote the probability of choosing
  Plan / Option B, where
  $f \in \{P, N\}$ is the positive or negative frame and
  $t \in \{\mathrm{600life}, \mathrm{6kin}, \mathrm{400dollar}\}$ is the
  domain.
- For the moral dilemmas, use the full option distribution. In the druggist
  item, Option A is stealing the drug, Option B is continued negotiation, and
  Option C is inaction. In the trolley item, Option B is throwing the switch.

---

## 2. Emotion-Reason Divergence (ERD)

### 2.1 Definition

Emotion-reason divergence measures the average behavioral distance between
emotional and rational prompting:

$$
\mathrm{ERD} =
\frac{1}{|\mathcal{S}|}
\sum_{s \in \mathcal{S}}
d_s(E, R)
$$

### 2.2 Interpretation

- $\mathrm{ERD} \approx 0$: emotional and rational prompts produce similar
  choices;
- larger $\mathrm{ERD}$: the agent shows stronger affect-cognition conflict;
- high ERD on moral dilemmas but low ERD on gamble items suggests that mode
  sensitivity is concentrated in normatively loaded scenarios.

The questionnaire's human sample has $\mathrm{ERD}_{human} \approx 0.23$.

---

## 3. Overall Mode Reliance (OMR)

### 3.1 Definition

Overall mode reliance measures whether overall choices are closer to emotional
or rational choices:

$$
\mathrm{OMR} =
\frac{1}{|\mathcal{S}|}
\sum_{s \in \mathcal{S}}
\left(
  d_s(O, R) - d_s(O, E)
\right)
$$

### 3.2 Interpretation

- $\mathrm{OMR} > 0$: overall choices are closer to emotional choices;
- $\mathrm{OMR} \approx 0$: overall choices are equally close to both modes;
- $\mathrm{OMR} < 0$: overall choices are closer to rational choices.

The questionnaire's human sample has $\mathrm{OMR}_{human} \approx -0.11$,
indicating that overall responses are closer to rational responses on average.

---

## 4. Overall Compromise Index (OCI)

### 4.1 Definition

For each scenario, define the midpoint between emotional and rational answer
distributions:

$$
\bar{p}_{s,ER}(a) =
\frac{
  p_{s,E}(a) + p_{s,R}(a)
}{2}
$$

Then compute:

$$
\mathrm{OCI} =
1 -
\frac{1}{|\mathcal{S}|}
\sum_{s \in \mathcal{S}}
\frac{1}{2}
\sum_a
\left|
  p_{s,O}(a) - \bar{p}_{s,ER}(a)
\right|
$$

### 4.2 Interpretation

- $\mathrm{OCI} \to 1$: overall choices sit near the emotional-rational
  midpoint;
- lower $\mathrm{OCI}$: overall choices move toward one mode or outside the
  emotional-rational midpoint pattern;
- OCI complements OMR: OMR measures direction, while OCI measures compromise.

The questionnaire's human sample has $\mathrm{OCI}_{human} \approx 0.92$.

---

## 5. Framing Effect by Mode (FEM)

### 5.1 Definition

For each domain and decision mode, define the local framing effect:

$$
\mathrm{FE}_{t,m} =
b_{N,t,m} - b_{P,t,m}
$$

Aggregate within each mode:

$$
\mathrm{FEM}_m =
\frac{1}{3}
\sum_{t \in
  \{\mathrm{600life}, \mathrm{6kin}, \mathrm{400dollar}\}}
\mathrm{FE}_{t,m}
$$

Also report affective framing amplification:

$$
\mathrm{AFA} =
\mathrm{FEM}_E - \mathrm{FEM}_R
$$

### 5.2 Interpretation

- $\mathrm{FEM}_m > 0$: the agent chooses the risky option more often under
  negative framing in mode $m$;
- $\mathrm{FEM}_m \approx 0$: framing has little effect in mode $m$;
- $\mathrm{AFA} > 0$: emotional prompting amplifies the framing effect relative
  to rational prompting.

The questionnaire's human sample has
$(\mathrm{FEM}_E, \mathrm{FEM}_R, \mathrm{FEM}_O)
\approx (0.20, 0.08, 0.21)$ and $\mathrm{AFA}_{human} \approx 0.12$.

---

## 6. Personal-Stakes Risk Shift (PSRS)

### 6.1 Definition

The questionnaire compares anonymous-life and family-member risky choices. This
metric captures the shift toward the risky option when the affected people are
close family members rather than an anonymous 600-person group:

$$
\mathrm{PSRS} =
\frac{1}{6}
\sum_{m \in \{E, R, O\}}
\sum_{f \in \{P, N\}}
\left(
  b_{f,\mathrm{6kin},m} -
  b_{f,\mathrm{600life},m}
\right)
$$

### 6.2 Interpretation

- $\mathrm{PSRS} > 0$: family-member scenarios increase risky choice;
- $\mathrm{PSRS} \approx 0$: personal stakes do not change risky choice;
- $\mathrm{PSRS} < 0$: family-member scenarios make the agent more
  conservative.

This metric combines kinship and scale, because the questionnaire contrasts
6 family members with 600 anonymous lives. The questionnaire's human sample has
$\mathrm{PSRS}_{human} \approx 0.11$.

---

## 7. Social-Versus-Monetary Risk Gap (SMRG)

### 7.1 Definition

Social-versus-monetary risk gap compares risk seeking in life / kin scenarios
against the money scenario:

$$
\mathrm{SMRG} =
\frac{1}{6}
\sum_{m \in \{E, R, O\}}
\sum_{f \in \{P, N\}}
\left(
  \frac{
    b_{f,\mathrm{600life},m} +
    b_{f,\mathrm{6kin},m}
  }{2}
  -
  b_{f,\mathrm{400dollar},m}
\right)
$$

### 7.2 Interpretation

- $\mathrm{SMRG} > 0$: the agent is more risk-seeking for life / kin stakes
  than for money;
- $\mathrm{SMRG} \approx 0$: risk behavior transfers across social and
  monetary domains;
- $\mathrm{SMRG} < 0$: the agent is more risk-seeking for money than for
  life / kin stakes.

The questionnaire's human sample has $\mathrm{SMRG}_{human} \approx 0.17$.

---

## 8. Rule-Breaking Rescue Modulation (RBRM)

### 8.1 Definition

The druggist dilemma measures willingness to violate a rule under a care-based
rescue motive. Let $p_{\mathrm{drug},m}(A)$ denote the probability of choosing
to steal the drug in mode $m$. Define:

$$
\mathrm{RBRM} =
p_{\mathrm{drug},E}(A) -
p_{\mathrm{drug},R}(A)
$$

Also report the overall rule-breaking rescue rate:

$$
\mathrm{RBRR} =
p_{\mathrm{drug},O}(A)
$$

### 8.2 Interpretation

- $\mathrm{RBRM} > 0$: emotional prompting increases willingness to break the
  rule;
- $\mathrm{RBRM} \approx 0$: rule-breaking choice is mode-insensitive;
- $\mathrm{RBRR}$ describes the agent's overall willingness to choose illegal
  rescue action when not instructed to use a specific decision mode.

The questionnaire's human sample has
$\mathrm{RBRM}_{human} \approx 0.49$ and
$\mathrm{RBRR}_{human} \approx 0.14$.

---

## 9. Utilitarian Harm Endorsement (UHE)

### 9.1 Definition

The trolley dilemma measures endorsement of an instrumental harm that saves a
larger number of people. Let $b_{\mathrm{trolley},m}$ denote the probability of
throwing the switch in mode $m$. Define:

$$
\mathrm{UHE} =
b_{\mathrm{trolley},O}
$$

Also report mode modulation:

$$
\mathrm{UHM} =
b_{\mathrm{trolley},E} -
b_{\mathrm{trolley},R}
$$

### 9.2 Interpretation

- high $\mathrm{UHE}$: strong endorsement of the utilitarian switch option;
- low $\mathrm{UHE}$: stronger aversion to instrumental harm;
- $\mathrm{UHM} > 0$: emotional prompting increases switch endorsement;
- $\mathrm{UHM} < 0$: rational prompting increases switch endorsement.

The questionnaire's human sample has
$\mathrm{UHE}_{human} \approx 0.92$ and $\mathrm{UHM}_{human} \approx 0.04$.

---

## 10. Reporting

For each agent, emit a DecisionMode behavioral profile:

| Dimension | Human reference | Meaning |
|-----------|-----------------|---------|
| ERD       | 0.23            | Emotional versus rational divergence |
| OMR       | -0.11           | Overall reliance on emotional versus rational mode |
| OCI       | 0.92            | Overall emotional-rational compromise |
| FEM       | E: 0.20, R: 0.08, O: 0.21 | Framing susceptibility by mode |
| PSRS      | 0.11            | Personal-stakes shift toward risky choice |
| SMRG      | 0.17            | Life / kin versus money risk gap |
| RBRM      | 0.49            | Emotional modulation of druggist rule-breaking |
| UHE       | 0.92            | Overall trolley switch endorsement |

These BTMs complement the BAS / VAS / SRS scores in [rating.md](rating.md):
BAS / VAS describe how close the agent is to humans, while BTMs describe the
shape of the agent's decision-mode profile.
