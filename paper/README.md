# 论文草稿与复现材料

本文题为《像人一样决策：大语言模型的有限理性图灵测试》，以经典社会心理学
范式介绍“类人决策评测工具”，并用国产模型示例说明初步发现。研究围绕
当前模型与人类决策偏好的异同展开，并说明如何组织后续版本比较；现有
横截面配置结果不构成模型发展趋势的证据。

`paper.docx` 为中文匿名稿，按《心理学报》投稿指南编排，包含中文摘要、
正文、21条参考文献、四段英文摘要及完整材料附录。
`self_check.docx` 单独保存论文自检报告及待作者确认的批注。
正文源为 `manuscript.md`，英文摘要源为 `english_abstract.txt`。

## 版本控制

本目录的 `.gitignore` 仅保留写作源文件、构建脚本、文献核验记录和
`references/` 中的参考输入材料。Word文档、`figures/` 中的全部生成物、
`data_audit.json`、`review_verification.json` 及预览文件不加入版本控制。
参考PDF是输入资料，因此保留；生成图表中的PDF、SVG和CSV均由脚本重建。

## 图表原文件

`figures/` 保存四幅图的可编辑SVG、矢量PDF、600 dpi PNG和精确CSV数据。
`figure_manifest.json` 记录图号、图注、数据来源、有效分母和区间方法。
正文及附录中的三线表为可编辑Word表格，数据来自 `data_audit.json`。

## 离线复算

在项目根目录依次执行以下命令；不会发起新的模型请求。

```bash
uv run python -B paper/audit_data.py
uv run --with matplotlib==3.10.7 --with PyYAML==6.0.3 python paper/create_figures.py
uv run --with python-docx==1.2.0 --with PyYAML==6.0.3 python paper/build_paper.py
```

最后一条命令同时生成 `paper.docx` 和 `self_check.docx`，两份文件独立编号。
离线复算仍需本地保存项目实验结果；忽略生成物不会把实验输入自动纳入Git。

绘图脚本当前使用macOS的宋体与Times New Roman字体文件；其他系统需调整
`FONT_ROOT`及对应字库。文献核验记录见 `references_verified.json`，其中保留
了作为核验或写作参考、但未纳入正文参考文献表的条目。

## 投稿前需由作者完成的事项

- 人类基线逐题原文对应证据、伦理审批或豁免及题项授权信息由合作者补充；
  稿件对应字段留空，具体待办见 [todo.md](todo.md)。
- 确认同数据投稿发表情况、原始数据提供方式、预注册、专业英文校阅，
  以及适用时的导师邮件与单位不涉密证明。独立自检报告已填写可核验事项，
  其余事项附有作者确认批注。
- 对正文与参考文献作最终学术审校，核对并确认AI使用披露。

本稿保留存档评分便于复核，同时说明决策前提VAS的实际定义、当前自我年龄
操纵未落实、选择程序未明示随机、跨文件加权及辅助模型格式修复等限制。
这些问题涉及测量解释，不能通过排版或补充免责声明消除；如拟将相关指标
作为心理构念或机制证据，应修正设计并开展新的验证。

期刊要求核对来源：
[投稿指南](https://journal.psych.ac.cn/xlxb/CN/column/column6.shtml)；
[当前论文自检报告](https://journal.psych.ac.cn/xlxb/CN/item/downloadFile.jsp?filedisplay=20260903180114.doc)。

2026-10-26审校及2026-10-27全文修订记录见 `review_report.md`，独立数值核对
结果与当前文件检查见 `review_verification.json`，文献核验范围见
`reference_review.json`。本次新增职业写作、客户服务及行为图灵测试三篇引文，
分别支持应用背景和行为比较思路；既有来源的核验范围仍按历史记录保留。
材料表中发现的五篇来源文献已补入参考文献，但尚未完成原文逐题对照。

Word预览时须确认渲染器能够加载中文字体；若出现中文空白而英文正常，
应为渲染器配置宋体字库并重新检查，不能据此判断正文已通过版式校验。
最终页数随正文修订更新；英文摘要及关键词应位于同一页。
