# 公文格式整理规范

## 范围

当前 Skill 只把 HiAgent Browser 提取出的纯文本重建为固定格式 DOCX。它不读取或保留原始 DOCX 的样式、页面结构、表格、图片、页眉页脚或 Section，也不解析 HTML、Markdown、PDF 或 OCR 内容。

未明确规定的页面尺寸、页边距、页码、版心、缩进、段前段后、发文机关、日期、版记、目录等均不设置。

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

## 类型与格式

| 类型 | 字体 | 字号 | 对齐/其他 |
| --- | --- | --- | --- |
| `title` | 方正小标宋简体 | 22 pt | 居中 |
| `heading_1` | 黑体 | 16 pt | 未规定 |
| `heading_2` | 楷体_GB2312 | 16 pt | 未规定 |
| `heading_3` | 仿宋_GB2312 | 16 pt | 不加粗 |
| `heading_4` | 仿宋_GB2312 | 16 pt | 不加粗 |
| `body` | 仿宋_GB2312 | 16 pt | 未规定 |
| `attachment` | 继承正文 | 16 pt | 未规定 |

每个非空段落使用一个 paragraph 和一个原文 run。字体必须写入 `w:rFonts` 的 `w:eastAsia`、`w:ascii`、`w:hAnsi`、`w:cs` 四项。

## 分类与 review

- 一级标题：`^[一二三四五六七八九十百]+、`
- 二级标题：`^（[一二三四五六七八九十百]+）`
- 三级标题：阿拉伯数字加半角 `.` 或全角 `．`，再结合长度和句末标点
- 四级标题：全角括号内阿拉伯数字，再结合长度和句末标点
- 附件：`^附件[:：]`，从此段到文末均为 attachment
- 主标题：首段、位于第一个一级标题之前、长度合理并具有公文标题结尾特征
- 无编号的普通陈述句直接归为 body

真正模糊的编号段只提供 `[heading_3, body]` 或 `[heading_4, body]`；模糊首段只提供 `[title, body]`。review 只允许一次，override 必须为段落 ID 到候选类型的映射。

## 严格验证

生成 DOCX 后必须重新打开并验证：

- Browser canonical 非空文本数量、顺序和逐字符 equality；
- 完整 paragraph sequence 与两处 canonical blank policy；
- 四个 `w:rFonts` 属性；
- 字号；
- 主标题居中；
- 所有段落 `w:lineRule=exact` 且 `w:line=600`（30 pt）。

任一检查失败均返回 `VALIDATION_FAILED`，不得报告成功。
