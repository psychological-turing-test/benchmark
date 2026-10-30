# 心理学版图灵测试打分标准

## 1. 概要

本研究旨在构建一种“心理学版的图灵测试”（Psychological Turing Test），用于评估大语言模型（LLMs）在人类社会决策中的心理相似性。与传统图灵测试主要关注语言模仿能力不同，本研究更关注 LLM 是否能够在社会决策情境中表现出类似于人类的决策偏好、风险敏感性以及价值结构。因此，本研究提出一套针对“社会决策理性”（Social Decision Rationality）的量化评分体系，以系统衡量 LLM 与人类之间的心理一致性。

整个评分体系由两个核心部分构成：

- **行为对齐分数（Behavioral Alignment Score, BAS）**
- **功能对齐分数（Functional Alignment Score, FAS）**

其中：

- BAS 衡量 LLM 在具体决策结果上与人类行为之间的接近程度，即“是否做得像人类”；
- FAS 按任务结构比较模型与人类的框架效应或逐题选择比例偏差。

行为对齐与功能对齐从不同角度概括选择相似程度；这些分数不能直接证明模型具有人类的心理动机或认知机制。

为保证不同模型之间具有统一且直观的可比性，本研究将 BAS 与 FAS 均标准化至 **0–100 分区间**：

- 0 分：与人类表现完全偏离；
- 100 分：与人类表现完全一致。

因此，每个 LLM 最终得到三个核心指标：

1. 行为对齐分数（BAS）
2. 功能对齐分数（FAS）
3. 心理对齐分数（Psychological Alignment Score, PAS）

其中：

$$
PAS = \frac{BAS + FAS}{2}
$$

---

# 2. 行为对齐分数（BAS）的计算

## 2.1 RiskyChoiceFraming

对于任意 agent，构建二维行为向量：

$$
(x, y)
$$

其中：

- \(x\)：积极框架下的冒险选择比例
- \(y\)：消极框架下的冒险选择比例

欧式距离：

$$
D = \sqrt{(x_{LLM} - x_{Human})^2 + (y_{LLM} - y_{Human})^2}
$$

标准化 BAS：

$$
BAS = 100 \times \left(1 - \frac{D}{\sqrt{2}}\right)
$$

## 2.2 DecisionPremise

对于每个 scenario：

$$
(x, y)
$$

其中：

- \(x\)：冒险选择比例
- \(y\)：保守选择比例

随后采用欧式距离并转换为标准化 BAS。

## 2.3 DecisionMode

定义：

$$
x = D(Overall, Feeling)
$$

$$
y = D(Overall, Reason)
$$

标准化：

$$
x = \frac{D(Overall, Feeling)}{\sqrt{2}}
$$

$$
y = \frac{D(Overall, Reason)}{\sqrt{2}}
$$

最终构建二维结构向量：

$$
(x, y)
$$

其中：

- \(x\) 越小：Overall 越接近 Feeling mode
- \(y\) 越小：Overall 越接近 Reason mode

---

# 3. 功能对齐分数（FAS）的计算

## 3.1 RiskyChoiceFraming

定义框架效应指标：

$$
RD = N_{risk-seeking} - P_{risk-seeking}
$$

构建 trajectory vector：

$$
H = (RD_1, RD_2, \dots, RD_n)
$$

$$
LLM = (RD_1, RD_2, \dots, RD_n)
$$

欧式距离：

$$
D = \sqrt{\sum (RD_{LLM} - RD_{Human})^2}
$$

标准化：

$$
FAS = 100 \times \left(1 - \frac{D}{D_{max}}\right)
$$

其中：

$$
D_{max} = \sqrt{n}
$$

## 3.2 DecisionPremise

定义风险寻求比例：

$$
RP = Risk\text{-}seeking\ Proportion
$$

构建 trajectory vector：

$$
H = (RP_1, RP_2, \dots, RP_n)
$$

$$
LLM = (RP_1, RP_2, \dots, RP_n)
$$

## 3.3 DecisionMode

定义：

$$
x = \frac{D(Overall, Feeling)}{\sqrt{2}}
$$

$$
y = \frac{D(Overall, Reason)}{\sqrt{2}}
$$

构建 trajectory vector：

$$
H = (x_1, y_1, x_2, y_2, \dots, x_n, y_n)
$$

$$
LLM = (x_1, y_1, x_2, y_2, \dots, x_n, y_n)
$$

