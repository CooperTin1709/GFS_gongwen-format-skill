# 公文格式整理 Skill

本项目把 HiAgent Browser 提取出的公文纯文本确定性地重建为规范 DOCX。程序不读取原始 DOCX，不联网，不调用模型 API，不改写任何 Browser 非空文本。

```text
用户 DOCX
→ HiAgent Browser
→ source_text
→ input_adapter
→ rules-first classify
→ render DOCX
→ reopen + strict validate
→ output DOCX
```

内容完整性的事实基准是 `Browser source_text` 生成的 canonical 非空段落，不是原始 DOCX。输出结果明确记录 `verified_against=browser_extracted_text`。

## 环境

- Python 3
- `python-docx`
- 不安装其他依赖，不使用网络、Pandoc、LibreOffice 或 Word COM

## 目录与职责

- `config/format_rules.json`：唯一排版值来源
- `references/format_spec.md`：维护和审计用内部规范
- `scripts/input_adapter.py`：保留原行文本，生成 canonical paragraph records
- `scripts/classify.py`：正则和上下文优先分类，生成有限 review 项
- `scripts/render_docx.py`：按原始 `text` 和配置生成 DOCX
- `scripts/validate.py`：重开 DOCX，严格验证文字、OOXML 字体、字号、对齐、行距和空行
- `scripts/main.py`：`process_text()` API 与单入口 CLI 编排
- `scripts/utils.py`：共享错误、路径、JSON 和配置读取
- `tests/`：input adapter、classification、validator 负面和 Browser Text E2E 测试
- `samples/browser_input.txt`：Browser 风格样例

## Python API

```python
from scripts.main import process_text

result = process_text(source_text, "work")
```

可选的 `overrides` 只能是 `paragraph_id -> candidate_type` 映射。

## CLI

```bash
python scripts/main.py --text-file samples/browser_input.txt --output-dir work
```

如返回 `NEEDS_REVIEW`，只读取 `review.json`，从每项的 `candidate_types` 选择一次并重跑：

```bash
python scripts/main.py --text-file samples/browser_input.txt --output-dir work --overrides overrides.json
```

stdout 只输出简短结果 JSON。成功结果包含：

```json
{
  "status": "SUCCESS",
  "source_type": "browser_text",
  "output_file": ".../formatted.docx",
  "validation_passed": true,
  "verified_against": "browser_extracted_text"
}
```

## 测试

```bash
python -m unittest discover -s tests -v
```

测试在 `.tmp/tests` 内生成临时 DOCX，并在验证前后真实保存和重新打开文件。

## 打包

部署包为 `dist/gongwen-format-skill.zip`。ZIP 根目录直接包含 `SKILL.md`，并仅包含 `SKILL.md`、`README.md`、`agents/`、`config/`、`references/` 和 `scripts/` 的运行必需文件。

## 当前限制

- 输入仅为 Browser 已提取的纯文本；不保留原 DOCX 页面结构或既有样式。
- 不处理图片、表格、页眉页脚、多 Section、PDF、OCR、HTML 或 Markdown。
- 不纠错、不规范标点、不修复编号。
- 只实现 `references/format_spec.md` 中明确批准的格式。
