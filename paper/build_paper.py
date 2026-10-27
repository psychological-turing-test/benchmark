"""Build separate manuscript and self-check documents.

Use the Codex bundled Python, with matplotlib and PyYAML available on PYTHONPATH.
Run create_figures.py first. Render both DOCX files with the documents renderer.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml
from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

PAPER = Path(__file__).resolve().parent
ROOT = PAPER.parent
SONG = "Songti SC"
HEI = "Heiti SC"
LATIN = "Times New Roman"
DATA = json.loads((PAPER / "data_audit.json").read_text())
REFS = json.loads((PAPER / "references_verified.json").read_text())
DOC = Document()
EQUATION_NUMBER = 0


def set_font(run: Any, size: float | None = None, bold: bool = False,
             italic: bool = False, east_asia: str = SONG) -> None:
  """Apply journal fonts without inherited theme colors."""
  run.font.name = LATIN
  run.font.color.rgb = RGBColor(0, 0, 0)
  run.font.bold = bold
  run.font.italic = italic
  if size is not None:
    run.font.size = Pt(size)
  fonts = run._element.get_or_add_rPr().get_or_add_rFonts()
  for key, value in (("ascii", LATIN), ("hAnsi", LATIN), ("eastAsia", east_asia)):
    fonts.set(qn(f"w:{key}"), value)
  for key in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme"):
    fonts.attrib.pop(qn(f"w:{key}"), None)


def add_text(paragraph: Any, text: str, size: float | None = None,
             bold: bool = False) -> None:
  """Add prose, preserving statistical symbol conventions."""
  if paragraph.style.name == "References":
    set_font(paragraph.add_run(text), size, bold)
    return
  cjk = HEI if paragraph.style.name in ("Title", "Heading 2", "Heading 3") else SONG
  bold = bold or bool(paragraph.style.font.bold)
  for chunk in re.split(r"(?<![A-Za-z])(pL|pH|SD|N|n|M|p)(?![A-Za-z])", text):
    if not chunk:
      continue
    if chunk in ("pL", "pH"):
      math = OxmlElement("m:oMath")
      math.append(sub(mr("p"), mr(chunk[1], plain=True)))
      paragraph._p.append(math)
    else:
      run = paragraph.add_run(chunk)
      set_font(run, size, bold, chunk in ("SD", "N", "n", "M", "p"), cjk)


def para(text: str, style: str = "Normal", indent: bool = True) -> Any:
  """Add a manuscript paragraph."""
  p = DOC.add_paragraph(style=style)
  if not indent:
    p.paragraph_format.first_line_indent = Pt(0)
  add_text(p, text)
  return p


def heading(text: str, level: int = 1, page_break: bool = False) -> Any:
  """Add a numbered section heading."""
  p = DOC.add_paragraph(style=f"Heading {level}")
  p.paragraph_format.page_break_before = page_break
  add_text(p, text)
  return p


def configure_styles() -> None:
  """Configure an anonymous single-column journal submission."""
  for border in list(DOC.styles.element.xpath(".//w:pBdr")):
    border.getparent().remove(border)
  sec = DOC.sections[0]
  sec.page_width, sec.page_height = Inches(8.5), Inches(11)
  sec.top_margin = sec.bottom_margin = Cm(2.25)
  sec.left_margin = sec.right_margin = Cm(2.54)
  sec.header_distance = sec.footer_distance = Cm(1.0)
  for name, size, cjk in (
    ("Normal", 10.5, SONG), ("Title", 22, HEI),
    ("Heading 1", 14, SONG), ("Heading 2", 10.5, HEI),
    ("Heading 3", 10.5, HEI), ("Caption", 9, SONG),
  ):
    style = DOC.styles[name]
    style.font.name = LATIN
    style.font.size = Pt(size)
    style.font.color.rgb = RGBColor(0, 0, 0)
    style.font.bold = name in ("Heading 2", "Heading 3")
    rpr = style.element.get_or_add_rPr()
    fonts = rpr.get_or_add_rFonts()
    for key, value in (("ascii", LATIN), ("hAnsi", LATIN), ("eastAsia", cjk)):
      fonts.set(qn(f"w:{key}"), value)
    for key in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme"):
      fonts.attrib.pop(qn(f"w:{key}"), None)
    pf = style.paragraph_format
    pf.line_spacing = 1.5
    pf.space_after = Pt(0)
    pf.space_before = Pt(0)
    pf.widow_control = True
    if name == "Normal":
      pf.first_line_indent = Pt(21)
      pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    elif name.startswith("Heading"):
      pf.first_line_indent = Pt(0)
      pf.space_before, pf.space_after = Pt(9), Pt(3)
      pf.keep_with_next = True
    else:
      pf.first_line_indent = Pt(0)
  DOC.styles["Title"].paragraph_format.space_after = Pt(12)
  DOC.styles["Title"].paragraph_format.line_spacing = 1.15
  for name, size in (("References", 9), ("Appendix", 9), ("Code", 8.5),
                     ("Checklist", 10.5)):
    style = DOC.styles.add_style(name, 1)
    style.base_style = DOC.styles["Normal"]
    style.font.size = Pt(size)
    pf = style.paragraph_format
    pf.first_line_indent = Pt(0)
    if name == "References":
      pf.left_indent = Cm(0.74)
      pf.first_line_indent = Cm(-0.74)
      pf.space_after = Pt(4)
      pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    if name == "Appendix":
      pf.line_spacing = 1.5
      pf.space_after = Pt(4)
    if name == "Code":
      pf.line_spacing = 1.5
      pf.space_after = Pt(2)
      pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    if name == "Checklist":
      pf.space_after = Pt(5)
  footer = sec.footer.paragraphs[0]
  footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
  field = OxmlElement("w:fldSimple")
  field.set(qn("w:instr"), "PAGE")
  footer._p.append(field)
  for key in ("author", "last_modified_by", "comments", "identifier"):
    setattr(DOC.core_properties, key, "")
  DOC.core_properties.title = "像人一样决策：大语言模型的有限理性图灵测试"
  DOC.core_properties.subject = "有限理性图灵测试的工具教程与国产模型应用示例"
  DOC.core_properties.keywords = "大语言模型 有限理性 图灵测试 社会决策 行为评测"
  # Use native equation typography and prevent theme title borders.
  settings = DOC.settings.element
  mathpr = settings.find(qn("m:mathPr"))
  if mathpr is None:
    mathpr = OxmlElement("m:mathPr")
    settings.append(mathpr)
  mathfont = OxmlElement("m:mathFont")
  mathfont.set(qn("m:val"), "Cambria Math")
  mathpr.append(mathfont)


def self_check() -> None:
  """Populate all current journal checklist items without false attestations."""
  p = DOC.add_paragraph(style="Title")
  p.alignment = WD_ALIGN_PARAGRAPH.CENTER
  set_font(p.add_run("论文自检报告"), 16, east_asia=HEI)
  checks = [
    ("1 研究亮点", "围绕模型代行判断时的决策偏好，介绍有限理性图灵测试的配置、施测和分析流程；以国产模型示例呈现类人性的任务依赖，并说明后续版本比较的设计要求。"),
    ("2 同数据发表情况", "由作者核对既往投稿与发表记录后确认。"),
    ("3 生成式人工智能使用", "本稿的正文草拟、文献检索整理、数据核验代码、图表与Word排版使用了生成式人工智能辅助，参与程度较高。作者须完成最终学术审核并承担稿件责任。"),
    ("4 共同方法偏差", "本文为方法教程与既有模型输出的二次分析，不以横断自陈相关估计变量关系。人类参考分布及提示材料的偏差在讨论中说明。"),
    ("5 效应量与置信区间", "报告选择比例、配对差分、对齐评分和敏感性变化；图2报告边际比例的95% Wilson区间。未以模型间描述差异代替人群推论。"),
    ("6 计划与实际样本量", "原配置默认每模型50次施测；源文件每模型每题有效回答为41至100。51个题项、19个模型配置，源文件有效答案计数之和67,893。既有运行未建立本稿的事前功效计划。"),
    ("7 假设检验", "本稿采用描述统计、条件区间与事后敏感性分析，不报告零假设显著性检验或贝叶斯因子，亦不使用显著性措辞。"),
    ("8 完备性与排除", "存档分析保留全部51题；另移除四个未落实自我年龄操纵的题项重算。原始日志共有57个错误题目记录。跨文件汇总、格式修复与历史参数限制见正文及附录。"),
    ("9 材料与共享", "附录A列出两套问卷全部题干、通用指令、答案格式及逐题人类参照。题项使用许可及共享授权：________________。"),
    ("10 原始数据提供方式", "数据向编辑部提供或公开存储的选项、链接和授权范围由作者确认；本稿不勾选尚未实施的公开承诺。"),
    ("11 预注册", "本稿未新增临床干预或实验室招募；二次分析与敏感性检查属于事后分析。原始研究的预注册情况由作者核对。"),
    ("12 伦理审查", "本稿不新增人类或动物招募，使用既有人类汇总分布。原始人类研究的伦理批准或豁免及文件编号：________________；知情同意与二次使用依据：________________。"),
    ("13 英文摘要", "英文摘要按四段撰写，正文不包含结果统计数字。专业语言校阅须由作者安排并确认。"),
    ("14 学生作者与导师确认", "第一作者身份及适用时的导师邮件由作者确认。"),
    ("15 不涉密证明", "单位盖章证明及递交事项由作者办理并确认。"),
  ]
  comment_targets = {2, 9, 10, 11, 12, 13, 14, 15}
  for i, (label, text) in enumerate(checks, 1):
    p = DOC.add_paragraph(style="Checklist")
    add_text(p, label + "  ", bold=True)
    add_text(p, text)
    if i in comment_targets:
      comment = (
        "相关信息由合作者掌握，本字段按要求留空。补充事项见paper/todo.md。"
        if i in {9, 12} else
        "投稿前请据真实记录补充并确认本项。不得将未完成事项改写为已经完成；尤其请核实人类材料出处、授权及伦理文件。"
      )
      DOC.add_comment(
        p.runs,
        text=comment,
        author="作者核验", initials="",
      )


def mr(text: str, plain: bool = False) -> Any:
  """Construct a native Word math run."""
  node = OxmlElement("m:r")
  if plain:
    pr = OxmlElement("m:rPr")
    sty = OxmlElement("m:sty")
    sty.set(qn("m:val"), "p")
    pr.append(sty)
    node.append(pr)
  wt = OxmlElement("m:t")
  wt.text = text
  node.append(wt)
  return node


def group(tag: str, nodes: list[Any]) -> Any:
  node = OxmlElement(tag)
  for child in nodes:
    node.append(child)
  return node


def sub(base: Any, index: Any) -> Any:
  return group("m:sSub", [group("m:e", [base]), group("m:sub", [index])])


def power(nodes: list[Any], exponent: str = "2") -> Any:
  return group("m:sSup", [group("m:e", nodes), group("m:sup", [mr(exponent)])])


def fraction(num: list[Any], den: list[Any]) -> Any:
  return group("m:f", [group("m:num", num), group("m:den", den)])


def radical(nodes: list[Any]) -> Any:
  pr = OxmlElement("m:radPr")
  hide = OxmlElement("m:degHide")
  hide.set(qn("m:val"), "1")
  pr.append(hide)
  return group("m:rad", [pr, OxmlElement("m:deg"), group("m:e", nodes)])


def summation(index: str, upper: str, nodes: list[Any]) -> Any:
  pr = OxmlElement("m:naryPr")
  char = OxmlElement("m:chr")
  char.set(qn("m:val"), "∑")
  pr.append(char)
  return group("m:nary", [pr, group("m:sub", [mr(index)]),
                         group("m:sup", [mr(upper)]), group("m:e", nodes)])


def var(name: str, index: str) -> Any:
  return sub(mr(name, plain=name == "δ"), mr(index, True))


def error(index: str, frame: str = "") -> list[Any]:
  suffix = f",{frame}" if frame else ""
  return [var("p", f"L{suffix},{index}"), mr("−"),
          var("p", f"H{suffix},{index}")]


def equation(key: str) -> None:
  """Create native editable OMML, with a right aligned equation number."""
  global EQUATION_NUMBER
  EQUATION_NUMBER += 1
  if key == "bas_framing":
    inside = [mr("1−"), fraction(
      [radical([power([mr("(")] + error("j", "P") + [mr(")")]),
                mr("+"), power([mr("(")] + error("j", "N") + [mr(")")])])],
      [radical([mr("2")])])]
    nodes = [var("BAS", "F"), mr("="), fraction([mr("100")], [mr("J")]),
             summation("j=1", "J", [mr("[")] + inside + [mr("]")])]
  elif key == "bas_premise":
    nodes = [var("BAS", "D"), mr("=100[1−"),
             fraction([mr("1")], [mr("I")]),
             summation("i=1", "I", [mr("|")] + error("i") + [mr("|")]), mr("]")]
  elif key == "delta":
    nodes = [var("δ", "a,j"), mr("="), var("p", "a,N,j"), mr("−"),
             var("p", "a,P,j"), mr("     a∈{L,H}")]
  elif key == "vas_framing":
    diff = [var("δ", "L,j"), mr("−"), var("δ", "H,j")]
    nodes = [var("VAS", "F"), mr("=C(100[1−"), radical([
      fraction([mr("1")], [mr("J")]),
      summation("j=1", "J", [power([mr("(")] + diff + [mr(")")])])]), mr("])")]
  elif key == "vas_premise":
    nodes = [var("VAS", "D"), mr("=100[1−"), radical([
      fraction([mr("1")], [mr("I")]),
      summation("i=1", "I", [power([mr("(")] + error("i") + [mr(")")])])]), mr("]")]
  elif key == "srs":
    nodes = [var("SRS", "q"), mr("="),
             fraction([var("BAS", "q"), mr("+"), var("VAS", "q")], [mr("2")]),
             mr("   ;   SRS="), fraction(
               [var("SRS", "F"), mr("+"), var("SRS", "D")], [mr("2")])]
  else:
    raise ValueError(key)
  p = DOC.add_paragraph()
  pf = p.paragraph_format
  pf.first_line_indent = Pt(0)
  pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
  pf.space_before = pf.space_after = Pt(5)
  pf.keep_together = True
  math = group("m:oMath", nodes)
  p._p.append(math)
  set_font(p.add_run(f"    ({EQUATION_NUMBER})"), 10.5)


def three_line_table(headers: list[str], rows: list[list[str]],
                     widths: list[float], caption: str, note: str) -> None:
  """Use the journal's three-line tables, which supersede generic grid tables."""
  p = para(caption, "Caption", indent=False)
  p.paragraph_format.keep_with_next = True
  table = DOC.add_table(rows=1, cols=len(headers))
  table.alignment = WD_TABLE_ALIGNMENT.CENTER
  table.autofit = False
  props = table._tbl.tblPr
  borders = OxmlElement("w:tblBorders")
  for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
    node = OxmlElement(f"w:{edge}")
    node.set(qn("w:val"), "single" if edge in ("top", "bottom") else "nil")
    node.set(qn("w:sz"), "10")
    node.set(qn("w:color"), "000000")
    borders.append(node)
  props.append(borders)
  margins = OxmlElement("w:tblCellMar")
  for side in ("top", "bottom", "left", "right"):
    m = OxmlElement(f"w:{side}")
    m.set(qn("w:w"), "35" if side in ("top", "bottom") else "85")
    m.set(qn("w:type"), "dxa")
    margins.append(m)
  props.append(margins)
  for j, h in enumerate(headers):
    table.rows[0].cells[j].text = h
  for row in rows:
    for cell, text in zip(table.add_row().cells, row):
      cell.text = text
  for i, row in enumerate(table.rows):
    rowpr = row._tr.get_or_add_trPr()
    rowpr.append(OxmlElement("w:cantSplit"))
    if i == 0:
      rowpr.append(OxmlElement("w:tblHeader"))
    for j, cell in enumerate(row.cells):
      cell.width = Inches(widths[j])
      cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
      if i == 0:
        cb = OxmlElement("w:tcBorders")
        edge = OxmlElement("w:bottom")
        edge.set(qn("w:val"), "single")
        edge.set(qn("w:sz"), "6")
        cb.append(edge)
        cell._tc.get_or_add_tcPr().append(cb)
      for p in cell.paragraphs:
        p.paragraph_format.first_line_indent = Pt(0)
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.keep_with_next = i == 0 or i >= len(table.rows) - 2
        p.alignment = (WD_ALIGN_PARAGRAPH.LEFT if j == 0
                       else WD_ALIGN_PARAGRAPH.CENTER)
        for run in p.runs:
          set_font(run, 9, bold=i == 0)
  note_p = para(note, "Caption", indent=False)
  note_p.paragraph_format.keep_with_next = False
  note_p.paragraph_format.keep_together = True
  note_p.paragraph_format.space_after = Pt(5)


def table_by_name(key: str) -> None:
  if key == "tasks":
    three_line_table(
      ["比较维度", "风险决策框架", "决策前提"],
      [["题项数", "36题 18组配对", "15题 敏感性分析保留11题"],
       ["条件组织", "框架与对象 数量 价值载体", "程序 对象 数量 收益及名义年龄"],
       ["人类每题有效回答", "30至50", "30至50"],
       ["评分比较单位", "正负框架概率向量与差值", "B选择率的逐题误差"],
       ["关键解释限制", "框架VAS采用名义缩放与截断", "自身年龄未进入提示 程序题未明示随机"]],
      [1.42, 2.40, 2.58], "表1 两类任务的测量范围",
      "注：人类样本量为逐题记录；不同题项的被试是否重合不能由汇总数据判断。")
  elif key == "scores":
    rows = []
    for item in sorted(DATA["model_table"], key=lambda x: x["overall_srs_rank"]):
      name = short_name(item["llm_id"])
      q = item["questionnaires"]
      rows.append([name, f'{q["risky-choice-framing"]["srs"]:.2f}',
                   f'{q["decision-premise"]["srs"]:.2f}',
                   f'{item["overall"]["srs"]:.2f}'])
    three_line_table(
      ["模型配置", "框架SRS", "前提SRS", "总体SRS"], rows,
      [3.40, 1.00, 1.00, 1.00], "表2 存档规则下19个模型配置的评分",
      "注：按未四舍五入的总体SRS排序；两任务等权平均。思考与非思考仅在存档标识明确时标注，未标注配置的历史思考设置不作推定。分数无推论性名次区间。")
  else:
    raise ValueError(key)


def short_name(llm_id: str) -> str:
  name = llm_id.split("/", 1)[-1]
  return name.replace(" (-1)", " 思考").replace(" (0)", " 非思考")


def figure(key: str) -> None:
  """Insert a figure as one paragraph with its caption and interpretive note."""
  captions = {
    "workflow": ("图1 社会决策基准的执行与核查流程", "注：记录与核查贯穿施测、汇总和解释环节；配置中的条件名称须落实至模型实际可见的文本。"),
    "framing": ("图2 600人疾病题的框架选择分布", "注：点为B选择率，误差线为95% Wilson边际区间；各条件的有效n见图内标注。人类为项目参考数据，模型为各自单一来源文件的有效回答。区间以条件内独立二项采样为前提，不是框架差值或人机差值的置信区间。"),
    "profiles": ("图3 决策前提任务的行为画像", "注：灰点为19个模型配置，纵向错开仅为避免重叠；深色圆点为配置等权均值，空心菱形为人类参考。FRP为B选择比例，其余为条件差分；横轴单位均为概率或概率差，不表示同一心理构念。"),
    "sensitivity": ("图4 题项范围与汇总规则的敏感性", "注：DS为DeepSeek，Q为Qwen，T为思考、NT为非思考。A比较全部题项与移除四个未落实自我年龄操纵题项后的总体SRS，框架任务不变，两任务仍等权；B比较DeepSeek v4 pro思考配置的源文件等权与按有效计数合并结果。此为事后描述性检查，不能替代修正材料后的新实验。"),
  }
  p = DOC.add_paragraph()
  p.paragraph_format.first_line_indent = Pt(0)
  p.paragraph_format.space_before = Pt(6)
  p.paragraph_format.space_after = Pt(1)
  p.paragraph_format.line_spacing = 1.0
  p.paragraph_format.keep_with_next = True
  p.alignment = WD_ALIGN_PARAGRAPH.CENTER
  path = PAPER / "figures" / f"{key}.png"
  run = p.add_run()
  shape = run.add_picture(str(path), width=Inches(6.35))
  docpr = shape._inline.docPr
  docpr.set("descr", captions[key][0] + "。" + captions[key][1])
  cp = para(captions[key][0], "Caption", indent=False)
  cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
  cp.paragraph_format.keep_with_next = True
  np = para(captions[key][1], "Caption", indent=False)
  np.paragraph_format.space_after = Pt(6)


def author_string(authors: list[str]) -> str:
  if len(authors) == 1:
    return authors[0]
  if len(authors) > 20:
    return ", ".join(authors[:19]) + ", … " + authors[-1]
  return ", ".join(authors[:-1]) + ", & " + authors[-1]


def references() -> None:
  heading("参考文献", page_break=True)
  used = [r for r in REFS if r["id"] not in {"cohen1960", "cui2026", "glaser2026"}]
  for ref in sorted(used, key=lambda r: (
    tuple(a.lower() for a in r["authors"]), str(r["year"])
  )):
    p = DOC.add_paragraph(style="References")
    title = ref["title"].rstrip(".")
    ending = " " if title.endswith(("?", "!")) else ". "
    add_text(p, f'{author_string(ref["authors"])} ({ref["year"]}). {title}{ending}')
    if ref.get("editors"):
      editors = ref["editors"]
      if isinstance(editors, list):
        names = []
        for editor in editors:
          surname, initials = editor.rsplit(", ", 1)
          names.append(f"{initials} {surname}")
        editors = ", ".join(names[:-1]) + ", & " + names[-1]
      add_text(p, f"In {editors} (Eds.), ")
    run = p.add_run(ref["container"])
    set_font(run, italic=True)
    if ref.get("editors"):
      add_text(p, f' (Vol. {ref["volume"]}, pp. {ref["pages"]}).')
      if ref.get("publisher"):
        add_text(p, f' {ref["publisher"]}.')
      add_text(p, " " + ref["url"])
      continue
    if ref.get("volume"):
      add_text(p, ", ")
      run = p.add_run(str(ref["volume"]))
      set_font(run, italic=True)
    if ref.get("issue"):
      add_text(p, f'({ref["issue"]})')
    pages = ref.get("pages", "")
    if pages:
      add_text(p, f", {pages}.")
    else:
      add_text(p, ".")
    if ref.get("publisher"):
      add_text(p, f' {ref["publisher"]}.')
    add_text(p, " " + ref["url"])


def english_abstract() -> None:
  heading("Judging like humans: A tutorial on the bounded rationality Turing test for LLMs using classic social psychology paradigms",
          page_break=True)
  for block in (PAPER / "english_abstract.txt").read_text().strip().split("\n\n"):
    p = para(block.replace("\n", " "), indent=False)
    p.paragraph_format.space_after = Pt(0)
  para("Keywords: large language models; bounded rationality; Turing test; social decision making; behavioral assessment", indent=False)


def materials() -> None:
  heading("附录A 模型可见材料与人类参考分布", page_break=True)
  para("以下按当前问卷配置逐字列出两套任务的51道英文题干；原有措辞保留以便审核。各题的来源标识仅用于追踪，不作为模型可见的年龄提示。系统提示与作答指令在题项之间重复使用，故在此各列一次。人类参照列为逐题B比例与有效n，不表示独立参与者总数。", "Appendix")
  task_data = []
  for slug in ("risky-choice-framing", "decision-premise"):
    task_data.append(yaml.safe_load((ROOT / "config/questionnaires" / f"{slug}.yaml").read_text())["questionnaire"])
  common = task_data[0]
  para("通用系统提示", "Appendix", indent=False).runs[0].bold = True
  para(common["system_prompt"].strip().replace("\n", " "), "Appendix")
  para("通用作答指令", "Appendix", indent=False).runs[0].bold = True
  para(common["sections"][0]["instructions"].strip().replace("\n", " "), "Appendix")
  para('程序另附指令 Respond with JSON that matches this schema exactly 以及答案模式 {"type":"object","properties":{"answer":{"type":"string","enum":["A","B"]}},"required":["answer"],"additionalProperties":false}。选项A为Plan A，B为Plan B。下列题干本身包含两个方案的完整结果。', "Appendix")
  for task, label in zip(task_data, ("A1 风险决策框架任务", "A2 决策前提任务")):
    heading(label, 2)
    for sec in task["sections"]:
      for question in sec["questions"]:
        ph = question["scoring"]["distribution"]["B"]
        n = sec["human"]["population"]
        label = f'{question["id"]}  人类B比例 {ph:.4f}  n = {n}'
        p = para(label, "Appendix", indent=False)
        for run in p.runs:
          run.bold = True
        p.paragraph_format.keep_with_next = True
        text = question["prompt"].strip().replace("\n", " ")
        para(text, "Appendix", indent=False)


def metrics_appendix() -> None:
  heading("附录B 行为指标与可追溯统计", page_break=True)
  para("FES为18个配对中负框架减正框架B比例的平均值。RC为正框架比例小于0.50且负框架比例大于0.50的配对占比。MS为各框架内B比例对人数以10为底对数的最小二乘斜率，再在两框架取平均。KG对应亲属数1、2、3、6的斜率均值；IGB为人类主体条件减外星主体条件的B比例差，再在两框架平均。RD为1减各题二项选择熵的平均值，熵以2为底，零概率项按零处理。上述名称均是指标简称，不能独立证实心理构念。", "Appendix")
  para("决策前提任务中，Pf表示选择程序题；P表示A确定救三分之一、B以三分之一概率全部获救；Pu表示A确定救三分之二而B概率仍为三分之一；Pe表示A确定救三分之二且B以三分之二概率全部获救。FRP为两个Pf题的B比例平均。KP为同一收益条件下6名亲属减6名匿名者的B比例差，再跨P、Pu、Pe平均。SC为6名匿名者减600名匿名者的B比例差，再跨收益条件平均。GPR为Pe减Pu，SBS为P减Pu，均跨6名亲属、6名匿名者、600名匿名者平均。名义年龄指标SAM未作年龄效应实证解读。", "Appendix")
  ms = DATA["metric_summary"]
  rows = []
  for task, keys in (("risky-choice-framing", ["fes", "rc", "ms_life", "kg", "igb", "rd"]),
                     ("decision-premise", ["frp", "kp", "sc", "gpr", "sbs"])):
    for key in keys:
      v = ms[task][key]
      fmt = lambda x: f"{x:.3f}".replace("-", "–")
      rows.append([key.upper().replace("MS_LIFE", "MS生命"), fmt(v["human"]),
                   fmt(v["mean"]), f'{fmt(v["min"])} 至 {fmt(v["max"])}'])
  three_line_table(["指标", "人类参照", "模型均值", "模型配置范围"], rows,
                   [1.25, 1.25, 1.25, 2.65], "表B1 行为指标的描述统计",
                   "注：保留三位小数以呈现接近零的差分；范围为模型配置间极值，不是置信区间。模型均值不推定为随机抽样的总体均值。")
  para("图2以原始选项计数和有效n计算Wilson区间。置信水平为95%，正态分布分位数取1.9599639845；当计数为0或n时仍使用同一计算规则。该方法以条件内独立二项观测为前提。图3与图4不添加将模型配置误当独立抽样单元的误差线。图表计算保留完整精度，仅在展示时四舍五入。", "Appendix")
  para("原始运行目录中有2,500条施测记录和67,950个题目记录；计入汇总的有效回答67,893个，与57个错误记录对应。思考模式前提任务的部分尝试经qwen3.6-flash进行JSON格式修复；修复可能对选项保真产生的影响须另行验证。跨文件的51个重复模型与题项分布按源比例等权平均；按有效计数合并的敏感性结果另见图4。", "Appendix")


def commands_appendix() -> None:
  heading("附录C 运行示例与复现文件", page_break=True)
  para("下列命令在项目根目录执行，用于说明一次新运行的流程，需先配置提供方凭证。示例选择明确存在的模型配置；它不重建历史请求，也不构成本稿已执行新的模型调用。", "Appendix")
  commands = [
    "uv sync",
    "uv run rationale-benchmark --list-questionnaires",
    "benchmark_time=$(date -u +%Y-%m-%dT%H-%M-%S-000000Z)",
    'benchmark_dir="results/risky-choice-framing-aliyun-$benchmark_time"',
    "uv run rationale-benchmark --questionnaire risky-choice-framing \\",
    "  --llm-config aliyun --models aliyun/qwen3.5-122b-a10b \\",
    '  --total-population 50 --output "$benchmark_dir"',
    'uv run python bin/evaluate_basic.py "$benchmark_dir"',
    'uv run python bin/rate_results.py "$benchmark_dir"',
  ]
  for command in commands:
    para(command, "Code", indent=False)
  para("以上命令对单次框架任务运行评分。若比较两套任务或多个来源，先将拟共同评分的逐题结果文件放入一个独立目录，再将该目录传给rate_results.py，避免混入不同版本或重复来源。新增问卷首先要通过题项与答案模式校验；新增模型需明确接口的请求参数及思考模式。当前评分器只实现风险决策框架与决策前提两类任务，新增范式仍需编写并验证相应评分。", "Appendix")
  para("本稿的离线核对由audit_data.py生成data_audit.json，保留源文件哈希、逐题分母、配置统计和敏感性结果。create_figures.py生成图1至图4的CSV数据、SVG向量原图、PDF及PNG。build_paper.py根据正文、核验文献和图表构建本文件。图表源与代码置于同一paper目录，便于审查与修订。", "Appendix")
  para("离线复算：在具有项目依赖的Python环境中运行paper/audit_data.py；绘图需matplotlib及其字体处理依赖fonttools，文档构建需python-docx与PyYAML。当前绘图脚本使用macOS宋体及Times New Roman字库。正式归档应同时保存环境锁文件、模型版本说明、脱敏请求与人类材料授权文件。当前本地复现文件不等于已经在公共存储库登记的数据集，公开链接与访问条件由作者依授权范围确认。", "Appendix")


def build() -> None:
  global DOC, EQUATION_NUMBER
  DOC = Document()
  EQUATION_NUMBER = 0
  configure_styles()
  self_check()
  DOC.core_properties.title = "论文自检报告"
  DOC.core_properties.subject = "有限理性图灵测试论文的投稿自检"
  DOC.save(PAPER / "self_check.docx")
  print(f"Saved {PAPER / 'self_check.docx'}; submission checklist.")

  DOC = Document()
  configure_styles()
  lines = (PAPER / "manuscript.md").read_text().splitlines()
  handlers = {"REFERENCES": references, "ENGLISH_ABSTRACT": english_abstract,
              "APPENDIX_MATERIALS": materials, "APPENDIX_METRICS": metrics_appendix,
              "APPENDIX_COMMANDS": commands_appendix}
  for line in lines:
    if not line.strip():
      continue
    if line.startswith("# "):
      p = DOC.add_paragraph(style="Title")
      p.paragraph_format.page_break_before = False
      p.alignment = WD_ALIGN_PARAGRAPH.CENTER
      add_text(p, line[2:])
    elif line.startswith("### "):
      heading(line[4:], 2)
    elif line.startswith("## "):
      if line[3:] == "摘要":
        p = para("摘要", indent=False)
        p.runs[0].bold = True
      else:
        heading(line[3:])
    elif line.startswith("[CODE:"):
      para(line[6:-1], "Code", indent=False)
    elif line.startswith("[FIGURE:"):
      figure(line[8:-1])
    elif line.startswith("[TABLE:"):
      table_by_name(line[7:-1])
    elif line.startswith("[EQUATION:"):
      equation(line[10:-1])
    elif line.startswith("[") and line.endswith("]"):
      handlers[line[1:-1]]()
    else:
      para(line, indent=not line.startswith(("关键词", "中图分类号")))
  DOC.save(PAPER / "paper.docx")
  print(f"Saved {PAPER / 'paper.docx'}; six native equations, four figures.")


if __name__ == "__main__":
  build()
