# 公文格式整理规范

## 范围

当前 Skill 只把 HiAgent Browser 提取出的纯文本重建为固定格式 DOCX。它不读取或保留原始 DOCX 的样式、页面结构、表格、图片、页眉页脚或 Section，也不解析 HTML、Markdown、PDF 或 OCR 内容。

未明确规定的页面尺寸、页边距、页码、版心、发文机关、版记、目录等均不设置。

## 内容事实来源

- `source_text` 是唯一内容事实来源。
- input adapter 仅统一 CRLF、CR 为 LF；每个保留行的 `text` 逐字符不变。
- `analysis_text` 只用于分类，不得用于输出。
- Validator 以 canonical 非空 `text` 与输出 DOCX 非空 `paragraph.text` 做数量、顺序和逐字符严格比较。
- 验证报告固定声明 `verified_against=browser_extracted_text`，不得声称与原始 DOCX 逐字一致。

## 空白策略

- Browser 原有空白行不复制。
- 主标题后恰好一个空白 Word Paragraph。
- 第一个附件段前恰好一个空白 Word Paragraph。
- 所有输出段落，包括规定空白段落，使用固定值 30 pt 行距。
- 所有输出段落段前、段后均为 0 pt；Normal Style 同样明确设置为 0/0，避免继承 Word 默认 10 pt 段后。

## 类型与格式

| 类型 | 字体 | 字号 | 对齐/其他 | 首行缩进 |
| --- | --- | --- | --- | --- |
| `title` | 方正小标宋简体 | 22 pt | 居中 | 0 |
| `salutation` | 仿宋_GB2312 | 16 pt | 左对齐 | 0 |
| `heading_1` | 黑体 | 16 pt | 未规定 | 2 字符 |
| `heading_2` | 楷体_GB2312 | 16 pt | 未规定 | 2 字符 |
| `heading_3` | 仿宋_GB2312 | 16 pt | 未规定、不加粗 | 2 字符 |
| `heading_4` | 仿宋_GB2312 | 16 pt | 未规定、不加粗 | 2 字符 |
| `body` | 仿宋_GB2312 | 16 pt | 未规定 | 2 字符 |
| `attachment` | 仿宋_GB2312 | 16 pt | 未规定 | 2 字符 |
| `signature` | 仿宋_GB2312 | 16 pt | 右对齐 | 0 |

两字符缩进使用 `w:firstLineChars="200"`，并清除冲突的 `w:firstLine`、`w:hanging`、`w:hangingChars`；不得在原文前插入空格。

非空段落按连续半角或全角阿拉伯数字安全拆分 Run。数字 Run 使用 Times New Roman，非数字 Run 使用段落基础字体，所有 Run 字号继承段落类型。字体必须写入 `w:rFonts` 的 `w:eastAsia`、`w:ascii`、`w:hAnsi`、`w:cs` 四项；拼接全部 Run 后必须逐字符等于原 `text`。

## 分类与 review

- 一级标题：`^[一二三四五六七八九十百]+、`
- 二级标题：`^（[一二三四五六七八九十百]+）`
- 三级标题：阿拉伯数字加半角 `.` 或全角 `．`，再结合长度和句末标点
- 四级标题：全角括号内阿拉伯数字，再结合长度和句末标点
- 附件：`^附件[:：]`，从此段到文末均为 attachment
- 主标题：首段、位于第一个一级标题之前、长度合理并具有公文标题结尾特征
- 称谓：仅在文档开头区域识别，以冒号结束的独立短称呼优先确定为 salutation
- 落款：仅在文末识别；日期为强特征，紧邻日期前的短单位名称同时为 signature
- 无编号的普通陈述句直接归为 body

真正模糊的编号段只提供 `[heading_3, body]` 或 `[heading_4, body]`；模糊首段只提供 `[title, body]`；模糊称谓只提供 `[salutation, body]`；文末只有单位名称而无日期时只提供 `[signature, body]`。review 只允许一次，override 必须为段落 ID 到候选类型的映射。

## 严格验证

生成 DOCX 后必须重新打开并验证：

- Browser canonical 非空文本数量、顺序和逐字符 equality；
- 完整 paragraph sequence 与两处 canonical blank policy；
- 四个 `w:rFonts` 属性；
- 数字 Run 只包含阿拉伯数字并使用 Times New Roman；
- 字号；
- `w:firstLineChars` 缩进策略及冲突属性；
- 主标题居中、称谓左对齐、落款右对齐；
- 所有段落 `w:lineRule=exact` 且 `w:line=600`（30 pt）。
- 所有段落 direct formatting 的段前/段后均为 0 pt，Normal Style 段前/段后也均为 0 pt。

任一检查失败均返回 `VALIDATION_FAILED`，不得报告成功。
