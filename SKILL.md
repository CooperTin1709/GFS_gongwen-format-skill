---
name: gongwen-format-skill
description: Deterministically format plain-text Chinese public-document DOCX files while preserving every original non-empty paragraph character and order. Use when a user provides a DOCX and asks to 整理公文格式、按公文要求排版、规范 Word 公文格式，或将 DOCX 整理为指定格式. Supports strict preflight rejection of complex content, paragraph classification with constrained review overrides, configured rendering, and mandatory DOCX validation.
---

# 公文格式整理

处理用户提供的纯文字 DOCX。以 `document.json` 中程序提取的原始 `text` 为唯一正文事实来源；仅用 Markdown 帮助判断模糊段落。

## 执行流程

1. 在 Skill 根目录运行预检、提取和分类：

   ```bash
   python scripts/main.py analyze input.docx --work-dir work
   ```

2. 查看 `work/result.json` 和 `work/analysis.json`。若 `code` 为 `UNSUPPORTED_COMPLEX_CONTENT`，明确告知用户当前版本只安全支持纯文字、单 Section DOCX，并停止。
3. 阅读 `work/document.md`，只关注 `needs_review` 列出的段落 ID 及上下文。
4. 若没有 `needs_review`，运行完整流水线：

   ```bash
   python scripts/main.py format input.docx --output output.docx --work-dir work
   ```

5. 若有 `needs_review`，只创建 ID 到类型的 JSON 映射，例如：

   ```json
   {
     "p0012": "heading_3",
     "p0021": "body"
   }
   ```

   只使用 `title`、`heading_1`、`heading_2`、`heading_3`、`heading_4`、`body`、`attachment`、`blank`；不得包含正文文本或其他字段。保存为 `work/classification_overrides.json`，再运行：

   ```bash
   python scripts/main.py render work/document.json --overrides work/classification_overrides.json --output output.docx --result-file work/result.json
   ```

6. 独立复核。没有 `needs_review` 时不要传入不存在的 override 文件：

   ```bash
   python scripts/main.py validate work/document.json --output output.docx --result-file work/validation-result.json
   ```

   只有实际创建了 override 文件时，才增加：

   ```text
   --overrides work/classification_overrides.json
   ```

7. 只有 `result.json` 和独立验证结果都为 `SUCCESS`，才向用户返回最终 DOCX。

## 禁止事项

- 不重写、纠错、润色、总结或重新输出全文作为 renderer 输入。
- 不修改文字、标点、数字、日期、标题编号、全半角字符或附件内容。
- 不把 Markdown 或模型输出的正文作为事实来源。
- 不覆盖源 DOCX。
- 不绕过 `needs_review` 或 Validator。
- 不自行增加 A4、页边距、缩进、页码等未确认规则。
- 不访问网络、不上传文档、不调用外部模型 API、不记录全文日志。

## 资源

- 格式值：`config/format_rules.json`
- 完整内部规范：`references/format_spec.md`
- 流水线入口：`scripts/main.py`
