# 公文格式整理 Skill —— 完整开发任务

你现在位于一个全新的 Git 项目目录中。

你的任务不是给我设计建议，而是**直接在当前目录中实现一个可以实际运行、可以测试、可以打包并用于智能体平台的“公文格式整理 Skill”**。

请自主完成：

- 架构落地；
- 文件创建；
- Python 实现；
- Skill 说明；
- 配置文件；
- 自动化测试；
- 测试 DOCX 生成；
- 端到端测试；
- Bug 修复；
- 输出验证；
- 最终打包。

不要只输出代码片段。

你必须实际创建文件并运行代码。

------

# 1. 项目目标

实现一个：

**中文公文 DOCX 格式整理 Skill**

输入：

一个用户上传的 `.docx` 文档。

输出：

一个内容完全保持不变、但按照指定公文格式重新整理后的 `.docx` 文档。

本项目第一阶段是一个：

**窄功能、强规则、确定性优先的公文格式整理器。**

不要扩展成通用 Word 编辑器。

不要增加：

- PDF；
- PPT；
- Excel；
- OCR；
- 内容润色；
- 内容摘要；
- 文本纠错；
- 自动改编号；
- 自动改标点；
- 知识库；
- RAG；
- 网络 API；
- 外部大模型 API；
- 数据库；
- Web 服务；
- GUI。

只完成本任务要求。

------

# 2. 最重要的设计原则

项目必须严格遵循：

> 原文由程序提取，不由大模型重新生成。

> 文档结构优先由确定性规则识别，大模型只处理无法确定的语义分类。

> 所有格式来自配置文件，不允许模型临场决定格式。

> 最终 DOCX 必须重新读取验证，验证失败不得报告成功。

Markdown 只能作为：

**给智能体 / 大模型查看文档结构的语义视图。**

Markdown 不得成为唯一的数据来源。

真正的事实来源必须是：

**结构化 JSON + 原始段落文字。**

------

# 3. 总体流水线

实现以下流程：

```text
DOCX
 ↓
Preflight 检查
 ↓
extract.py
 ↓
生成：
document.json
document.md
 ↓
classify.py
 ↓
确定性 Regex / 结构规则优先
 ↓
高置信度 → 直接分类
低置信度 → 标记 needs_review
 ↓
智能体仅对 needs_review 项判断类型
 ↓
classification_overrides.json
 ↓
render_docx.py
 ↓
按照 format_rules.json 重新生成 DOCX
 ↓
validate.py
 ↓
重新读取生成文件
 ↓
验证文字 + 格式
 ↓
PASS → 返回 DOCX
FAIL → 明确失败
```

Markdown 不参与最终文字生成。

最终 DOCX 中的文字必须直接来源于最初提取出来的原始 `text` 字段。

------

# 4. 运行环境限制

最终代码运行在内部沙箱。

可以确认存在的 Python 包：

## 文档处理

- python-docx
- python-pptx
- pdfminer.six
- pdfplumber
- PyPDF2
- pypdfium2
- docx2txt
- mammoth

## 数据处理

- pandas
- numpy
- openpyxl
- xlrd
- xlsxwriter
- xlwt
- xlutils

## 图像

- opencv-python
- pillow
- reportlab

## Web

- requests
- httpx
- fastapi
- uvicorn
- beautifulsoup4

## 机器学习

- scikit-learn
- scipy

## 其他

- playwright
- gitpython
- cryptography
- pydantic

此外可以使用 Python 标准库。

------

# 5. 依赖约束

核心实现尽量只使用：

- Python 标准库；
- python-docx。

必要时可以使用：

- mammoth；
- beautifulsoup4。

但：

**不要为了“能用”而强行使用 mammoth。**

如果 python-docx 已经能够可靠获取原始段落，则直接使用 python-docx。

禁止：

- pip install 新包；
- 从互联网下载依赖；
- Pandoc；
- LibreOffice；
- Microsoft Word COM；
- win32com；
- docx4j；
- Node.js 文档转换工具；
- 外部 API。

测试框架使用：

```text
unittest
```

不要依赖 pytest，因为目标沙箱并未明确提供 pytest。

------

# 6. 当前唯一生效的格式规范

不要自行加入其他所谓国家标准。

不要自行补充：

- A4；
- 页边距；
- 页码；
- 版心；
- 首行缩进；
- 段前段后；
- 发文机关；
- 红头；
- 落款；
- 日期；
- 页脚；
- Times New Roman；
- 自动编号。

除非下面明确规定，否则：

**不要擅自增加格式规则。**

当前需求是：

## 主标题

示例：

```text
关于……通知
```

要求：

- 字体：方正小标宋简体；
- 字号：二号；
- 对齐：居中。

其中：

```text
二号 = 22 pt
```

主标题后：

**必须恰好空一行。**

即必须存在一个真正的空白 Word Paragraph。

------

## 一级标题

示例：

```text
一、一级标题
```

格式：

- 黑体；
- 三号。

其中：

```text
三号 = 16 pt
```

------

## 正文

格式：

- 仿宋_GB2312；
- 三号。

------

## 二级标题

示例：

```text
（一）二级标题
```

格式：

- 楷体_GB2312；
- 三号。

------

## 二级标题后的正文

格式：

- 仿宋_GB2312；
- 三号。

------

## 三级标题

示例：

```text
1. 三级标题
```

格式：

- 仿宋_GB2312；
- 三号。

不要自动增加粗体。

不要修改原有编号文字。

------

## 三级标题后的正文

格式：

- 仿宋_GB2312；
- 三号。

------

## 四级标题

示例：

```text
（1）四级标题
```

格式：

- 仿宋_GB2312；
- 三号。

不要自动加粗。

------

## 四级标题后的正文

格式：

- 仿宋_GB2312；
- 三号。

------

## 附件

形式：

```text
附件：1.
　　　2.
```

附件块前：

**必须恰好空一行。**

当前需求没有明确规定附件字体、字号、缩进等其他格式。

因此采取最保守策略：

附件文字默认继承正文文字格式：

- 仿宋_GB2312；
- 三号。

不要擅自修改附件文本。

不要自动补全附件名称。

不要重新编号。

保留用户原来的全角空格、编号和内容。

------

## 全文行距

所有生成的段落统一：

```text
固定值 30 磅
```

包括：

- 主标题；
- 一级标题；
- 二级标题；
- 三级标题；
- 四级标题；
- 正文；
- 附件；
- 规定插入的空白段落。

必须是 Word 的“固定值 30 磅”，不能实现为：

- 1.5 倍行距；
- 30 倍；
- 30 行；
- 自动行距。

在 python-docx 中应使用绝对 Pt 值正确实现。

------

# 7. 不允许修改正文内容

这是最高优先级约束。

禁止：

- 改字；
- 删除文字；
- 增加正文文字；
- 修改标点；
- 修改数字；
- 修改日期；
- 修改人名；
- 修改单位；
- 自动纠错；
- 内容润色；
- 自动补充句子；
- 自动总结；
- 改编号；
- 将“1.”改成“1、”；
- 将全角括号改半角；
- 将半角字符自动变全角；
- 去掉附件中的全角空格。

最终：

**所有原始非空段落的文字内容和出现顺序必须与原文完全一致。**

唯一允许增加或规范化的是：

1. 主标题后恰好一个空白 Paragraph；
2. 附件块前恰好一个空白 Paragraph。

其他原有空段落：

第一版采取保守策略：

**保留。**

不要自动清理其他空段落。

------

# 8. 中间 JSON 数据结构

extract.py 必须生成结构化 JSON。

建议结构：

```json
{
  "source_file": "...",
  "paragraphs": [
    {
      "id": "p0001",
      "index": 0,
      "text": "关于进一步加强工作的通知",
      "is_blank": false,
      "original_style": {},
      "classification": null,
      "confidence": null,
      "classification_source": null
    }
  ],
  "preflight": {},
  "metadata": {}
}
```

可根据实际需要稍作调整。

但是每个段落必须至少有：

- id；
- index；
- text；
- is_blank；
- classification；
- confidence；
- classification_source。

不要让后续阶段通过 Markdown 重新获得原文。

------

# 9. Markdown 语义视图

同时生成：

```text
document.md
```

这个 Markdown 只用于给大模型理解。

建议类似：

```markdown
<!-- p0001 -->
关于进一步加强工作的通知

<!-- p0002 -->
[BLANK]

<!-- p0003 -->
一、总体要求
```

必须保留段落 ID。

需要避免 Markdown 自身改变编号语义。

例如：

```text
1. 三级标题
```

不要依赖 Markdown Renderer 来理解它。

它只是文本视图。

------

# 10. 分类类型

第一版只允许以下类型：

```text
title
heading_1
heading_2
heading_3
heading_4
body
attachment
blank
unknown
```

不要增加几十种类型。

------

# 11. 确定性分类规则

分类优先使用 Regex。

## 一级标题候选

匹配：

```text
一、
二、
三、
四、
五、
六、
七、
八、
九、
十、
十一、
……
```

应支持合理范围内的中文数字编号。

例如：

```regex
^[一二三四五六七八九十百]+、
```

------

## 二级标题候选

例如：

```text
（一）
（二）
（三）
```

规则：

```regex
^（[一二三四五六七八九十百]+）
```

------

## 三级标题候选

例如：

```text
1.
2.
3.
```

同时兼容：

```text
1．
```

但是：

**不得因为某正文恰好以数字开头就强制判定为标题。**

应综合：

- 文本长度；
- 是否以明显句号结尾；
- 是否像完整正文句；
- 前后结构；
- 编号模式。

如果不能高置信度判断：

标记：

```text
unknown / needs_review
```

不要强猜。

------

## 四级标题候选

例如：

```text
（1）
（2）
（3）
```

同样需要避免把长正文误判为标题。

------

## attachment

识别：

```text
附件：
附件:
```

以及附件之后连续的附件列表段落。

不要修改附件内容。

------

# 12. 主标题判断

主标题不能简单地“所有第一段都认为是标题”。

建议综合：

- 第一个非空段落；
- 位于正文第一个一级标题之前；
- 文本长度合理；
- 符合常见公文标题形态；
- 或包含“通知”等明显结尾。

如果不能确定：

标记为：

```text
title_candidate / needs_review
```

由于最终分类枚举不需要新增 title_candidate，可以使用：

```text
classification = unknown
candidate_type = title
```

或类似结构。

不要强制猜测。

------

# 13. LLM 的职责边界

Python 代码本身：

**不得调用任何大模型 API。**

LLM 是 Skill 所在智能体平台本身。

因此工作方式应该是：

```text
classify.py
→ 输出高置信度结果
→ 输出 needs_review 段落
```

如果存在 needs_review：

Skill 的 SKILL.md 应指导智能体：

1. 阅读 `document.md`；
2. 阅读待确认段落及其前后上下文；
3. 只判断这些段落属于哪种类型；
4. 创建 classification_overrides.json；
5. override 中只能写 paragraph id → type；
6. 禁止在 override 中重新输出或修改正文文本。

例如：

```json
{
  "p0012": "heading_3",
  "p0021": "body"
}
```

然后 renderer 使用：

```text
原始 text
+
classification
```

进行生成。

绝不能使用 LLM 返回的正文文本生成 DOCX。

------

# 14. renderer 的实现原则

`render_docx.py` 是核心确定性模块。

职责：

```text
document.json
+
classification
+
classification_overrides
+
format_rules.json
→
output.docx
```

它不做：

- 语义推断；
- LLM 调用；
- 内容生成。

------

# 15. 中文字体设置必须正确

python-docx 对中文字体不能只写：

```python
run.font.name = "黑体"
```

必须正确设置 Word XML 中中文 East Asia 字体。

应使用 python-docx 自带 XML API，例如通过：

```text
qn("w:eastAsia")
```

设置相应字体。

代码应确保：

```text
方正小标宋简体
黑体
楷体_GB2312
仿宋_GB2312
```

在 DOCX XML 中真正写入。

不要通过检测操作系统是否安装字体来决定是否写字体。

DOCX 只需要正确声明字体名称。

运行环境没有字体文件，不应导致程序失败。

不要嵌入字体文件。

------

# 16. format_rules.json

所有具体格式值必须集中放到：

```text
config/format_rules.json
```

不要把格式参数大量散落在 Python 文件中。

建议至少包含：

```text
title
heading_1
heading_2
heading_3
heading_4
body
attachment
global
blank_policy
```

其中：

```text
title.font = 方正小标宋简体
title.size_pt = 22
title.alignment = center

heading_1.font = 黑体
heading_1.size_pt = 16

heading_2.font = 楷体_GB2312
heading_2.size_pt = 16

heading_3.font = 仿宋_GB2312
heading_3.size_pt = 16

heading_4.font = 仿宋_GB2312
heading_4.size_pt = 16

body.font = 仿宋_GB2312
body.size_pt = 16

attachment.inherit = body

global.line_spacing_pt = 30
```

这是示意结构。

可以合理设计实际 JSON schema。

但不要加入需求中没有明确给出的公文格式。

------

# 17. 页面设置策略

当前需求没有给出：

- A4；
- 页边距；
- 页眉；
- 页脚；
- 页码；
- 首行缩进。

因此：

**不得自行实现这些格式规范。**

对于输入 DOCX：

尽可能保留源文档 Section 的：

- page_width；
- page_height；
- margins；
- orientation；
- header/footer distance。

如果重新创建 DOCX：

应把原文档第一节页面属性复制到新文档。

如果存在多 Section：

第一版 Preflight 应认为属于复杂文档。

不要悄悄把多 Section 合成一个 Section。

可以返回“不支持复杂分节”的错误。

------

# 18. Preflight

处理前必须检查输入文档。

第一版主要支持：

**普通纯文字公文。**

必须检测：

- 文件不存在；
- 非 `.docx`；
- DOCX 损坏；
- 多 Section；
- 表格；
- 图片；
- 文本框等明显复杂对象。

对于：

```text
表格
图片
多分节
```

第一版采取 fail-safe：

**停止格式重建并给出明确的 unsupported_complex_content。**

原因：

不能为了格式整理导致原始对象丢失。

不要静默忽略。

错误必须清楚告诉用户：

当前版本只保证纯文字公文的内容完整性。

------

# 19. Validator

`validate.py` 必须是独立模块。

这是本项目的关键质量保障。

输出 DOCX 创建完成后必须：

**重新打开一次。**

然后验证：

## 内容完整性

提取源文档所有：

```text
非空 paragraph.text
```

提取输出文档所有：

```text
非空 paragraph.text
```

要求：

```text
完全相等
顺序完全相同
```

不得只是比较数量。

必须逐字符比较。

------

## 格式验证

根据 classification 检查：

### title

- 方正小标宋简体；
- 22pt；
- center；
- fixed 30pt。

### heading_1

- 黑体；
- 16pt；
- fixed 30pt。

### heading_2

- 楷体_GB2312；
- 16pt；
- fixed 30pt。

### heading_3

- 仿宋_GB2312；
- 16pt；
- fixed 30pt。

### heading_4

- 仿宋_GB2312；
- 16pt；
- fixed 30pt。

### body

- 仿宋_GB2312；
- 16pt；
- fixed 30pt。

### attachment

- 当前继承 body；
- fixed 30pt。

------

# 20. 中文字体验证

Validator 不得只检查：

```python
run.font.name
```

还必须验证 DOCX XML 中的：

```text
w:rFonts / w:eastAsia
```

确保中文字体实际正确。

------

# 21. 空行验证

必须验证：

## 主标题后

恰好一个空白 Paragraph。

不能：

- 没有；
- 两个；
- 三个。

## 附件前

如果存在附件块：

恰好一个空白 Paragraph。

如果不存在附件：

不要额外增加尾部空行。

------

# 22. 行距验证

必须验证实际：

```text
固定值 30 pt
```

不能仅验证配置文件。

应读取输出 DOCX 的实际 ParagraphFormat / XML 后确认。

------

# 23. Validator 失败策略

如果任何核心验收项失败：

```text
success = false
```

不能报告：

“处理成功”。

错误报告至少包含：

```json
{
  "success": false,
  "errors": [],
  "warnings": [],
  "output_file": null
}
```

可根据需要扩展。

------

# 24. CLI 设计

请给 `scripts/main.py` 一个清晰 CLI。

建议支持：

```text
analyze
format
render
validate
```

例如：

```bash
python scripts/main.py analyze input.docx --work-dir work
```

生成：

```text
work/document.json
work/document.md
work/analysis.json
```

如果所有分类都可确定：

可以直接：

```bash
python scripts/main.py format input.docx --output output.docx
```

如果存在 needs_review：

format 不得默默猜测。

应返回明确状态，例如：

```text
NEEDS_REVIEW
```

并告诉调用方：

```text
review_file
document_md
```

智能体创建：

```text
classification_overrides.json
```

之后：

```bash
python scripts/main.py render ... --overrides classification_overrides.json
```

再自动 validate。

具体参数设计可以优化，但必须保持简单。

------

# 25. SKILL.md

根目录必须存在：

```text
SKILL.md
```

它是最终 Skill 的核心说明。

必须清楚告诉智能体：

## 什么时候调用

用户提出：

- 整理公文格式；
- 按公文要求排版；
- 规范 Word 公文格式；
- 将 DOCX 整理为指定格式。

并提供 DOCX 时。

------

## 工作步骤

必须写明：

1. 先运行 Preflight / analyze；
2. 读取 document.md；
3. 查看是否有 needs_review；
4. 没有 → 直接格式化；
5. 有 → LLM 只判断对应 paragraph id 的类型；
6. 写 classification_overrides；
7. 调用 renderer；
8. 调用 validator；
9. PASS 后才返回最终 DOCX。

------

## LLM 禁止事项

SKILL.md 要非常明确：

大模型不得：

- 重写正文；
- 重新输出整篇文章作为输入；
- 自动修改标题编号；
- 修改标点；
- 修改附件内容；
- 自行增加其他公文标准。

------

# 26. 建议最终项目结构

目标控制在大约以下规模：

```text
gongwen-format-skill/
├── AGENTS.md
├── SKILL.md
├── README.md
├── config/
│   └── format_rules.json
├── references/
│   └── format_spec.md
├── scripts/
│   ├── main.py
│   ├── extract.py
│   ├── classify.py
│   ├── render_docx.py
│   └── validate.py
├── tests/
│   ├── test_classify.py
│   ├── test_render.py
│   └── test_e2e.py
├── samples/
│   ├── input/
│   └── output/
└── dist/
```

允许增加：

```text
scripts/utils.py
```

但仅在多个模块确实共享代码时增加。

不要为了“模块化”继续拆十几个 Python 文件。

准确性来自：

- 明确规则；
- 数据不可变；
- Validator；
- 测试；

不是来自文件数量。

------

# 27. AGENTS.md

创建一个简洁的 AGENTS.md。

用于 Codex 后续继续维护项目。

至少写入：

- 不允许新增外部依赖；
- 不允许联网；
- 不修改正文；
- 规则集中在 format_rules.json；
- 测试使用 unittest；
- 所有改动必须运行完整测试；
- 文档输出必须经过 validate；
- 不允许绕过 Validator；
- 不允许自行增加未确认公文规范。

不要写成几千字。

------

# 28. README.md

面向开发人员。

应包括：

- 项目是什么；
- 环境要求；
- 文件结构；
- 如何运行；
- 如何测试；
- 如何生成测试文件；
- 如何打包；
- 当前限制；
- 如何修改 format_rules.json。

------

# 29. references/format_spec.md

把本需求作为人类可读的规范保存在这里。

必须明确注明：

**当前 Skill 只严格实现内部提供的这些格式要求，并不自行声称完整实现任何其他国家标准。**

不要引用或增加其他未提供标准。

------

# 30. 测试方法

测试必须使用：

```bash
python -m unittest discover -s tests -v
```

不依赖 pytest。

------

# 31. test_classify.py

至少测试：

1. `一、标题` → heading_1；
2. `（一）标题` → heading_2；
3. `1. 标题` → heading_3；
4. `1．标题` → heading_3；
5. `（1）标题` → heading_4；
6. 普通正文 → body；
7. 附件 → attachment；
8. 空段 → blank；
9. 容易误判的长数字正文不能盲目识别为标题；
10. 不确定情况能进入 needs_review。

------

# 32. test_render.py

程序自动创建一个格式故意混乱的 DOCX。

原始格式应该故意包含：

- 错误字体；
- 错误字号；
- 错误对齐；
- 错误行距。

内容包含：

```text
关于进一步加强人工智能应用管理工作的通知

一、总体要求
这是一级标题后的正文内容，不允许发生任何修改。

（一）主要任务
这是二级标题后的正文内容，不允许发生任何修改。

1. 加强组织管理
这是三级标题后的正文内容，不允许发生任何修改。

（1）明确责任分工
这是四级标题后的正文内容，不允许发生任何修改。

附件：1.人工智能应用管理任务表
　　　2.相关工作说明
```

输入文件可以故意没有正确空行。

Renderer 后必须验证：

- 主标题正确；
- 主标题后恰好一空行；
- 一级标题黑体三号；
- 二级标题楷体_GB2312 三号；
- 三级标题仿宋_GB2312 三号；
- 四级标题仿宋_GB2312 三号；
- 正文仿宋_GB2312 三号；
- 附件前恰好一空行；
- 全文固定30磅；
- 所有非空文字完全没变。

------

# 33. test_e2e.py

完成真正端到端：

```text
创建混乱DOCX
↓
analyze
↓
classify
↓
render
↓
validate
↓
重新读取
```

测试：

## 文字完整性

原始非空文本：

```text
==
```

输出非空文本。

必须完全相同。

## 顺序

必须完全相同。

## 字体

读取 XML 的 `w:eastAsia` 验证。

## 字号

必须正确。

## 行距

30pt。

## 空行

恰好符合要求。

## 幂等性

再次把：

```text
output.docx
```

作为输入重新运行。

第二次结果必须仍然通过全部验证。

不得产生：

- 越改越多空行；
- 内容变化；
- 编号变化；
- 格式漂移。

------

# 34. Preflight 测试

至少测试：

- 非 DOCX；
- 损坏 DOCX；
- 有表格；
- 有图片；
- 多 Section。

均不得静默损坏文档。

------

# 35. 不要虚假测试

禁止：

- 写完测试但不运行；
- mock 掉核心 renderer；
- mock 掉 validator；
- 只检查“函数被调用”；
- 只检查文件存在；
- 只检查程序 exit code。

必须打开真实生成的 DOCX 检查内部属性。

------

# 36. 不要因为字体未安装导致测试失败

测试验证的是：

DOCX 中声明的字体属性。

不是：

操作系统有没有安装方正小标宋简体。

不得：

- 下载字体；
- 嵌入字体；
- 搜索字体文件。

------

# 37. 代码质量

要求：

- Python 3；
- UTF-8；
- 函数职责清晰；
- 类型提示适度；
- 不过度抽象；
- 不建立没必要的类层级；
- 不引入框架；
- 错误信息明确；
- 中文路径可工作；
- Windows/Linux 路径使用 pathlib；
- 临时目录安全；
- 不覆盖源文件。

------

# 38. 错误码

至少考虑：

```text
INVALID_INPUT
INVALID_DOCX
UNSUPPORTED_COMPLEX_CONTENT
NEEDS_REVIEW
INVALID_OVERRIDE
RENDER_FAILED
VALIDATION_FAILED
SUCCESS
```

无需做复杂错误框架。

------

# 39. 输出报告

每次处理建议生成：

```text
result.json
```

至少：

```json
{
  "success": true,
  "source_file": "...",
  "output_file": "...",
  "validation": {},
  "warnings": [],
  "needs_review": []
}
```

不要输出大量完整正文到日志。

------

# 40. 保护敏感内容

因为项目用于内部环境：

- 不访问网络；
- 不上传文件；
- 不打印全文到日志；
- 不写外部 API；
- 不加入 telemetry；
- 不读取工作目录之外文件；
- 不把真实文件写进测试代码。

所有测试文档必须使用程序自动生成的虚构文本。

------

# 41. Browser / Markdown 的定位

智能体平台可能先通过 Browser 把文档转成网页内容供大模型阅读。

本项目不要依赖 Browser 的 HTML 作为唯一事实来源。

核心路径仍然是：

```text
DOCX
→ python-docx
→ structured JSON
→ Markdown view
```

如果未来平台只能提供 HTML，可以在 `extract.py` 中预留一个非常简单的 HTML Adapter 接口。

但：

**本轮不要为了这个功能拖慢核心 DOCX 路线。**

如果实现 HTML fallback：

- 使用 BeautifulSoup；
- 只负责获得段落文本；
- 明确标记 source_type=html；
- 不宣称能够保留 DOCX 页面属性。

Mammoth 同样只允许作为未来备用语义转换工具，不得成为核心事实来源。

------

# 42. Skill 打包

当所有测试通过后：

创建：

```text
dist/gongwen-format-skill.zip
```

ZIP 根目录必须直接包含：

```text
SKILL.md
config/
references/
scripts/
```

不要出现：

```text
gongwen-format-skill/
    gongwen-format-skill/
        SKILL.md
```

这种多层嵌套。

部署 ZIP 中不必包含：

- tests；
- samples；
- .git；
- **pycache**；
- 临时 work 目录。

源码项目中保留测试。

使用 Python 标准库 `zipfile` 完成即可。

无需额外创建 package_skill.py，除非确有必要。

------

# 43. 开发执行顺序

不要一次写完所有文件然后宣布成功。

按以下顺序实际工作：

## Phase 1

检查环境。

确认：

```text
python
python-docx
```

可用。

不要 pip install。

------

## Phase 2

创建：

- AGENTS.md；
- config/format_rules.json；
- references/format_spec.md。

------

## Phase 3

实现：

- extract.py；
- classify.py。

立即运行分类测试。

------

## Phase 4

实现：

- render_docx.py。

运行 render 测试。

------

## Phase 5

实现：

- validate.py。

确保是真实 DOCX 验证。

------

## Phase 6

实现：

- main.py；
- SKILL.md；
- README.md。

------

## Phase 7

运行全部：

```bash
python -m unittest discover -s tests -v
```

------

## Phase 8

执行真实端到端测试。

不要只运行 unittest。

真正执行 CLI：

```text
测试输入 DOCX
→ CLI
→ 输出 DOCX
```

然后使用 validate CLI 再验证一次。

------

## Phase 9

再次以第一次输出作为输入。

验证幂等性。

------

## Phase 10

检查：

```text
git diff
```

审阅自己写的代码。

主动寻找：

- 文字可能被修改的路径；
- 字体 XML 设置 Bug；
- 30pt 行距 Bug；
- 空行重复 Bug；
- needs_review 被绕过；
- 错误文件被报告成功。

发现问题就修。

------

## Phase 11

打包：

```text
dist/gongwen-format-skill.zip
```

------

# 44. 最终验收条件

只有全部满足才允许宣布完成：

## 输入输出

- 能读取真实 DOCX；
- 输出真实 DOCX；
- 不覆盖输入。

## 文字

- 原始所有非空 paragraph.text 与输出完全一致；
- 顺序完全一致。

## 标题

- 主标题：方正小标宋简体，22pt，居中；
- 一级：黑体，16pt；
- 二级：楷体_GB2312，16pt；
- 三级：仿宋_GB2312，16pt；
- 四级：仿宋_GB2312，16pt。

## 正文

- 仿宋_GB2312；
- 16pt。

## 附件

- 前恰好空一行；
- 内容不变；
- 当前继承正文格式。

## 空行

- 标题后恰好空一行；
- 附件前恰好空一行。

## 行距

- 全文固定 30pt。

## 中文字体

- `w:eastAsia` 正确。

## 安全

- 表格/图片/复杂分节不会被静默删除；
- 不支持则明确失败。

## LLM

- 不使用 LLM 重新输出原文；
- LLM 只允许输出 paragraph id 到 type 的映射。

## 测试

- unittest 全部通过；
- 真实 CLI E2E 通过；
- 幂等测试通过。

## 部署包

- ZIP 已生成；
- 结构正确；
- SKILL.md 位于 ZIP 根目录。

------

# 45. 最终回复要求

完成所有工作之后，不要给我一篇泛泛的说明。

请最后报告：

1. 最终目录树；
2. 每个核心文件作用；
3. 运行的实际测试命令；
4. unittest 通过数量；
5. E2E 测试结果；
6. 原始文本和输出文本是否逐字一致；
7. 各标题实际检测到的 eastAsia 字体；
8. 实际检测到的字号；
9. 实际检测到的行距；
10. 两处规定空行是否正确；
11. 幂等测试是否通过；
12. Preflight 复杂内容测试是否通过；
13. 当前仍存在的限制；
14. 最终 ZIP 路径。

如果测试失败：

继续修复。

不要在测试仍然失败时结束任务。

除非遇到当前环境中真正无法解决的阻塞，否则请自主推进，不要频繁询问我。

不要自行扩大需求。

最终目标只有一个：

**得到一个可以上传到智能体平台、严格按照本需求整理纯文字 DOCX 公文格式、并且不会修改原文内容的可靠 Skill。**