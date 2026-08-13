# HiAgent 公文格式整理 Skill —— Browser 纯文本输入架构改造任务

你现在正在一个已经能够运行的“公文格式整理 Skill”项目中工作。

这是一次**基于真实 HiAgent 平台运行结果的架构调整**。

不要创建新项目、不要创建 v2、不要复制出另一个 Skill。

请直接检查当前仓库，在现有代码基础上进行合理重构、删除冗余实现、修改测试，并最终重新生成可部署 ZIP。

这次允许调整现有架构。

目标不是尽可能保留旧代码，而是得到一个：

**逻辑简单、输入明确、确定性强、适合 HiAgent + Qwen3、能够稳定把 Browser 提取出的公文纯文本生成规范 DOCX 的 Skill。**

------

# 一、真实平台环境

实际 HiAgent 运行链路已经确认如下：

```text
用户上传 DOCX
    ↓
HiAgent Browser 插件
    ↓
Browser 将 DOCX 转换为可供模型读取的网页内容 / 纯文本
    ↓
Qwen3 获取这些文本
    ↓
调用 Skill
```

已经经过人工测试确认：

Browser 输出基本能够正常保留：

- 原文字；
- 中文标点；
- 数字；
- 标题；
- 段落；
- 换行；
- 附件等主要文字结构。

因此：

**本 Skill 不再要求拿到原始 DOCX 文件。**

正式运行输入改为：

```text
Browser 提取后的文本
```

Skill 的任务变为：

```text
Browser文本
→ 识别公文结构
→ 按内部固定规则生成新的DOCX
→ 自动验证
→ 返回文件
```

------

# 二、本轮核心架构决定

正式部署版本只以：

```text
browser_text / source_text
```

作为主要输入。

不要为了兼容以前的 DOCX 输入方式增加额外复杂度。

如果旧项目存在：

- DOCX 输入校验；
- DOCX source_file 要求；
- DOCX → Markdown；
- DOCX → JSON；
- Mammoth 解析；
- Browser HTML 再解析；
- DOCX Preflight；
- 原始 DOCX 页面结构保留；

请检查其是否仍然有实际作用。

如果只是为旧 DOCX 输入流程服务，请删除。

本项目现在不是：

“修改原 Word 文件”。

而是：

**“根据 Browser 已经提取好的文字重新生成规范公文 DOCX”。**

------

# 三、最终目标流水线

最终运行逻辑应尽量收敛成：

```text
source_text
    ↓
input_adapter.py
    ↓
canonical paragraphs
    ↓
classify.py
    ↓
确定性规则分类
    ↓
┌─────────────────────────┐
│ 没有歧义                │
│ → 直接继续              │
├─────────────────────────┤
│ 存在少量歧义            │
│ → NEEDS_REVIEW          │
│ → Qwen3只判断段落类型   │
│ → overrides             │
└─────────────────────────┘
    ↓
render_docx.py
    ↓
validate.py
    ↓
SUCCESS
    ↓
返回DOCX
```

模型正常情况下只需要调用一个入口。

不要要求 Qwen3 每次手工执行：

extract
→ classify
→ render
→ validate

这些步骤必须由：

```text
main.py
```

自动编排。

------

# 四、针对 Qwen3 的设计原则

最终执行 Skill 的模型是 Qwen3，而且并非能力最强版本。

因此整个 Skill 必须针对以下特点设计：

- 不让模型承担大量代码逻辑判断；
- 不要求模型理解复杂架构；
- 不要求模型重复复制全文；
- 不要求模型执行很多连续命令；
- 不要求模型维护复杂状态；
- 不要求模型生成复杂 JSON；
- 不让模型决定任何字体、字号、行距；
- 不让模型判断能够由正则解决的问题；
- 尽量做到正常公文一次调用成功；
- 歧义分支最多允许一次模型分类。

原则：

> 能写进 Python 的确定性行为，不交给 Qwen3。

> 能用 Regex 判断的，不交给 Qwen3。

> 格式永远由配置和代码决定，不交给 Qwen3。

> Qwen3 最多负责“这一个段落是什么类型”。

------

# 五、最终建议目录

请先检查当前目录。

允许根据实际情况调整，但目标应接近：

```text
gongwen-format-skill/
├── AGENTS.md
├── SKILL.md
├── README.md
│
├── config/
│   └── format_rules.json
│
├── references/
│   └── format_spec.md
│
├── scripts/
│   ├── main.py
│   ├── input_adapter.py
│   ├── classify.py
│   ├── render_docx.py
│   ├── validate.py
│   └── docx_utils.py       # 只有确有共享逻辑时保留
│
├── tests/
│   ├── test_input_adapter.py
│   ├── test_classify.py
│   ├── test_render_validate.py
│   └── test_e2e_browser_text.py
│
├── samples/
│   └── browser_input.txt
│
└── dist/
```

不要为了模块化拆出十几个 Python 文件。

如果 `docx_utils.py` 只有几十行且没有明显复用价值，可以合并。

推荐核心脚本数量：

**5～6 个。**

------

# 六、删除冗余实现

请主动检查当前项目是否还存在以下旧设计：

- extract.py 用于读取源 DOCX；
- document.md 作为核心中间数据；
- DOCX 输入 Preflight；
- 表格、图片、多 Section 检测；
- mammoth；
- BeautifulSoup；
- docx2txt；
- Markdown Renderer；
- HTML Adapter；
- 通用模板系统；
- 多种公文 preset；
- 通用 Word 编辑器能力；
- RAG；
- 知识库；
- style XML assets；
- 与当前需求无关的 minimax-docx 遗留文件。

如果这些内容已经失去实际用途：

**删除。**

不要为了“以后也许能用”长期保留死代码。

本 Skill 当前只解决：

```text
Browser文本
→ 固定格式公文DOCX
```

------

# 七、依赖

目标内部沙箱已经有：

- python-docx；
- Python 标准库；

本轮核心实现只需要：

```text
Python标准库
python-docx
```

除非发现明确必要性，否则不要使用：

- mammoth；
- BeautifulSoup；
- pandas；
- requests；
- pydantic；
- 其他包。

禁止：

- pip install；
- 网络访问；
- 外部 API；
- LLM API；
- Pandoc；
- LibreOffice；
- Word COM。

------

# 八、输入契约

新的核心输入定义：

```text
source_text: str
```

即：

**Browser 实际返回给模型的原始文字内容。**

Skill 不应再出现：

```text
必须上传DOCX
source_file必须是.docx
```

等限制。

当收到纯文本时：

必须正常处理。

不得返回：

“输入为纯文本，不符合DOCX要求”。

------

# 九、main.py 必须提供清晰 Python API

除了 CLI，本项目应提供一个清晰函数接口。

例如：

```python
process_text(
    source_text: str,
    output_dir: str | Path,
    overrides: dict | None = None
) -> dict
```

具体函数名可以根据现有实现调整。

但必须保证：

输入一个字符串就能完成整个流程。

这样 HiAgent 未来无论如何封装 Skill，都不需要伪造 DOCX 输入。

------

# 十、本地 CLI

为了本地测试，main.py 至少支持：

```text
--text-file
```

例如：

```bash
python scripts/main.py --text-file samples/browser_input.txt --output-dir work
```

不要要求把几千字正文直接作为 shell 参数。

避免：

```text
--text "超长全文……"
```

因为可能有：

- shell quoting；
- 长度；
- 换行；
- 中文字符；
- 特殊符号；

问题。

可以额外支持 stdin，但不是必须。

------

# 十一、input_adapter.py

这是本轮新增/核心模块。

职责：

```text
Browser source_text
→ canonical paragraph records
```

每个非空文本段落至少包含：

```json
{
  "id": "p0001",
  "index": 0,
  "text": "原始文字",
  "analysis_text": "仅供分类使用的文字",
  "classification": null,
  "confidence": null,
  "classification_source": null
}
```

------

# 十二、原文保护原则

这是整个 Skill 的最高优先级。

必须区分：

```text
text
```

和：

```text
analysis_text
```

### text

必须尽可能保持 Browser 输入原样。

后续 Renderer 只能使用：

```text
text
```

生成 DOCX。

### analysis_text

允许为了分类：

- 去除行首尾普通空白的副本；
- 进行正则匹配；
- 判断编号。

但是：

**analysis_text 永远不能用于最终输出正文。**

------

# 十三、禁止正文 normalize

特别检查并禁止以下危险逻辑作用于 `text`：

```python
text.strip()
```

覆盖原 text；

```python
re.sub(r"\s+", " ", text)
```

以及：

- replace 标点；
- 自动全半角转换；
- 删除全角空格；
- collapse whitespace；
- 自动编号；
- Markdown normalize；
- Unicode 文本重写。

允许统一底层换行编码：

```text
\r\n
\r
→
\n
```

但不得修改实际非空行文字。

------

# 十四、空白行的新策略

由于 Browser 自身可能因为网页转换产生额外视觉空行，因此：

**原输入空白行不再作为必须保真的正文内容。**

正文完整性验证只比较：

```text
非空文本段落
```

输出格式采取：

```text
canonical blank policy
```

即严格按照当前内部要求重建空白段落。

只需要输出以下规定空行：

### 主标题后

恰好：

```text
1个空白Paragraph
```

### 附件块前

恰好：

```text
1个空白Paragraph
```

其他 Browser 输入中的空白行：

默认不复制到最终 DOCX。

这样避免：

- Browser 多生成空行；
- 原文已有空行；
- Renderer 再增加空行；

导致重复空白。

------

# 十五、当前唯一格式要求

只能实现以下明确规则。

不要自行增加其他国家标准。

## 主标题

例：

```text
关于……通知
```

要求：

- 方正小标宋简体；
- 二号；
- 22 pt；
- 居中；
- 固定值 30 磅行距。

标题后：

恰好空一行。

------

## 一级标题

例：

```text
一、一级标题
```

要求：

- 黑体；
- 三号；
- 16 pt；
- 固定值 30 磅。

------

## 二级标题

例：

```text
（一）二级标题
```

要求：

- 楷体_GB2312；
- 三号；
- 16 pt；
- 固定值 30 磅。

------

## 三级标题

例：

```text
1. 三级标题
```

要求：

- 仿宋_GB2312；
- 三号；
- 16 pt；
- 固定值 30 磅。

不要自动加粗。

不要修改编号。

兼容：

```text
1．标题
```

------

## 四级标题

例：

```text
（1）四级标题
```

要求：

- 仿宋_GB2312；
- 三号；
- 16 pt；
- 固定值 30 磅。

不要自动加粗。

------

## 正文

要求：

- 仿宋_GB2312；
- 三号；
- 16 pt；
- 固定值 30 磅。

------

## 附件

例：

```text
附件：1.
　　　2.
```

附件块前：

恰好空一行。

当前没有额外附件字体规则，因此继承正文：

- 仿宋_GB2312；
- 16 pt；
- 固定值30磅。

必须保留 Browser 提供的附件文字，包括：

- 数字；
- 标点；
- 全角空格；
- 内容。

------

# 十六、不要添加未规定格式

禁止自行增加：

- A4；
- 页边距；
- 页码；
- 页眉；
- 页脚；
- 发文机关；
- 红头；
- 日期；
- 版记；
- 首行缩进；
- 段前；
- 段后；
- Times New Roman；
- 自动编号；
- Word Heading Style；
- 自动目录。

当前需求没有写，就不要实现。

------

# 十七、format_rules.json

所有真正的排版值集中在：

```text
config/format_rules.json
```

至少：

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

Python 文件不能散落大量字体字号常量。

例如逻辑上：

```json
{
  "global": {
    "line_spacing_pt": 30
  },
  "title": {
    "font": "方正小标宋简体",
    "size_pt": 22,
    "alignment": "center"
  },
  "heading_1": {
    "font": "黑体",
    "size_pt": 16
  }
}
```

具体 schema 可优化。

------

# 十八、中文字体必须真正写入 DOCX

Renderer 设置字体时不能只使用：

```python
run.font.name
```

必须正确设置 DOCX XML：

```text
w:rFonts
```

至少处理：

```text
w:eastAsia
w:ascii
w:hAnsi
w:cs
```

对于当前严格格式要求：

建议四项都设置为对应目标字体。

例如正文：

```text
仿宋_GB2312
```

这样：

- 中文；
- 英文；
- 数字；

不会因为 Word 默认西文字体产生不可控差异。

不检查系统是否安装字体。

不下载字体。

不嵌入字体。

------

# 十九、分类架构

`classify.py` 应做到：

**规则优先。**

第一版只允许：

```text
title
heading_1
heading_2
heading_3
heading_4
body
attachment
unknown
```

不要扩大类型集合。

------

# 二十、一级标题

高置信度：

```regex
^[一二三四五六七八九十百]+、
```

例如：

```text
一、总体要求
十一、其他事项
```

直接识别：

```text
heading_1
```

不需要 Qwen3。

------

# 二十一、二级标题

例如：

```regex
^（[一二三四五六七八九十百]+）
```

直接：

```text
heading_2
```

------

# 二十二、三级标题

支持：

```text
1.
2.
3.
```

以及：

```text
1．
```

不能仅因为一行以数字开头就无条件认定为 heading_3。

可以结合：

- 行长度；
- 是否明显是完整长句；
- 是否以 `。！？；` 等结束；
- 当前上下文。

高置信度则直接 heading_3。

明显是正文则 body。

真正模糊才 unknown。

目标是：

**尽可能减少 Qwen3 review。**

------

# 二十三、四级标题

例如：

```text
（1）
（2）
```

结合合理长度判断。

高置信度直接：

```text
heading_4
```

------

# 二十四、正文

对于：

- 没有标题编号特征；
- 普通陈述句；
- 明显完整正文；

直接：

```text
body
```

不要把大量普通正文标记为 unknown。

------

# 二十五、附件

匹配：

```text
^附件[:：]
```

从附件起始段落开始。

附件通常位于文档末尾。

附件第一行：

```text
attachment
```

其后连续附件列表行也应归为 attachment。

由于 attachment 当前继承 body 字体字号，所以即使后续附件列表分类只影响“附件块前空一行”，也不得修改其文字。

------

# 二十六、主标题识别

尽量自动解决。

重点看：

- 第一非空段；
- 位于第一个 heading_1 之前；
- 长度合理；
- 是否符合常见标题形态；
- 是否包含类似：
  - 通知；
  - 报告；
  - 请示；
  - 函；
  - 意见；
  - 决定；
  - 通报；
  - 纪要；
  - 方案；
    等结尾特征。

明显符合：

```text
title
```

不要 review。

如果第一非空段是否为 title 真的无法确定：

才：

```text
unknown
candidate_types = ["title", "body"]
```

交给 Qwen3。

------

# 二十七、Qwen3 Review 必须非常有限

不要把整篇文档重新交给模型重新分类。

如果存在 unknown：

生成一个非常小的：

```text
review.json
```

每个项目只包含：

```json
{
  "id": "p0012",
  "text": "1.某段文字",
  "previous_text": "前一段必要上下文",
  "next_text": "后一段必要上下文",
  "candidate_types": ["heading_3", "body"],
  "suggested_type": "heading_3"
}
```

不要提供大量无关上下文。

------

# 二十八、Qwen3 只允许返回简单映射

overrides 格式必须极简单：

```json
{
  "p0012": "heading_3",
  "p0041": "body"
}
```

禁止模型返回：

```json
{
  "p0012": {
    "text": "...",
    "reason": "...",
    "style": "..."
  }
}
```

Qwen3 永远不能重新返回正文。

Renderer 只能使用：

```text
input_adapter中保存的原始 text
```

------

# 二十九、限制候选类型

为降低 Qwen3 出错率：

不要让每个 unknown 都从 7 种类型中选择。

例如：

数字 `1.` 模糊：

```text
["heading_3", "body"]
```

第一非空标题候选：

```text
["title", "body"]
```

不要出现：

```text
["title","heading_1","heading_2","heading_3","heading_4","body","attachment"]
```

这种无意义选择。

------

# 三十、最多一次 Review

模型 review 完成后：

程序验证 overrides。

如果：

- paragraph id 不存在；
- type 不在 candidate_types；
- JSON 非法；

返回：

```text
INVALID_OVERRIDE
```

给出非常明确的错误。

不要无限循环模型 review。

如果一次 review 后仍不能继续：

fail-safe。

不要强猜。

------

# 三十一、正常路径必须是一键执行

绝大部分标准公文：

```text
Browser text
→ main.py
→ SUCCESS
```

不应该进入 review。

这是针对 Qwen3 的关键性能目标。

------

# 三十二、main.py 状态设计

stdout 应尽量只输出最终结构化结果。

避免大量进度日志干扰模型。

建议：

```json
{
  "status": "SUCCESS",
  "output_file": "...",
  "validation_passed": true
}
```

或：

```json
{
  "status": "NEEDS_REVIEW",
  "review_file": "...",
  "review_count": 2
}
```

错误：

```json
{
  "status": "VALIDATION_FAILED",
  "errors": [...]
}
```

调试日志写 stderr 或调试文件。

------

# 三十三、状态数量要少

建议只保留：

```text
SUCCESS
NEEDS_REVIEW
INVALID_INPUT
INVALID_OVERRIDE
RENDER_FAILED
VALIDATION_FAILED
```

不要建立复杂状态机。

------

# 三十四、Renderer

`render_docx.py` 不做任何语义推理。

输入：

```text
paragraph records
+
final classifications
+
format_rules.json
```

输出：

```text
DOCX
```

原则：

每个原始非空文本段落：

最好生成一个明确的 Word Paragraph。

每个 paragraph 使用原始：

```text
text
```

创建内容。

由于现在本质是纯文本重建：

可以优先采用：

```text
一个paragraph
+
一个run
```

避免复杂 run 拆分。

这样更容易保证：

- 内容完整；
- 字体一致；
- Validator准确。

------

# 三十五、空行 Renderer

不要复制 Browser 原有 blank paragraphs。

渲染时根据语义：

### title 之后

删除/忽略原有空白结构，然后：

```text
插入恰好一个空Paragraph
```

### attachment 第一段之前

如果前面不是标题后的同一个规定空段：

插入：

```text
恰好一个空Paragraph
```

最终 Validator 必须确认：

数量是 exactly one。

------

# 三十六、30磅固定值

必须使用 python-docx 正确的绝对值行距。

例如核心逻辑应等价于：

```python
paragraph.paragraph_format.line_spacing = Pt(30)
```

并验证其 XML / python-docx 属性代表：

```text
exact / fixed
```

而不是：

- multiple；
- 1.5；
- 30倍。

所有输出 Paragraph 包括规定空白段落都应用。

------

# 三十七、Validator 的事实基准发生变化

这是本次改造非常重要的修改。

以前可能写：

```text
与原始DOCX内容一致
```

现在不能这么说。

因为 Skill 没有读取原 DOCX。

Validator 的 ground truth 必须是：

```text
Browser source_text
```

处理后的 canonical 非空段落。

最终报告必须明确：

```text
verified_against = browser_extracted_text
```

禁止声称：

```text
与原始DOCX逐字一致
```

------

# 三十八、内容完整性 Validator

从输入 canonical paragraphs：

取：

```text
所有非空 text
```

从输出 DOCX：

重新读取：

```text
所有非空 paragraph.text
```

要求：

```text
数量一致
顺序一致
逐字符一致
```

必须严格 equality。

不能：

- strip 后比较；
- normalize 后比较；
- 忽略标点比较。

------

# 三十九、必须测试全角字符

测试 Browser 输入必须包含：

```text
附件：1.测试附件
　　　2.第二个附件
```

以及：

- 中文括号；
- 全角括号；
- 中文冒号；
- ASCII数字；
- 英文字母；
- 半角小数点；
- 全角句号；
- 001；
- 日期；
- 百分号等。

确认完全不变化。

------

# 四十、格式 Validator

重新打开生成 DOCX。

逐元素验证：

## title

- 方正小标宋简体；
- 22pt；
- center；
- 30pt fixed。

## heading_1

- 黑体；
- 16pt；
- 30pt fixed。

## heading_2

- 楷体_GB2312；
- 16pt；
- 30pt fixed。

## heading_3

- 仿宋_GB2312；
- 16pt；
- 30pt fixed。

## heading_4

- 仿宋_GB2312；
- 16pt；
- 30pt fixed。

## body

- 仿宋_GB2312；
- 16pt；
- 30pt fixed。

## attachment

- 仿宋_GB2312；
- 16pt；
- 30pt fixed。

------

# 四十一、Validator 必须检查 XML 字体

不能只检查：

```python
run.font.name
```

必须检查：

```text
w:rFonts
w:eastAsia
w:ascii
w:hAnsi
w:cs
```

以真实输出 DOCX 为准。

------

# 四十二、Validator 不能假阳性

如果 Renderer 存在任何：

- 字体没实际写；
- 字号错误；
- 行距错误；
- alignment错误；
- 内容变化；
- 空行数量错误；

Validator 必须失败。

不要为了让测试通过降低验证要求。

------

# 四十三、SKILL.md 针对 Qwen3 重写

这是本次改造的重点之一。

当前 Skill 最终运行模型较弱，因此：

SKILL.md 要：

**明确，但不要臃肿。**

不要把：

- Python架构；
- XML实现；
- 测试设计；
- 开发历史；
- 复杂理论；

全部塞给模型。

------

# 四十四、SKILL.md 推荐结构

只保留以下内容：

## 1. Skill 是干什么的

接收：

```text
Browser插件读取到的公文文本
```

生成：

```text
规范DOCX
```

------

## 2. 什么时候使用

用户要求：

- 整理公文格式；
- 规范公文；
- 按规定字体字号排版；
- 将 Browser 读取的文档转换成规范 Word。

------

## 3. 输入规则

明确：

**Browser输出的纯文本就是合法输入。**

看到纯文本不得拒绝。

不得要求重新上传 DOCX。

不得尝试访问原文件 URL。

------

## 4. 正常执行

非常明确写：

```text
步骤1：
把Browser返回的完整原始文本作为source_text传给Skill入口。

步骤2：
运行Skill。

步骤3：
如果status=SUCCESS，直接返回output_file。

不要自行再次修改文件。
```

------

## 5. NEEDS_REVIEW

如果：

```text
status=NEEDS_REVIEW
```

则：

```text
只阅读review_file中的项目。
```

对于每项：

只能从：

```text
candidate_types
```

选择一个。

生成：

```json
{
  "p0012": "heading_3"
}
```

然后调用 resume / overrides 流程。

------

## 6. 禁止事项

明确重复强调：

- 不重写全文；
- 不总结；
- 不修改文字；
- 不修改标点；
- 不修改编号；
- 不增加其他标准；
- 不自行设置格式；
- 不访问原始 DOCX URL；
- 不因为输入是文本而拒绝；
- 不跳过 Validator。

------

## 7. SUCCESS

只有程序：

```text
status=SUCCESS
```

才告诉用户完成。

直接返回生成文件。

------

# 四十五、SKILL.md 中的模型提示要“机械化”

针对较弱模型：

尽量使用：

```text
如果 A → 做 B
如果 C → 做 D
禁止 E
```

不要大量写：

```text
请综合判断……
根据情况灵活……
自行决定……
```

减少开放式推理。

------

# 四十六、格式要求不要让 Qwen3记

虽然 SKILL.md 可以简要说明目标格式，

但模型不负责格式设置。

真正格式来自：

```text
format_rules.json
+
render_docx.py
```

Qwen3 无需记住每一个字体。

这样减少上下文和执行错误。

------

# 四十七、references

只保留真正有价值的：

```text
references/format_spec.md
```

用于：

- 人工维护；
- 开发；
- 审计。

不要让 Qwen3 每次都必须读取。

如果存在大量旧 reference 文件：

检查是否与本 Skill 仍有关。

无关则删除。

------

# 四十八、AGENTS.md

更新为开发维护约束。

保持简洁。

至少包含：

- 不联网；
- 不新增依赖；
- source_text 是内容事实来源；
- renderer 永远使用 original text；
- 不允许 normalize 正文；
- 格式统一从 JSON；
- 修改后必须运行 unittest；
- 必须运行 E2E；
- Validator 不可绕过；
- 不自行增加未确认格式要求。

AGENTS.md 是给 Codex / 开发 Agent 的。

不是给 Qwen3 执行 Skill 的。

不要把两者混在一起。

------

# 四十九、README

更新为当前真实架构。

删除已经过时的：

```text
用户上传DOCX → Skill读取DOCX
```

改成：

```text
DOCX
→ HiAgent Browser
→ source_text
→ Skill
→ DOCX
```

明确说明内容完整性基准是：

```text
Browser提取文本
```

而不是原 DOCX。

------

# 五十、测试结构

推荐：

```text
test_input_adapter.py
test_classify.py
test_render_validate.py
test_e2e_browser_text.py
```

无需为了模块对应创建很多小测试文件。

------

# 五十一、input adapter 测试

测试：

- LF；
- CRLF；
- 中文；
- 英文；
- 数字；
- 全角符号；
- 全角空格；
- leading blank；
- trailing blank；
- 多个 blank；
- 非空文本完全保留。

特别验证：

```text
text
```

没有被 `.strip()` 覆盖。

------

# 五十二、分类测试

至少：

```text
一、标题
→ heading_1

（一）标题
→ heading_2

1. 标题
→ heading_3

1．标题
→ heading_3

（1）标题
→ heading_4

普通正文。
→ body

附件：1.测试
→ attachment
```

还应测试：

明显正文：

```text
1.2026年业务增长达到……
```

不要无条件识别 heading_3。

不确定时：

```text
unknown
```

------

# 五十三、浏览器真实风格 E2E Fixture

创建：

```text
samples/browser_input.txt
```

模拟 Browser 返回，而不是模拟 DOCX。

必须包含：

```text
关于进一步加强人工智能应用管理工作的通知

一、总体要求
近年来，人工智能技术快速发展，相关工作编号为AI-001，不得修改。

（一）主要任务
各单位应严格按照相关要求开展工作。

1. 加强组织管理
本项目2026年度测试编号为001。

（1）明确责任分工
相关单位应按要求完成工作，不得改变数字、中文标点及英文ABC。

附件：1.人工智能应用管理任务表
　　　2.相关工作说明
```

可以加入多余 Browser 空行测试 canonical blank policy。

------

# 五十四、E2E

真正执行：

```text
browser_input.txt
↓
main
↓
classify
↓
render
↓
validate
↓
output.docx
```

要求：

```text
SUCCESS
```

然后重新读取 DOCX。

检查所有非空文本逐字一致。

------

# 五十五、幂等性定义调整

因为正式输入来自 Browser text：

幂等测试不必再：

```text
output.docx → 重新解析
```

核心幂等性改为：

同一份：

```text
browser_input.txt
```

连续执行两次。

两个输出的：

- 非空文字；
- 分类；
- 字体；
- 字号；
- 行距；
- 空行结构；

必须完全相同。

DOCX ZIP 文件二进制不要求 byte-for-byte 相同，因为文档元数据可能变化。

------

# 五十六、Validator 负面测试

必须主动制作错误输出测试：

例如：

- 把正文改一个字；
- title 字体设错；
- 行距改成1.5倍；
- 删除空行；
- 多插一个空行；
- heading_2字号错误。

确认 Validator：

```text
FAIL
```

这是验证 Validator 真实有效的重要测试。

------

# 五十七、Qwen3 review 流程测试

人为制造一个 ambiguous line。

程序应：

```text
NEEDS_REVIEW
```

输出：

```text
review.json
```

然后测试合法：

```json
{
  "pXXXX": "heading_3"
}
```

可以成功继续。

测试非法类型：

```json
{
  "pXXXX": "heading_1"
}
```

如果 candidate_types 不包含 heading_1：

必须：

```text
INVALID_OVERRIDE
```

------

# 五十八、不要把大模型调用写进 Python

Python 不调用：

- Qwen；
- OpenAI；
- DeepSeek；
- 任何 HTTP LLM。

Skill 平台上的 Qwen3 自己负责 review。

Python 只产生：

```text
NEEDS_REVIEW + candidate_types
```

------

# 五十九、结果 JSON

最终结果保持小而清晰。

SUCCESS：

```json
{
  "status": "SUCCESS",
  "source_type": "browser_text",
  "output_file": "...",
  "validation_passed": true,
  "verified_against": "browser_extracted_text"
}
```

NEEDS_REVIEW：

```json
{
  "status": "NEEDS_REVIEW",
  "review_file": "...",
  "review_count": 1
}
```

不要往 stdout 打印正文。

------

# 六十、安全

整个项目：

- 不联网；
- 不上传任何内容；
- 不写第三方API；
- 不保存长期敏感内容；
- 不在日志打印全文；
- 临时文件限定当前工作目录；
- 不访问 Browser 原文件URL；
- 不下载原始DOCX。

------

# 六十一、本轮不做的功能

明确不做：

- 原DOCX格式保留；
- 图片；
- 表格；
- 页眉页脚；
- 多Section；
- PDF；
- OCR；
- HTML解析；
- Markdown解析；
- RAG；
- 知识库；
- 多preset；
- 内容纠错；
- 自动编号修复；
- 标点规范；
- Word模板导入。

原因：

HiAgent Browser 已经把当前业务需要转换成可靠文本。

这些功能只会增加当前 Skill 复杂度。

------

# 六十二、兼容现有项目

请首先查看：

```text
git status
git diff
当前目录结构
当前测试
当前SKILL.md
当前main入口
```

不要机械地全部重写。

保留：

- 已经正确的 renderer；
- 已经正确的字体 XML；
- 已经正确的 validator；
- 已经正确的 format_rules；
- 有价值的 tests。

删除：

只服务旧 DOCX input 架构的代码。

------

# 六十三、实现顺序

请严格按照：

## Phase 1

审计现有项目。

输出到你的内部计划中：

- 保留什么；
- 删除什么；
- 修改什么；
- 新增什么。

然后开始实施。

不要停下来只让我确认计划。

------

## Phase 2

改造 input adapter + main。

先跑相关测试。

------

## Phase 3

改造 classification。

减少 Qwen review。

运行分类测试。

------

## Phase 4

确认 renderer 满足新 Browser 输入架构。

重点：

- original text；
- exact blanks；
- exact 30pt；
- fonts。

------

## Phase 5

重构 validator。

ground truth 改：

```text
browser_extracted_text
```

------

## Phase 6

重写 SKILL.md。

重点针对 Qwen3。

------

## Phase 7

清理旧文件。

不要留下误导下一位维护人员的死代码。

------

## Phase 8

运行：

```bash
python -m unittest discover -s tests -v
```

所有测试必须通过。

------

## Phase 9

运行真实 E2E CLI：

```text
samples/browser_input.txt
→ output.docx
```

必须：

```text
SUCCESS
```

------

## Phase 10

主动破坏一个生成文件。

确认 Validator 真正能够：

```text
FAIL
```

然后删除该破坏文件。

------

## Phase 11

模拟 Qwen3 NEEDS_REVIEW 流程。

确认：

- review简洁；
- candidate_types有限；
- override简单；
- 非法override被拒绝。

------

## Phase 12

审阅：

```text
git diff
```

重点搜索：

```text
strip(
replace(
re.sub
normalize
source_file
.docx input
mammoth
BeautifulSoup
document.md
```

确认没有危险或过时逻辑。

注意：

`.strip()` 可以用于 analysis_text。

但不能覆盖 original text。

------

# 六十四、部署 ZIP

最终重新生成：

```text
dist/gongwen-format-skill.zip
```

部署 ZIP 只包含运行必需：

```text
SKILL.md
README.md
config/
references/
scripts/
```

如果平台 Skill 规范还要求其他已有元数据文件，则保留。

不要包含：

```text
tests/
samples/
.git/
__pycache__/
work/
临时输出
```

ZIP 根目录直接存在：

```text
SKILL.md
```

不要多套一层目录。

------

# 六十五、最终完成条件

只有同时满足以下条件才完成：

### 输入

Browser纯文本能够直接作为合法输入。

不会再说：

```text
输入不是DOCX
```

### 正常路径

规范公文：

```text
一次调用
→ SUCCESS
```

不需要Qwen额外干预。

### 内容

Browser非空文本：

```text
==
输出DOCX非空文本
```

逐字符一致。

### 格式

title：
方正小标宋简体 / 22pt / center。

heading_1：
黑体 / 16pt。

heading_2：
楷体_GB2312 / 16pt。

heading_3：
仿宋_GB2312 / 16pt。

heading_4：
仿宋_GB2312 / 16pt。

body：
仿宋_GB2312 / 16pt。

attachment：
仿宋_GB2312 / 16pt。

全文：

fixed 30pt。

### 空白

title后：

exactly one blank paragraph。

attachment前：

exactly one blank paragraph。

其他Browser空行不复制。

### Qwen3

正常情况无需模型分类。

真正歧义才：

NEEDS_REVIEW。

一次Review。

候选类型有限。

只返回：

paragraph_id → type。

### Validator

能够：

- 检测正文变化；
- 检测字体错误；
- 检测字号错误；
- 检测行距错误；
- 检测空行错误。

### 依赖

不新增任何第三方依赖。

### ZIP

最终部署ZIP正确生成。

------

# 六十六、最终报告

完成后请不要只说：

“修改完成，测试通过。”

请给我：

1. 改造前后的最终架构对比；
2. 删除了哪些旧文件以及为什么；
3. 新增了哪些文件；
4. 最终目录树；
5. 核心脚本职责；
6. SKILL.md针对Qwen3做了哪些简化；
7. unittest实际测试数量和结果；
8. Browser Text E2E结果；
9. 输入/输出非空文本是否逐字符一致；
10. 主标题实际 eastAsia 字体、字号、alignment；
11. 一级标题实际字体字号；
12. 二级标题实际字体字号；
13. 三级/四级标题实际字体字号；
14. 正文实际字体字号；
15. 实际检测到的行距；
16. title后空行数量；
17. attachment前空行数量；
18. Validator负面测试结果；
19. NEEDS_REVIEW模拟结果；
20. 当前仍然存在的限制；
21. 最终ZIP路径。

如果测试中发现 Bug：

直接继续修复。

不要降低验收标准。

不要为了保留旧代码牺牲最终架构简单性。

最终目标：

**得到一个专门适配 HiAgent Browser 纯文本输入、对 Qwen3 执行负担低、依靠 Python 确定性规则生成规范 DOCX、并通过严格 Validator 防止正文和格式错误的可靠公文格式整理 Skill。**