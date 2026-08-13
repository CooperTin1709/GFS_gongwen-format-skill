# HiAgent 公文格式整理 Skill —— 落款识别/右对齐与全文段前段后 0 磅增量修复

你现在位于一个已经基本可用的“HiAgent Browser 纯文本 → 规范公文 DOCX”Skill 项目中。

当前 Skill 已经实现并验证了大部分功能，包括：

- HiAgent Browser 纯文本输入；
- 原始非空文字内容保护；
- 主标题识别与格式；
- 称谓识别；
- 一级至四级标题识别；
- 正文格式；
- 附件处理；
- 全文固定值 30 磅行距；
- 一级至四级标题、正文、附件首行缩进 2 字符；
- 称谓不缩进；
- 阿拉伯数字 Times New Roman；
- 中文字体 Run 级正确设置；
- Validator；
- NEEDS_REVIEW；
- Qwen3 低负担执行流程；
- Browser Text E2E。

本轮只针对真实运行中发现的两个问题进行修复，并允许为解决根因进行小范围合理重构。

不要创建新项目。
不要创建 v2。
不要重新引入 DOCX 输入架构。
不要重新引入 Markdown、Mammoth、RAG、知识库等已经不需要的设计。
不要破坏当前已经正常工作的功能。

------

# 一、本轮真实问题

## 问题 1：文末落款仍然没有正确右对齐

真实 Browser 文本结尾类似：

```text
数据管理部
2025年X月X日
```

实际生成 DOCX 中出现：

```text
数据管理部
```

被错误设置为：

```text
居中
```

而：

```text
2025年X月X日
```

被错误设置为：

```text
左对齐
首行缩进2字符
```

正确结果必须是：

```text
数据管理部
2025年X月X日
```

两个段落都属于：

```text
signature
```

并统一：

```text
仿宋_GB2312
三号
16pt
固定值30磅
段前0磅
段后0磅
右对齐
首行缩进0
```

其中所有阿拉伯数字仍然：

```text
Times New Roman
```

------

# 二、重要背景：不要依赖原 DOCX 的右对齐信息

HiAgent 当前链路是：

```text
原DOCX
→ Browser
→ 纯文本
→ Skill
```

Browser 提取文本后：

**原 Word 中“这个段落原本居右”的格式信息已经不存在。**

因此：

不能依赖原 DOCX alignment 判断落款。

必须依据：

```text
文本内容
+
文档末尾位置
+
上下文结构
```

确定性识别 signature。

------

# 三、落款识别应改为“文末结构识别”

建议不要只在普通逐段 Regex 分类中顺手判断 signature。

为了提高准确率和降低 Qwen3 负担，请考虑采用：

```text
第一遍基础分类
+
第二遍 tail signature post-processing
```

即：

```text
Browser Text
↓
基础分类：
title
salutation
heading_1
heading_2
heading_3
heading_4
body
attachment
...
↓
对最后若干非空段落单独进行落款结构识别
↓
必要时覆盖为 signature
```

这是推荐的小范围架构优化。

不要因此重写整个 classifier。

------

# 四、落款日期强识别

文档末尾如果出现日期，应作为强 signature 信号。

至少支持：

## 阿拉伯数字日期

```text
2025年8月12日
2025年08月12日
2025 年 8 月 12 日
2025年8月12日
```

合理允许空格差异。

## 中文数字日期

例如：

```text
二〇二五年八月十二日
二○二五年八月十二日
```

## 测试/模板式日期

为了增强鲁棒性，也允许测试 fixture 中类似：

```text
2025年X月X日
2025年x月x日
2025年XX月XX日
XXXX年XX月XX日
```

但这些只是格式测试兼容。

不要修改这些字符。

例如输入：

```text
2025年x月x日
```

输出仍然逐字符：

```text
2025年x月x日
```

不能自动替换成真实日期。

------

# 五、日期识别范围必须限制在文末

不能看到正文中的：

```text
项目计划于2025年8月12日完成。
```

就认定为 signature。

日期 signature 必须结合：

```text
位于文档最后若干个非空段落
+
整段主要表现为日期
```

建议：

只扫描最后：

```text
3～5个非空段落
```

具体数量可以配置或使用小常量。

日期 Regex 应尽量匹配：

**整个 analysis_text**

而不是正文中只要出现日期就匹配。

------

# 六、单位名称 + 日期组合识别

最重要场景：

```text
数据管理部
2025年8月12日
```

如果：

最后一个非空段落被高置信度识别为日期 signature，

则检查它前面的非空段落。

如果前一个段落满足：

- 文本较短；
- 不以 `。！？；` 等明显完整句标点结尾；
- 不是一级至四级标题；
- 不是附件编号；
- 不是主标题；
- 不是称谓；
- 看起来像组织/单位/部门名称；
- 紧邻日期；

则：

```text
数据管理部
```

也应高置信度归类：

```text
signature
```

这样：

```text
数据管理部
2025年8月12日
```

两行都成为 signature。

------

# 七、单位落款关键词可以作为辅助，不应成为唯一条件

为了提高准确率，可以使用少量稳定组织名称特征作为辅助，例如行尾或整体包含：

```text
部
处
科
室
中心
办公室
委员会
工作组
银行
分行
支行
公司
部门
```

例如：

```text
数据管理部
科技管理部
XX银行深圳分行
项目工作组
```

但是：

不要只因为文本包含“部”就认为是 signature。

仍必须结合：

```text
文末位置
+
后面存在落款日期
+
短文本结构
```

综合判断。

------

# 八、日期前允许识别一至两个署名段

增强一点鲁棒性。

例如：

```text
XX银行深圳分行
数据管理部
2025年8月12日
```

如果日期前连续 1～2 个短段落均符合单位/署名特征，可以全部归类：

```text
signature
```

但第一版不要无限向前扫描。

建议最多：

```text
2个单位/署名段 + 1个日期段
```

避免吞掉正文。

------

# 九、如果没有日期，不要激进识别

例如文末只有：

```text
数据管理部
```

这时缺少强证据。

如果 classifier 无法高置信度确定，应：

```text
candidate_types = ["signature", "body"]
```

进入：

```text
NEEDS_REVIEW
```

不要为了减少 review 而直接强制右对齐。

------

# 十、如果日期明确存在，不应再让 Qwen3处理

典型：

```text
数据管理部
2025年8月12日
```

应该由 Python 确定性识别完成。

正常路径：

```text
一次调用
→ SUCCESS
```

不要因为标准落款再进入 Qwen3 review。

这是针对 Qwen3 性能的重要要求。

------

# 十一、signature 优先级

请检查当前 classification pipeline。

避免出现：

```text
数据管理部
```

先被误认为 title，

或者：

```text
2025年8月12日
```

被直接固定成 body，

然后 signature 后处理无法覆盖。

建议逻辑：

```text
基础分类
↓
head structure processing（title/salutation）
↓
tail structure processing（signature）
↓
得到final classification
```

最终 tail signature 高置信度判断：

应允许把原本低置信度的：

```text
body
unknown
甚至误判的title candidate
```

纠正为：

```text
signature
```

但不得覆盖真正明确的：

```text
heading_1
heading_2
heading_3
heading_4
attachment
```

除非存在非常明确的代码 Bug。

------

# 十二、signature Renderer 必须强制格式

只要最终 classification：

```text
signature
```

Renderer 不再参考其他历史状态。

必须明确设置：

```text
font = 仿宋_GB2312
size_pt = 16
alignment = right
first_line_indent_chars = 0
line_spacing_pt = 30
space_before_pt = 0
space_after_pt = 0
```

数字 Run：

```text
Times New Roman
```

且字号继承：

```text
16pt
```

------

# 十三、特别检查 signature 不得继承正文缩进

当前日期出现：

```text
左对齐 + 首行缩进2字符
```

说明很可能最终 classification 仍是：

```text
body
```

或者 renderer 在设置 signature 之后又执行了全局 body indent。

请检查执行顺序。

原则：

```text
paragraph-type-specific rule
```

必须最终生效。

不要出现：

```text
先signature indent=0
↓
后全局统一 firstLineChars=200
```

导致覆盖。

全局配置只负责真正全局属性，例如：

```text
line_spacing
space_before
space_after
digit_font
```

首行缩进属于：

```text
paragraph type rule
```

------

# 十四、第二个真实问题：全文段后10磅

当前生成 DOCX：

```text
固定值30磅行距
```

已经正确。

但是 Word 段落设置中还出现：

```text
间距
段后：10磅
```

这是错误的。

最终要求：

```text
段前：0磅
段后：0磅
固定值30磅
```

全文全部如此。

------

# 十五、段前段后规则适用于所有 Paragraph

以下所有类型：

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
blank
```

都必须：

```text
space_before = 0pt
space_after = 0pt
```

包括规定插入的：

```text
主标题后空白Paragraph
附件前空白Paragraph
```

不能通过段后间距制造空行。

空行必须仍然通过：

```text
真正的空白Paragraph
```

实现。

------

# 十六、不要把“段后10磅”当作无关视觉问题

这是正式格式验收项。

Validator 必须严格检查：

```text
space_before == 0pt
space_after == 0pt
```

任何：

```text
10pt
8pt
None但继承样式非0
```

都不能认为通过。

------

# 十七、重点检查 Normal Style

段后10磅很可能不是 Renderer 显式写入的。

很可能来自 Word 默认模板：

```text
Normal Style
→ spaceAfter = 10pt
```

如果 Paragraph 的：

```text
paragraph.paragraph_format.space_after
```

没有显式设置，

Word 会从 Normal Style 继承。

因此本轮不能只在报告中写：

```text
space_after=0
```

必须保证生成 DOCX 实际显示：

```text
段后 0 磅
```

------

# 十八、推荐双保险方案

为了彻底消除 Word 默认样式继承，建议同时：

## 第一层：基础 Normal Style

创建 Document 后，明确设置：

```text
Normal
```

的 paragraph format：

```text
space_before = Pt(0)
space_after = Pt(0)
```

必要时：

```text
line_spacing = Pt(30)
```

但注意：

不要因为设置 Normal Style 破坏各类型自己的 alignment、indent、font。

------

## 第二层：每个实际 Paragraph 显式设置

Renderer 对每个生成 Paragraph：

都明确执行：

```python
paragraph.paragraph_format.space_before = Pt(0)
paragraph.paragraph_format.space_after = Pt(0)
```

包括：

```text
title
salutation
headings
body
attachment
signature
blank
```

这样：

即使 Word 样式有问题，

Paragraph direct formatting 仍然确保：

```text
0 / 0
```

这是推荐实现。

------

# 十九、不要只设置其中一个

必须同时：

```text
space_before = 0
space_after = 0
```

不要只修：

```text
space_after
```

因为明确需求是：

```text
段前段后都应该是0
```

------

# 二十、配置文件更新

请修改：

```text
config/format_rules.json
```

把全局规则明确加入：

```json
{
  "global": {
    "line_spacing_pt": 30,
    "space_before_pt": 0,
    "space_after_pt": 0,
    "digit_font": "Times New Roman"
  }
}
```

具体 schema 按当前项目结构适配。

不要在 Renderer 中到处硬编码：

```text
Pt(0)
```

Renderer 和 Validator 都应读取同一规则来源。

但是底层实现函数可以接受配置值后设置。

------

# 二十一、不要把空一行改成段后30磅

当前规则仍然保持：

## 主标题后

```text
恰好一个空白 Paragraph
```

## 附件前

```text
恰好一个空白 Paragraph
```

不要改成：

```text
space_after = 30pt
```

或：

```text
space_before = 30pt
```

因为现在明确要求：

**全文段前段后均为0。**

所以视觉空行只能由：

```text
empty paragraph
```

实现。

------

# 二十二、Blank Paragraph 规则

规定插入的 blank paragraph：

```text
text = ""
line_spacing = fixed 30pt
space_before = 0pt
space_after = 0pt
no first-line indent
```

这样空行高度来自：

```text
固定值30磅
```

而不是额外 spacing。

------

# 二十三、段前段后 Validator 不要只看 python-docx 返回值

注意：

如果 direct formatting 没有明确设置，

```python
paragraph.paragraph_format.space_after
```

可能为：

```text
None
```

但 Word 实际通过 Style 继承：

```text
10pt
```

因此 Validator 应至少做到以下之一：

## 推荐

确保 Renderer：

- Normal Style = 0/0；
- Paragraph direct formatting = 0/0；

然后 Validator 同时检查：

```text
实际Paragraph pPr
+
Normal Style paragraph format
```

## 或

直接检查 OOXML：

```text
w:spacing
```

确保：

```text
w:before="0"
w:after="0"
```

并确认没有其它 Style 继承导致不同结果。

目标不是“代码变量看起来是0”。

目标是：

**Word/WPS 打开以后实际显示段前0磅、段后0磅。**

------

# 二十四、建议抽取统一 Paragraph Layout 函数

为了避免：

```text
title设置了0/0
body忘了
signature忘了
blank忘了
```

如果当前代码还没有统一入口，可以合理抽取：

```python
apply_paragraph_layout(...)
```

或类似函数。

统一负责：

```text
alignment
line_spacing
space_before
space_after
first_line_indent
```

然后 Renderer 对所有类型调用。

但不要因为这次修改把整个 Renderer 重写成复杂框架。

这是允许的小范围代码优化。

------

# 二十五、格式属性优先级建议

为了避免再次出现 signature 被正文规则覆盖，建议 Renderer 的流程清晰化：

```text
1. 创建Paragraph
2. 设置Paragraph公共规则
   - fixed 30pt
   - space_before 0
   - space_after 0

3. 设置类型专属规则
   - alignment
   - first-line indent

4. 按text生成Run
   - 基础字体
   - 数字Times New Roman

5. 最终不再执行会覆盖类型规则的全局格式
```

例如：

```text
signature
```

必须最终得到：

```text
common:
30pt
before=0
after=0

type:
right
indent=0

runs:
仿宋 / TNR数字
```

------

# 二十六、最终有效格式要求汇总

当前所有已经确认的要求必须继续保持。

## title

```text
方正小标宋简体
22pt
居中
首行缩进0
固定30磅
段前0
段后0
```

阿拉伯数字：

```text
Times New Roman
22pt
```

标题后：

```text
恰好1个空白Paragraph
```

------

## salutation

```text
仿宋_GB2312
16pt
左对齐
首行缩进0
固定30磅
段前0
段后0
```

阿拉伯数字：

```text
Times New Roman
16pt
```

------

## heading_1

```text
黑体
16pt
首行缩进2字符
固定30磅
段前0
段后0
```

阿拉伯数字：

```text
Times New Roman
16pt
```

------

## heading_2

```text
楷体_GB2312
16pt
首行缩进2字符
固定30磅
段前0
段后0
```

阿拉伯数字：

```text
Times New Roman
16pt
```

------

## heading_3

```text
仿宋_GB2312
16pt
首行缩进2字符
固定30磅
段前0
段后0
```

阿拉伯数字：

```text
Times New Roman
16pt
```

------

## heading_4

```text
仿宋_GB2312
16pt
首行缩进2字符
固定30磅
段前0
段后0
```

阿拉伯数字：

```text
Times New Roman
16pt
```

------

## body

```text
仿宋_GB2312
16pt
首行缩进2字符
固定30磅
段前0
段后0
```

阿拉伯数字：

```text
Times New Roman
16pt
```

------

## attachment

```text
仿宋_GB2312
16pt
首行缩进2字符
固定30磅
段前0
段后0
```

阿拉伯数字：

```text
Times New Roman
16pt
```

附件前：

```text
恰好1个空白Paragraph
```

------

## signature

```text
仿宋_GB2312
16pt
右对齐
首行缩进0
固定30磅
段前0
段后0
```

阿拉伯数字：

```text
Times New Roman
16pt
```

------

## blank

```text
固定30磅
段前0
段后0
无首行缩进
```

------

# 二十七、内容完整性要求保持不变

本轮修复不得修改：

```text
Browser source_text
```

中的任何非空文本。

继续严格要求：

```text
输入canonical非空段落
==
输出DOCX非空段落
```

比较：

- 数量；
- 顺序；
- 逐字符内容。

都必须相同。

不能为了落款识别：

```text
增加空格
删除空格
改日期
合并单位和日期
拆文本
增加制表符
```

------

# 二十八、落款不能通过空格或Tab实现右对齐

禁止：

```text
　　　　　　　　　数据管理部
```

禁止：

```text
\t\t数据管理部
```

禁止：

```text
left indent
```

模拟右对齐。

必须真正：

```text
paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
```

或等价 OOXML。

------

# 二十九、增加真实落款测试

创建/扩展 Browser Text fixture。

至少包含：

```text
关于2025年度数据治理工作的通知

行领导：

一、总体要求
相关部门应按照2025年度工作要求开展数据治理。

（一）重点任务
请于2025年8月完成相关工作。

1. 完成数据检查
项目编号为DATA-001。

（1）完成核验
完成率应达到100%。

数据管理部
2025年8月12日
```

预期：

```text
数据管理部
→ signature

2025年8月12日
→ signature
```

两个：

```text
RIGHT
0 char indent
0 before
0 after
30pt fixed
```

日期数字：

```text
2025
8
12
```

Times New Roman。

------

# 三十、测试模板式日期

再测试：

```text
数据管理部
2025年x月x日
```

确认：

两个都属于 signature。

其中：

```text
2025
```

Times New Roman。

字母：

```text
x
```

不要自动改写。

是否采用仿宋_GB2312 作为非数字基础字体即可。

------

# 三十一、测试正文日期不能变signature

例如：

```text
请各部门于2025年8月12日前完成数据报送。
```

位于正文中间。

必须：

```text
body
```

不能：

```text
signature
```

即使包含完整日期。

------

# 三十二、测试文末普通正文

例如：

```text
以上事项，请遵照执行。
```

位于最后。

不能因为位于结尾就识别：

```text
signature
```

仍然：

```text
body
```

------

# 三十三、测试无日期单位名

例如：

```text
以上事项，请遵照执行。
数据管理部
```

没有日期。

如果规则不能确定：

返回：

```text
NEEDS_REVIEW
```

候选：

```text
["signature", "body"]
```

不要强制 signature。

------

# 三十四、段前段后 E2E 测试

生成完整 DOCX 后：

遍历：

```text
所有paragraph
```

包括：

- title；
- blank；
- salutation；
- headings；
- body；
- attachment；
- signature。

验证：

```text
space_before == 0pt
space_after == 0pt
```

------

# 三十五、Normal Style 测试

必须额外检查：

```text
doc.styles["Normal"].paragraph_format.space_before
doc.styles["Normal"].paragraph_format.space_after
```

最终等价：

```text
0
0
```

防止 Word 再继承默认 10 磅。

------

# 三十六、XML 检查

实际检查生成：

```text
word/styles.xml
```

以及：

```text
word/document.xml
```

确认不存在导致正文普遍：

```text
after=200
```

即 10pt 的默认规则。

Word OOXML 中 spacing 通常以 twentieths of a point 表示。

例如：

```text
10pt = 200
```

所以特别搜索：

```text
w:after="200"
```

并确认当前生成内容不再依赖这种默认值。

如果旧模板中存在：

```text
w:after="200"
```

应找到来源并修掉。

不要简单做字符串替换 XML。

应该从样式/Paragraph API正确设置。

------

# 三十七、Validator 负面测试：段后

主动构造：

```text
body paragraph
space_after = 10pt
```

Validator 必须：

```text
VALIDATION_FAILED
```

不能通过。

------

# 三十八、Validator 负面测试：段前

主动构造：

```text
heading_1
space_before = 6pt
```

必须失败。

------

# 三十九、Validator 负面测试：signature alignment

主动把：

```text
数据管理部
```

改成：

```text
center
```

必须：

```text
VALIDATION_FAILED
```

这正对应当前真实 Bug。

------

# 四十、Validator 负面测试：signature date

把：

```text
2025年8月12日
```

设成：

```text
left
firstLineChars=200
```

Validator 必须同时报告：

```text
alignment error
indent error
```

不能只检查字体。

------

# 四十一、验证所有现有功能不能回归

修复完成后重新验证：

## Browser Text

仍可直接输入。

## title

仍正确。

## salutation

仍不缩进。

## heading 1～4

仍正确字体、字号、2字符缩进。

## body

仍仿宋、16pt、2字符缩进。

## attachment

仍正确且前空一行。

## digit font

所有阿拉伯数字仍 Times New Roman。

## line spacing

仍 fixed 30pt。

## content integrity

仍逐字符一致。

## blank policy

仍：

```text
title后 exactly 1
attachment前 exactly 1
```

## Qwen3

标准公文正常一次调用 SUCCESS。

不要因为 signature 改造导致大量 NEEDS_REVIEW。

------

# 四十二、SKILL.md 更新

只做必要调整。

新增/明确：

## 落款

当 Browser 文本结尾出现：

```text
单位名称
日期
```

程序会自动识别并设置：

```text
右对齐
```

Qwen3 不需要自行添加空格、Tab 或修改文本。

如果：

```text
status=NEEDS_REVIEW
```

且候选：

```text
["signature","body"]
```

模型只选择类型。

------

# 四十三、SKILL.md 不要让 Qwen3判断段距

段前段后：

```text
0 / 0
```

完全由 Python Renderer 控制。

Qwen3 不需要知道：

```text
Word Normal Style
w:spacing
Pt(0)
```

这些实现细节。

保持 Skill 执行提示简洁。

------

# 四十四、README / format_spec

更新：

```text
README.md
references/format_spec.md
```

明确：

```text
全文固定30磅
全文段前0磅
全文段后0磅
```

并明确：

```text
文末落款：仿宋_GB2312、三号、右对齐
```

不要自行加入其它新格式。

------

# 四十五、AGENTS.md

只增加必要工程约束：

```text
- 所有Paragraph必须显式设置space_before=0和space_after=0。
- Normal Style也必须设置段前段后0，避免Word默认样式继承。
- signature必须通过Paragraph alignment真正右对齐，不允许空格/Tab模拟。
- signature识别优先采用文末结构规则。
- 任何格式规则修改都必须同步Validator和E2E测试。
```

保持简洁。

------

# 四十六、允许的合理重构

本轮允许对以下区域做小范围优化：

```text
classify.py
render_docx.py
validate.py
docx_utils.py
format_rules.json
```

特别是：

### classify

可增加：

```text
tail signature detection
```

### renderer

可统一：

```text
apply_common_paragraph_format()
apply_type_specific_layout()
```

### validator

可增加：

```text
validate_paragraph_spacing()
validate_signature()
```

但是：

不要重写整个 Skill。

不要改变外部输入输出契约，除非为修 Bug 必须且保持向后兼容。

------

# 四十七、实施顺序

## Phase 1：审计当前 Bug 根因

首先检查：

```text
git status
git diff
classify.py
render_docx.py
validate.py
docx_utils.py
format_rules.json
```

找到：

### 为什么：

```text
数据管理部
```

会被居中。

### 为什么：

```text
日期
```

会被当 body 并有2字符缩进。

### 为什么：

```text
space_after
```

最终是10pt。

不要直接凭猜测修改。

先确认真实根因。

然后继续实施，不需要停下来等我确认。

------

## Phase 2：修 signature classifier

加入尾部结构识别。

------

## Phase 3：修 renderer

确保：

```text
signature → RIGHT + indent 0
所有Paragraph → before 0 + after 0
```

------

## Phase 4：修 Normal Style

确保不存在默认10pt段后。

------

## Phase 5：修 validator

加入：

```text
signature alignment
signature indent
paragraph before/after
Normal style
```

------

## Phase 6：补测试

包括真实复现场景。

------

## Phase 7：运行完整 unittest

执行：

```bash
python -m unittest discover -s tests -v
```

所有测试必须通过。

------

## Phase 8：Browser Text E2E

真实：

```text
browser_input
→ process
→ output.docx
→ validate
```

检查：

```text
数据管理部 = right
日期 = right
两个都 indent 0
全文 before=0
全文 after=0
全文 fixed30
```

------

## Phase 9：XML真实检查

不要只相信测试封装。

直接检查生成 DOCX 属性/XML。

------

## Phase 10：负面 Validator 测试

至少：

```text
signature center
signature date left
body space_after 10
heading space_before 6
```

都必须失败。

------

## Phase 11：完整回归

重新验证：

```text
digit font
2-char indent
salutation
title
headings
body
attachment
blank policy
content integrity
NEEDS_REVIEW
```

全部不回归。

------

## Phase 12：git diff审计

重点搜索：

```text
space_after
space_before
Pt(10)
after="200"
Normal
signature
WD_ALIGN_PARAGRAPH.CENTER
WD_ALIGN_PARAGRAPH.RIGHT
firstLineChars
```

确保没有旧规则覆盖新规则。

------

# 四十八、最终验收标准

只有全部满足才允许宣布完成。

## 落款识别

```text
数据管理部
2025年8月12日
```

均：

```text
classification = signature
```

标准场景不进入 NEEDS_REVIEW。

------

## 落款格式

两个段落均：

```text
仿宋_GB2312
16pt
RIGHT
first-line indent = 0
fixed 30pt
space before = 0
space after = 0
```

日期数字：

```text
Times New Roman
16pt
```

------

## 全文 Paragraph spacing

所有 Paragraph：

```text
space_before = 0pt
space_after = 0pt
```

包括：

```text
blank paragraph
```

------

## Normal Style

也明确：

```text
before=0
after=0
```

不能再出现 Word UI：

```text
段后10磅
```

------

## 行距

仍然：

```text
固定值30磅
```

------

## 内容

Browser 非空原文：

```text
==
```

输出非空文本。

逐字符一致。

------

## 原有格式

全部继续正确：

```text
title
salutation
heading1-4
body
attachment
digit font
indent
blank policy
```

------

# 四十九、最终报告

完成后请明确报告：

1. 落款错误的真实根因是什么；
2. 段后10磅的真实根因是什么；
3. 修改了哪些文件；
4. 是否进行了结构小优化；
5. signature tail detection 如何实现；
6. `数据管理部` 最终classification；
7. 日期最终classification；
8. 两个段落实际alignment；
9. 两个段落实际firstLineChars；
10. signature实际中文字体；
11. signature日期数字实际字体；
12. 全文实际space_before；
13. 全文实际space_after；
14. Normal Style实际space_before/space_after；
15. 全文实际line spacing；
16. 是否仍存在 `w:after="200"` 导致10pt段后的来源；
17. unittest实际数量；
18. unittest结果；
19. E2E结果；
20. Validator负面测试结果；
21. 原有数字字体测试是否继续通过；
22. 原有2字符缩进测试是否继续通过；
23. 内容完整性是否继续通过；
24. 当前仍存在的限制；
25. 最终部署ZIP路径。

如果任何已有测试出现回归：

继续修复。

不要通过删除测试、放宽 Validator 或弱化原要求解决失败。

最终目标：

**在保持现有 HiAgent Browser Text 公文整理 Skill 全部已有能力的基础上，稳定识别“单位名称 + 日期”形式的文末落款并真正右对齐，同时彻底消除 Word 默认段后10磅，使全文段前段后均严格为0磅，且继续保持固定30磅行距。**