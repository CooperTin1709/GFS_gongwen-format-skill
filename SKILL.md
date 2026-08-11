---
name: gongwen-format-skill
description: Convert complete Chinese public-document text extracted by the HiAgent Browser plugin into a strictly formatted, validated DOCX without changing any non-blank source paragraph. Use for 整理公文格式、规范公文、按规定字体字号排版，或把 Browser 读取的文档文本转换为规范 Word；Browser 纯文本是合法输入，不要求原始 DOCX。
---

# 公文格式整理

接收 Browser 插件读取到的完整公文纯文本，生成经过严格验证的 DOCX。格式由程序和 `config/format_rules.json` 决定。

## 输入

- 把 Browser 返回的完整原始文本保存为 UTF-8 文本文件。
- 纯文本就是合法输入。不得拒绝，不得要求重新上传 DOCX，不得访问原文件 URL。

## 正常执行

1. 运行：

   ```bash
   python scripts/main.py --text-file browser_input.txt --output-dir work
   ```

2. 如果 `status=SUCCESS`，直接返回 `output_file`。
3. 不要再次修改生成文件。

## NEEDS_REVIEW

如果 `status=NEEDS_REVIEW`：

1. 只读取 `review_file` 中的项目。
2. 每项只能从 `candidate_types` 选择一个类型。
3. 只生成段落 ID 到类型的简单映射：

   ```json
   {
     "p0012": "heading_3"
   }
   ```

4. 保存映射后只再调用一次：

   ```bash
   python scripts/main.py --text-file browser_input.txt --output-dir work --overrides overrides.json
   ```

5. 如果返回 `INVALID_OVERRIDE` 或其他失败状态，停止并报告错误；不要循环 review，不要强猜。

## 禁止事项

- 不重写、总结、纠错或重新返回全文。
- 不修改文字、空格、标点、数字、日期或编号。
- 不在 overrides 中返回正文、理由或格式。
- 不自行设置字体、字号、行距或新增其他公文标准。
- 不访问原始 DOCX URL，不联网，不调用外部模型 API。
- 不因输入是文本而拒绝。
- 不跳过 Validator。

只有程序返回 `status=SUCCESS` 才告诉用户已经完成，并直接返回 `output_file`。
