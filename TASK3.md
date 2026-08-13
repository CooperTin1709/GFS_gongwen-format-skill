# 公文格式整理 Skill —— 首行缩进、称谓、落款、数字字体增量改造任务

你现在正在一个已经可以正常运行并通过 HiAgent Browser 纯文本输入进行公文格式整理的 Skill 项目中工作。

当前项目已经基本完成：

```text
Browser纯文本
→ input_adapter
→ classify
→ render_docx
→ validate
→ 输出规范DOCX
```

本轮是一次**增量功能修改**。

不要创建新项目。
不要创建 v2。
不要复制新 Skill。
不要推翻现有 Browser Text 架构。
不要重新引入 DOCX 输入、Markdown、Mammoth、RAG、知识库等已删除的旧方案。

请先审计当前实现，然后直接修改现有代码、配置、SKILL.md 和测试。

完成后必须真实运行全部 unittest、E2E、Validator 负面测试，并检查生成 DOCX XML。

------

# 一、本轮新增需求

在当前已有格式要求基础上新增以下 3 类规则：

## 1. 首行缩进

除以下特殊段落外：

- 开头称谓；
- 居中的主标题；
- 居右的落款；

其余主要公文内容均增加：

```text
首行缩进 2 个中文字符
```

具体应用到：

```text
heading_1
heading_2
heading_3
heading_4
body
attachment
```

例如：

```text
一、一级标题
　　正文……
（一）二级标题
　　正文……
1. 三级标题
　　正文……
（1）四级标题
　　正文……
```

注意：

**不要通过在文字前插入两个全角空格实现。**

必须使用 Word Paragraph 的真正首行缩进属性。

原始 `text` 字符串不得发生变化。

------

# 二、两字符缩进的实现原则

优先实现真正的 Word：

```text
首行缩进 2 字符
```

而不是简单写死一个视觉上大约相等的空格。

如果使用 OOXML，可检查并正确设置：

```text
<w:ind w:firstLineChars="200"/>
```

其中 200 表示 2.00 个字符。

同时应清理可能冲突的：

```text
w:firstLine
w:hanging
w:hangingChars
```

具体实现请根据当前项目结构选择最稳定方案。

如果 python-docx 的公开 API 无法直接设置字符单位，可使用其自带 XML API：

```python
docx.oxml
docx.oxml.ns.qn
```

不要新增依赖。

Validator 必须真正重新打开 DOCX 并检查 XML 中首行缩进，而不是只检查配置文件。

------

# 三、缩进策略必须配置化

不要把：

```text
2
```

大量硬编码在 renderer 中。

修改：

```text
config/format_rules.json
```

加入类似：

```json
{
  "global": {
    "line_spacing_pt": 30,
    "digit_font": "Times New Roman"
  },
  "heading_1": {
    "first_line_indent_chars": 2
  },
  "heading_2": {
    "first_line_indent_chars": 2
  },
  "heading_3": {
    "first_line_indent_chars": 2
  },
  "heading_4": {
    "first_line_indent_chars": 2
  },
  "body": {
    "first_line_indent_chars": 2
  },
  "attachment": {
    "first_line_indent_chars": 2
  }
}
```

具体 JSON schema 可结合当前已有结构调整。

特殊元素：

```text
title
salutation
signature
```

设置：

```text
first_line_indent_chars = 0
```

或明确配置为不应用首行缩进。

不要依赖 renderer 中零散的 if type == xxx 特例。

------

# 四、增加“称谓”类型

当前文档开头可能存在称谓，例如：

```text
行领导：
XX部门：
各部门：
各位领导：
```

这种段落属于：

```text
salutation
```

新增分类类型：

```text
salutation
```

------

# 五、称谓格式

称谓：

- 字体：仿宋_GB2312；
- 字号：三号；
- 16 pt；
- 固定值30磅行距；
- 左对齐；
- 首行缩进：0。

最关键规则：

> 称谓不能进行两字符首行缩进。

称谓的原始文字不得修改。

例如：

```text
行领导：
```

输出仍必须是逐字：

```text
行领导：
```

不能自动增加：

```text
　　行领导：
```

不能删除冒号。

不能转换中英文冒号。

------

# 六、称谓识别规则

优先通过确定性规则识别，尽量不要交给 Qwen3。

高置信度称谓通常满足：

1. 位于文档开头区域；
2. 是较短的独立段落；
3. 以：

```text
：
:
```

结束；

1. 内容明显像收文对象或称呼；
2. 不属于附件；
3. 不属于标题编号；
4. 不像正常完整正文。

例如：

```text
行领导：
XX部门：
各部门：
各位领导：
各位同事：
```

应尽量直接识别：

```text
salutation
```

------

# 七、避免误识别称谓

不能看到所有：

```text
xxx：
```

都认定为 salutation。

例如正文：

```text
具体要求如下：
```

很可能只是普通正文。

因此还应结合：

- 是否位于文档前几个非空段落；
- 是否位于正文主体开始前；
- 文本长度；
- 上下文；
- 是否为典型称谓形式。

如果无法高置信度判断：

```text
candidate_types = ["salutation", "body"]
```

进入 NEEDS_REVIEW。

不要强猜。

------

# 八、增加“落款”类型

文档结尾如果存在落款，例如：

```text
XX部门
XX银行XX分行
2026年8月11日
```

或：

```text
XX部门
2026年8月11日
```

应识别为：

```text
signature
```

新增分类类型：

```text
signature
```

不需要进一步拆成：

```text
signature_org
signature_date
```

第一版统一使用：

```text
signature
```

保持类型集合简单。

------

# 九、落款格式

所有 signature 段落：

- 字体：仿宋_GB2312；
- 字号：三号；
- 16pt；
- 固定值30磅；
- 右对齐；
- 不额外增加首行缩进。

也就是说：

```text
alignment = right
first_line_indent = 0
```

因为落款的版式主要由右对齐决定。

不要为了满足普通正文的两字符缩进，再把右对齐落款额外向右偏移。

------

# 十、落款识别原则

落款只允许在：

```text
文档末尾区域
```

识别。

不要把正文中间的单位名称识别成 signature。

强特征之一是结尾日期。

至少支持以下日期候选：

```text
2026年8月11日
2026年08月11日
```

以及合理的中文数字日期，例如：

```text
二〇二六年八月十一日
```

如果文档最后一个非空段落明显是日期：

可以高置信度分类为：

```text
signature
```

------

# 十一、单位名称 + 日期的落款

典型：

```text
XX部门
2026年8月11日
```

如果最后一段为高置信度日期：

可以检查它前一个非空段落。

如果该段：

- 较短；
- 不以 `。！？；` 等完整句结束；
- 不是标题；
- 不是附件编号；
- 位于日期紧前面；

可以将：

```text
XX部门
```

和日期一起识别为：

```text
signature
```

------

# 十二、只有单位名称、没有日期时

例如最后只有：

```text
XX部门
```

这种情况不应单凭“位于结尾”就高置信度认定落款。

如果无法确定：

```text
candidate_types = ["signature", "body"]
```

进入：

```text
NEEDS_REVIEW
```

让 Qwen3 只选择类型。

避免把正文最后一句错误地右对齐。

------

# 十三、Qwen3 对 salutation / signature 的判断提示

更新 SKILL.md。

如果 review 中：

```text
candidate_types = ["salutation", "body"]
```

告诉模型：

```text
salutation = 文档开头用于称呼收文对象的独立短段，
典型如“行领导：”“XX部门：”。
如果只是正文中的“具体要求如下：”，应选择body。
```

如果：

```text
candidate_types = ["signature", "body"]
```

告诉模型：

```text
signature = 文档结尾的署名、单位名称或落款日期。
普通正文最后一句仍选择body。
```

Qwen3 仍然只允许返回：

```json
{
  "p0012": "signature"
}
```

不得重新输出 text。

------

# 十四、所有阿拉伯数字使用 Times New Roman

新增严格格式要求：

> 文档中的所有阿拉伯数字使用 Times New Roman。

包括但不限于：

```text
1
2
2026
001
100
3.14 中的数字字符
AI-001 中的001
1. 一级编号中的1
（1）四级编号中的1
2026年8月11日中的所有数字
```

------

# 十五、“数字”的严格定义

本轮“数字”定义为：

半角阿拉伯数字：

```text
0 1 2 3 4 5 6 7 8 9
```

同时为了鲁棒性，可以支持全角数字：

```text
０１２３４５６７８９
```

中文数字：

```text
一
二
三
十
百
〇
```

属于中文字符。

不要设置为 Times New Roman。

例如：

```text
一、总体要求
```

其中：

```text
一
```

继续使用一级标题的：

```text
黑体
```

而：

```text
1. 总体要求
```

其中：

```text
1
```

使用：

```text
Times New Roman
```

------

# 十六、不要修改字符本身

数字字体修改：

**只能改变字体。**

不能：

```text
０ → 0
```

不能：

```text
001 → 1
```

不能：

```text
2026年8月11日
→
2026-08-11
```

不能修改小数点、括号、百分号等字符。

原始文本必须逐字符保持一致。

------

# 十七、实现数字字体的正确方法

当前 renderer 如果采用：

```text
一个paragraph
+
一个run
```

本轮需要调整。

因为同一段可能同时存在：

```text
中文
+
数字
```

例如：

```text
本项目2026年度编号为AI-001。
```

目标：

```text
本项目          → 仿宋_GB2312
2026            → Times New Roman
年度编号为AI-   → 仿宋_GB2312
001             → Times New Roman
。              → 仿宋_GB2312
```

------

# 十八、需要安全拆分 Run

实现一个确定性文本分段函数。

例如：

```python
split_text_by_digit_runs(text)
```

或更通用：

```python
add_formatted_text_runs(...)
```

功能：

将：

```text
本项目2026年度编号为AI-001。
```

按照字符类型拆为：

```text
["本项目", "2026", "年度编号为AI-", "001", "。"]
```

或等价结构。

连续数字尽量组成一个 Run。

不能逐字符建立几千个 Run，避免低效。

------

# 十九、拆 Run 时的最高约束

Renderer 最终：

```text
"".join(run.text for run in paragraph.runs)
```

必须严格等于：

```text
original text
```

逐字符一致。

不得：

- strip；
- normalize；
- replace；
- Unicode转换；
- 自动空格；
- 标点调整。

------

# 二十、数字 Run 字体

数字 Run：

```text
font = Times New Roman
```

应正确设置：

```text
w:ascii
w:hAnsi
w:eastAsia
w:cs
```

都为：

```text
Times New Roman
```

因为该 Run 中只包含数字。

字号：

继续继承当前段落类型的字号。

当前所有普通正文/标题层级都是：

```text
16pt
```

主标题如果包含数字：

数字仍然：

```text
Times New Roman
22pt
```

不要因为数字字体而错误地把字号统一成16pt。

------

# 二十一、非数字 Run 字体

根据 paragraph classification：

## title

```text
方正小标宋简体
```

## salutation

```text
仿宋_GB2312
```

## heading_1

```text
黑体
```

## heading_2

```text
楷体_GB2312
```

## heading_3

```text
仿宋_GB2312
```

## heading_4

```text
仿宋_GB2312
```

## body

```text
仿宋_GB2312
```

## attachment

```text
仿宋_GB2312
```

## signature

```text
仿宋_GB2312
```

数字 Run 是这些字体规则之上的覆盖规则：

```text
digit font override > paragraph base font
```

但：

```text
字号
行距
alignment
indent
```

仍由 paragraph 类型决定。

------

# 二十二、不要错误处理标点

例如：

```text
1. 加强组织管理
```

只要求：

```text
1
```

使用 Times New Roman。

`.` 字符本身不要因为实现方便而修改。

同样：

```text
（1）明确工作职责
```

只要求数字：

```text
1
```

Times New Roman。

中文括号：

```text
（ ）
```

继续采用该段落基础字体。

------

# 二十三、配置文件增加 digit_font

在：

```text
config/format_rules.json
```

增加：

```json
{
  "global": {
    "digit_font": "Times New Roman"
  }
}
```

不要在 renderer 中到处写死：

```text
Times New Roman
```

Validator 也读取同一份规则。

------

# 二十四、最终 paragraph 类型集合

本轮建议正式固定为：

```text
title
salutation
heading_1
heading_2
heading_3
heading_4
body
attachment
signature
unknown
```

不要再扩展更多类型。

------

# 二十五、最终格式规则

完整有效规则现在是：

## title

```text
方正小标宋简体
22pt
居中
固定30磅
首行缩进0
```

数字：

```text
Times New Roman
22pt
```

标题后：

```text
恰好空一行
```

------

## salutation

```text
仿宋_GB2312
16pt
左对齐
固定30磅
首行缩进0
```

数字：

```text
Times New Roman
16pt
```

------

## heading_1

```text
黑体
16pt
固定30磅
首行缩进2字符
```

数字：

```text
Times New Roman
16pt
```

------

## heading_2

```text
楷体_GB2312
16pt
固定30磅
首行缩进2字符
```

数字：

```text
Times New Roman
16pt
```

------

## heading_3

```text
仿宋_GB2312
16pt
固定30磅
首行缩进2字符
```

数字：

```text
Times New Roman
16pt
```

------

## heading_4

```text
仿宋_GB2312
16pt
固定30磅
首行缩进2字符
```

数字：

```text
Times New Roman
16pt
```

------

## body

```text
仿宋_GB2312
16pt
固定30磅
首行缩进2字符
```

数字：

```text
Times New Roman
16pt
```

------

## attachment

```text
仿宋_GB2312
16pt
固定30磅
首行缩进2字符
```

数字：

```text
Times New Roman
16pt
```

附件前：

```text
恰好空一行
```

------

## signature

```text
仿宋_GB2312
16pt
右对齐
固定30磅
首行缩进0
```

数字：

```text
Times New Roman
16pt
```

------

# 二十六、空白 Paragraph

规定插入的空白 Paragraph：

- title 后 1 个；
- attachment 前 1 个。

空白 Paragraph：

```text
固定30磅行距
```

没有文字，因此：

- 不需要数字字体；
- 不需要首行缩进。

不要对 blank 设置：

```text
firstLineChars=200
```

------

# 二十七、Validator 增强：首行缩进

validate.py 必须增加：

```text
indent validation
```

逐类检查。

应有：

```text
heading_1 → 2字符
heading_2 → 2字符
heading_3 → 2字符
heading_4 → 2字符
body → 2字符
attachment → 2字符
```

以及：

```text
title → 0
salutation → 0
signature → 0
blank → 0
```

优先直接检查生成 DOCX XML：

```text
<w:ind ...>
```

确保目标类型真正是：

```text
w:firstLineChars="200"
```

或项目最终选择的等价正确实现。

------

# 二十八、Validator 增强：alignment

增加：

```text
title = center
salutation = left
signature = right
```

特别确认 signature 真正：

```text
WD_ALIGN_PARAGRAPH.RIGHT
```

而不是通过空格模拟右对齐。

禁止：

```text
"                       XX部门"
```

这种实现。

------

# 二十九、Validator 增强：数字字体

重新打开生成 DOCX。

遍历所有非空 paragraph 的所有 Run。

只要 Run 中包含阿拉伯数字：

应验证这些数字所在 Run：

```text
Times New Roman
```

同时必须验证：

```text
w:ascii
w:hAnsi
w:eastAsia
w:cs
```

均正确声明。

------

# 三十、最好增加更严格的 Run Validator

Renderer 应保证：

```text
数字 Run
```

中只包含数字。

不要出现：

```text
"2026年度"
```

整个 Run 都变 Times New Roman。

Validator 可以检查：

如果某 Run 使用：

```text
Times New Roman
```

且它本应由数字字体覆盖产生，

其文字应该全部属于：

```text
[0-9０-９]+
```

否则提示：

```text
digit font run contains non-digit characters
```

避免错误地把中文一起改为 Times New Roman。

------

# 三十一、内容完整性仍然是最高约束

原输入 canonical paragraphs 的：

```text
所有非空 text
```

与输出 DOCX 的：

```text
所有非空 paragraph.text
```

必须：

- 数量一致；
- 顺序一致；
- 逐字符一致。

新增 salutation、signature 和数字 Run 后仍然不能放宽这一规则。

------

# 三十二、增加测试：首行缩进

新增或扩展测试：

```text
test_indent_policy
```

至少验证：

```text
heading_1
heading_2
heading_3
heading_4
body
attachment
```

全部实际为：

```text
2字符
```

同时：

```text
title
salutation
signature
```

不缩进。

不要只测试配置值。

必须检查生成 DOCX XML。

------

# 三十三、增加测试：称谓

测试：

```text
行领导：
```

应识别：

```text
salutation
```

格式：

```text
仿宋_GB2312
16pt
left
0 indent
30pt fixed
```

再测试：

```text
具体要求如下：
```

位于正文中间时：

不能自动识别为 salutation。

------

# 三十四、增加测试：落款

至少测试：

```text
XX部门
2026年8月11日
```

位于文末。

应识别：

```text
signature
signature
```

两个段落均：

```text
right
仿宋_GB2312
16pt
30pt fixed
```

日期中的：

```text
2026
8
11
```

必须 Times New Roman。

------

# 三十五、增加测试：无日期落款歧义

例如：

```text
正文最后一句。
XX部门
```

如果程序不能高置信度判断：

返回：

```text
NEEDS_REVIEW
```

并且：

```text
candidate_types = ["signature", "body"]
```

不要无脑将最后一行右对齐。

------

# 三十六、增加测试：所有数字 Times New Roman

E2E fixture 至少包含：

```text
关于2026年度工作安排的通知

行领导：

一、2026年度总体要求
项目编号为AI-001，完成率为100%。

（一）第2阶段任务
计划于2026年8月11日前完成。

1. 完成第3轮测试
测试编号001。

（1）处理第4类问题
相关指标为3.14。

附件：1.2026年度任务表
　　　2.测试说明

XX部门
2026年8月11日
```

注意：

这里的原始文字只用于测试。

不得在最终 Skill 中硬编码。

------

# 三十七、数字字体测试要求

实际重新打开输出 DOCX。

验证至少：

```text
2026
001
100
2
8
11
1
3
4
3
14
```

所有数字字符都位于 Times New Roman Run 中。

同时检查：

```text
年度
项目编号
AI-
完成率
%
年
月
日
```

不能因为邻近数字被错误设置为 Times New Roman。

------

# 三十八、测试标题编号

必须专门验证：

```text
1. 完成第3轮测试
```

最终 Run 至少逻辑等价于：

```text
"1" → Times New Roman
". 完成第" → 仿宋_GB2312
"3" → Times New Roman
"轮测试" → 仿宋_GB2312
```

不要求 Run 必须恰好如此拆分。

但字体结果必须等价。

------

# 三十九、测试四级标题

例如：

```text
（1）处理第4类问题
```

要求：

```text
（ → 仿宋_GB2312
1 → Times New Roman
）处理第 → 仿宋_GB2312
4 → Times New Roman
类问题 → 仿宋_GB2312
```

同时原：

```text
（1）处理第4类问题
```

必须逐字符保持不变。

------

# 四十、测试主标题中的数字

例如：

```text
关于2026年度工作的通知
```

要求：

中文：

```text
方正小标宋简体
22pt
```

数字：

```text
Times New Roman
22pt
```

整个段落：

```text
center
30pt fixed
```

------

# 四十一、测试落款日期

```text
2026年8月11日
```

最终：

```text
2026 → Times New Roman
年 → 仿宋_GB2312
8 → Times New Roman
月 → 仿宋_GB2312
11 → Times New Roman
日 → 仿宋_GB2312
```

整个 paragraph：

```text
right
16pt
30pt fixed
```

------

# 四十二、Validator 负面测试

主动构造以下错误并确认 FAIL：

## 错误1

正文首行缩进为 0。

必须：

```text
VALIDATION_FAILED
```

## 错误2

salutation 被缩进 2 字符。

必须失败。

## 错误3

signature 左对齐。

必须失败。

## 错误4

signature 使用宋体。

必须失败。

## 错误5

数字：

```text
2026
```

仍使用仿宋_GB2312。

必须失败。

## 错误6

为了 Times New Roman 修改了：

```text
AI-001
```

文本。

必须失败。

------

# 四十三、幂等性

同一 Browser source_text 连续处理两次。

两次输出：

- 非空文字；
- classification；
- paragraph alignment；
- indentation；
- 字体；
- 数字Run；
- 字号；
- 行距；
- canonical blank structure；

必须一致。

DOCX ZIP 二进制不要求 byte-for-byte 一致。

------

# 四十四、SKILL.md 更新

针对 Qwen3 更新，但不要大幅变长。

新增它需要知道的只有：

## salutation

开头称谓：

```text
行领导：
XX部门：
```

属于：

```text
salutation
```

只有 review 时才需要模型判断。

------

## signature

文末：

```text
单位名称
日期
```

属于：

```text
signature
```

只有程序无法判断时模型才 review。

------

# 四十五、Qwen3 不负责格式

SKILL.md 不要要求 Qwen3：

- 自己设置首行缩进；
- 自己找数字；
- 自己设置 Times New Roman；
- 自己右对齐；
- 自己判断字号。

这些全部由 Python 实现。

模型只处理：

```text
ambiguous classification
```

------

# 四十六、README 和 format_spec 更新

更新：

```text
README.md
references/format_spec.md
```

记录最新需求：

1. 一级至四级标题、正文、附件首行缩进2字符；
2. 称谓不缩进；
3. 主标题保持居中；
4. 落款右对齐，不增加首行缩进；
5. 落款仿宋_GB2312、三号；
6. 所有阿拉伯数字 Times New Roman；
7. 全文固定30磅。

不要加入其他未要求标准。

------

# 四十七、AGENTS.md 更新

只增加必要维护约束：

```text
数字字体只能通过Run级格式实现，不得修改文字；
首行缩进必须使用Word段落属性，不得插入空格；
signature必须右对齐；
salutation不得缩进；
新增规则后Validator必须同步更新。
```

保持简洁。

------

# 四十八、代码重构原则

本轮允许合理重构：

如果当前：

```text
render_docx.py
```

已经变得复杂，可以抽取：

```text
docx_utils.py
```

用于：

- 字体设置；
- 数字 Run 拆分；
- 首行缩进 XML；
- 行距设置；
- XML读取。

但只在确有复用价值时增加。

不要拆成十几个模块。

目标仍然控制在：

```text
5~7个核心Python文件
```

------

# 四十九、不要增加新依赖

仍然只允许：

```text
Python标准库
python-docx
```

禁止：

```text
pip install
网络访问
外部API
```

------

# 五十、实施顺序

请按以下顺序工作。

## Phase 1：审计

检查：

```text
git status
git diff
format_rules.json
classify.py
render_docx.py
validate.py
SKILL.md
当前tests
```

确认现有实现。

------

## Phase 2：配置

先扩展：

```text
format_rules.json
```

加入：

```text
digit_font
indent policy
salutation
signature
```

------

## Phase 3：分类

扩展：

```text
salutation
signature
```

优先规则判断。

真正歧义才 NEEDS_REVIEW。

------

## Phase 4：Renderer

实现：

```text
2字符真正首行缩进
signature right alignment
salutation zero indent
digit Run splitting
Times New Roman digits
```

------

## Phase 5：Validator

同步实现严格验证。

不能只改 Renderer 不改 Validator。

------

## Phase 6：测试

补全：

```text
indent
salutation
signature
digit font
mixed run
negative validator
E2E
```

------

## Phase 7：完整测试

运行：

```bash
python -m unittest discover -s tests -v
```

全部通过。

------

## Phase 8：真实 E2E

使用新的 Browser Text fixture：

```text
source_text
→ process
→ output.docx
→ validate
```

必须：

```text
SUCCESS
```

------

## Phase 9：真实 XML 检查

不要只相信 unittest。

实际打开生成 DOCX ZIP/XML 或使用 python-docx + OXML。

确认：

### heading/body

```text
firstLineChars = 200
```

### salutation/signature/title

不存在错误2字符首行缩进。

### signature

```text
alignment = right
```

### digits

```text
Times New Roman
```

------

## Phase 10：Validator破坏测试

主动制造：

- 错缩进；
- 错数字字体；
- 错落款alignment；

确认 Validator FAIL。

------

## Phase 11：审阅

执行：

```text
git diff
```

搜索：

```text
"  " + text
"\u3000\u3000" + text
strip(
replace(
re.sub(
Times New Roman
first_line_indent
firstLineChars
```

确认：

不存在：

```text
通过插空格实现首行缩进
```

并确认：

所有正文 normalize 操作只用于 analysis_text，不覆盖 original text。

------

# 五十一、最终验收条件

只有以下全部满足才能宣布完成。

## 内容

Browser source_text 非空段落与输出 DOCX：

```text
逐字符一致
顺序一致
```

------

## title

```text
方正小标宋简体
22pt
center
30pt fixed
no first-line indent
```

其中阿拉伯数字：

```text
Times New Roman
22pt
```

------

## salutation

```text
仿宋_GB2312
16pt
left
30pt fixed
no first-line indent
```

------

## heading_1

```text
黑体
16pt
30pt fixed
2-char first-line indent
```

------

## heading_2

```text
楷体_GB2312
16pt
30pt fixed
2-char first-line indent
```

------

## heading_3

```text
仿宋_GB2312
16pt
30pt fixed
2-char first-line indent
```

------

## heading_4

```text
仿宋_GB2312
16pt
30pt fixed
2-char first-line indent
```

------

## body

```text
仿宋_GB2312
16pt
30pt fixed
2-char first-line indent
```

------

## attachment

```text
仿宋_GB2312
16pt
30pt fixed
2-char first-line indent
```

附件前：

```text
exactly one blank paragraph
```

------

## signature

```text
仿宋_GB2312
16pt
right
30pt fixed
no extra first-line indent
```

------

## all Arabic digits

无论位于：

- title；
- salutation；
- heading；
- body；
- attachment；
- signature；

均：

```text
Times New Roman
```

但字号继承所在 paragraph 类型。

------

# 五十二、最终输出报告

完成后不要只说测试通过。

请报告：

1. 修改了哪些文件；
2. 是否新增文件；
3. 最终 classification 类型；
4. 两字符缩进具体如何实现；
5. 是否真正使用 `firstLineChars=200` 或等价 Word 字符缩进；
6. salutation 如何识别；
7. signature 如何识别；
8. ambiguous signature 如何进入 NEEDS_REVIEW；
9. 数字 Run 如何拆分；
10. 是否确认拆 Run 后 paragraph.text 逐字符不变；
11. 数字实际 Times New Roman XML 检查结果；
12. title实际格式；
13. salutation实际格式；
14. heading_1~4实际缩进；
15. body实际缩进；
16. signature实际right alignment；
17. signature数字日期字体；
18. unittest实际数量；
19. unittest结果；
20. E2E结果；
21. Validator负面测试结果；
22. 幂等性结果；
23. 当前仍存在的限制；
24. 最终部署ZIP路径。

测试失败就继续修复。

不要降低验收标准。

最终目标：

**在现有 HiAgent Browser 文本输入 Skill 基础上，可靠增加“两字符首行缩进、开头称谓例外、文末落款右对齐、所有阿拉伯数字 Times New Roman”能力，同时继续保证原始文字逐字符不变。**