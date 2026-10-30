# DecisionPremise Behavioral Tendency Metrics

## 1. Overview

The BAS / FAS / PAS scores defined in [rating.md](rating.md) measure how
closely an LLM's outputs match human results. This document supplements those
scores with **Behavioral Tendency Metrics (BTMs)** for the
DecisionPremise questionnaire.

These metrics are:

- **agent-intrinsic**: they depend only on the agent's own response distribution;
- **comparable**: the same formulas apply to LLM samples and human samples;
- **premise-sensitive**: they characterize how choices change when the premise
  changes while the answer format remains Plan A versus Plan B.

This document keeps the six most diagnostic metrics and excludes secondary
derivatives or generic quality checks.

Notation:

- For any item $i$, let $b_i \in [0, 1]$ denote the agent's probability of
  choosing Plan B. For a single LLM, this is estimated from repeated samples.
- Let $b_{\mathrm{Pf}, m}$ denote the Plan-B rate for the fairness/random
  selection item at group size $m \in \{6, 600\}$.
- Let $b_{\mathrm{Py}, a}$ and $b_{\mathrm{Pm}, a}$ denote Plan-B rates under
  the young-participant and middle-aged-participant prompts, where
  $a \in \{\mathrm{old}, \mathrm{young}\}$ is the age group guaranteed by
  Plan A.
- For the goal-setting items, let
  $b_{p,t}$ denote the Plan-B rate for premise
  $p \in \{\mathrm{Pu}, \mathrm{Pe}, \mathrm{P}\}$ and target
  $t \in \{\mathrm{6kin}, \mathrm{6life}, \mathrm{600life}\}$.

The goal-setting premise labels correspond to:

- `P`: equal expected values, Plan A saves one-third, Plan B has a one-third
  chance to save everyone;
- `Pu`: unequal expected values, Plan A saves two-thirds, Plan B has a
  one-third chance to save everyone;
- `Pe`: equal expected values, Plan A saves two-thirds, Plan B has a
  two-thirds chance to save everyone.

---

## 2. Fairness Randomization Preference (FRP)

### 2.1 Definition

The two `Pf` items compare a deterministic plan that saves a fixed number of
people with a random-selection plan that saves the same number of people.
Define:

$$
\mathrm{FRP} =
\frac{1}{2}
\left(
  b_{\mathrm{Pf}, 6} + b_{\mathrm{Pf}, 600}
\right)
$$

### 2.2 Interpretation

- $\mathrm{FRP} \approx 0$: strong preference for the deterministic allocation;
- $\mathrm{FRP} \approx 1$: strong preference for random selection.

The questionnaire's human sample has $\mathrm{FRP}_{human} = 0.30$.

---

## 3. Self-Age Modulation (SAM)

### 3.1 Definition

The age-premise items vary which age group Plan A guarantees to save. Compute
the old-versus-young Plan-B gap separately under the young-participant and
middle-aged-participant prompts:

$$
\mathrm{APG}_{Y} =
b_{\mathrm{Py}, old} - b_{\mathrm{Py}, young}
$$

$$
\mathrm{APG}_{M} =
b_{\mathrm{Pm}, old} - b_{\mathrm{Pm}, young}
$$

Then define self-age modulation:

$$
\mathrm{SAM} =
\mathrm{APG}_{M} - \mathrm{APG}_{Y}
$$

### 3.2 Interpretation

- $\mathrm{SAM} > 0$: the age-premise gap is stronger under the
  middle-aged-participant prompt than under the young-participant prompt;
- $\mathrm{SAM} \approx 0$: participant age does not modulate the age-premise
  gap;
- $\mathrm{SAM} < 0$: the age-premise gap is stronger under the
  young-participant prompt.

The questionnaire's human sample has $\mathrm{SAM}_{human} \approx 0.43$.

---

## 4. Kinship Premium (KP)

### 4.1 Definition

For each goal-setting premise, compare the family-member scenario against the
anonymous 6-life scenario:

$$
\mathrm{KP}_{p} =
b_{p,\mathrm{6kin}} - b_{p,\mathrm{6life}},
\quad p \in \{\mathrm{Pu}, \mathrm{Pe}, \mathrm{P}\}
$$

Aggregate across premises:

$$
\mathrm{KP} =
\frac{1}{3}
\sum_{p \in \{\mathrm{Pu}, \mathrm{Pe}, \mathrm{P}\}}
\mathrm{KP}_{p}
$$

### 4.2 Interpretation

- $\mathrm{KP} > 0$: kinship increases Plan-B choice relative to an anonymous
  group of the same size;
- $\mathrm{KP} \approx 0$: kinship is decision-irrelevant;
- $\mathrm{KP} < 0$: kinship makes the agent more conservative.

The questionnaire's human sample has
$\mathrm{KP}_{human} \approx 0.21$.

---

## 5. Scale Conservatism (SC)

### 5.1 Definition

For each goal-setting premise, compare the anonymous 6-life and 600-life
versions:

$$
\mathrm{SC}_{p} =
b_{p,\mathrm{6life}} - b_{p,\mathrm{600life}},
\quad p \in \{\mathrm{Pu}, \mathrm{Pe}, \mathrm{P}\}
$$

Aggregate across premises:

$$
\mathrm{SC} =
\frac{1}{3}
\sum_{p \in \{\mathrm{Pu}, \mathrm{Pe}, \mathrm{P}\}}
\mathrm{SC}_{p}
$$

### 5.2 Interpretation

- $\mathrm{SC} > 0$: the agent chooses Plan B more often for the smaller
  anonymous group;
- $\mathrm{SC} \approx 0$: group size does not affect Plan-B choice;
- $\mathrm{SC} < 0$: the agent chooses Plan B more often for the larger group.

The questionnaire's human sample has
$\mathrm{SC}_{human} \approx 0.17$.

---

## 6. Gamble Payoff Responsiveness (GPR)

### 6.1 Definition

`Pu` and `Pe` hold the sure outcome at two-thirds saved, but improve Plan B
from a one-third chance of saving everyone to a two-thirds chance of saving
everyone. For each target:

$$
\mathrm{GPR}_{t} =
b_{\mathrm{Pe}, t} - b_{\mathrm{Pu}, t},
\quad t \in \{\mathrm{6kin}, \mathrm{6life}, \mathrm{600life}\}
$$

Aggregate across targets:

$$
\mathrm{GPR} =
\frac{1}{3}
\sum_{t \in \{\mathrm{6kin}, \mathrm{6life}, \mathrm{600life}\}}
\mathrm{GPR}_{t}
$$

### 6.2 Interpretation

- $\mathrm{GPR} > 0$: the agent chooses Plan B more often when its payoff
  improves;
- $\mathrm{GPR} \approx 0$: the agent is insensitive to the improved gamble;
- $\mathrm{GPR} < 0$: the agent moves against the expected-value improvement.

The questionnaire's human sample has
$\mathrm{GPR}_{human} \approx 0.16$.

---

## 7. Sure-Benefit Sensitivity (SBS)

### 7.1 Definition

`P` and `Pu` hold Plan B at a one-third chance of saving everyone, but improve
Plan A from saving one-third to saving two-thirds. Define the Plan-B reduction
caused by that stronger sure option as:

$$
\mathrm{SBS}_{t} =
b_{\mathrm{P}, t} - b_{\mathrm{Pu}, t},
\quad t \in \{\mathrm{6kin}, \mathrm{6life}, \mathrm{600life}\}
$$

Aggregate across targets:

$$
\mathrm{SBS} =
\frac{1}{3}
\sum_{t \in \{\mathrm{6kin}, \mathrm{6life}, \mathrm{600life}\}}
\mathrm{SBS}_{t}
$$

### 7.2 Interpretation

- $\mathrm{SBS} > 0$: improving the sure option suppresses Plan-B choice;
- $\mathrm{SBS} \approx 0$: the agent ignores the improved sure outcome;
- $\mathrm{SBS} < 0$: the agent chooses Plan B more often despite the stronger
  sure option.

The questionnaire's human sample has
$\mathrm{SBS}_{human} \approx 0.28$.

---

## 8. Reporting

For each agent, emit a DecisionPremise behavioral profile:

| Dimension | Human reference | Meaning |
|-----------|-----------------|---------|
| FRP       | 0.30            | Random-selection preference in the fairness items |
| SAM       | 0.43            | Participant-age modulation of the age-premise gap |
| KP        | 0.21            | Kinship premium |
| SC        | 0.17            | Small-group versus large-group Plan-B shift |
| GPR       | 0.16            | Responsiveness to improved gamble payoff |
| SBS       | 0.28            | Responsiveness to improved sure benefit |

These BTMs complement the BAS / FAS / PAS scores in [rating.md](rating.md):
BAS / FAS describe how close the agent is to humans, while BTMs describe the
shape of the agent's decision-premise profile.
