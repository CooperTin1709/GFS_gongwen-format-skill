# 公文格式整理 Skill

这是一个确定性优先的中文纯文字 DOCX 格式整理器。它从 DOCX 直接提取段落文本，以结构化 JSON 为事实来源，按配置重建文档，再重新打开输出文件验证文字、顺序和格式。程序不联网、不调用大模型 API，也不修改原文内容。

## 环境要求

- Python 3
- `python-docx`
- 不需要也不允许在线安装额外依赖

## 目录

- `config/format_rules.json`：唯一格式值来源
- `references/format_spec.md`：当前内部格式规范
- `scripts/extract.py`：Preflight、DOCX 提取、JSON/Markdown 视图
- `scripts/classify.py`：Regex 与结构规则分类
- `scripts/render_docx.py`：按 JSON 原文和分类重新生成 DOCX
- `scripts/validate.py`：重新打开输出并验证
- `scripts/main.py`：CLI 入口
- `tests/`：真实 DOCX 单元与端到端测试
- `samples/input/`、`samples/output/`：可选本地样例目录
- `dist/`：最终部署 ZIP（生成物，不纳入 Git）

## 运行

分析：

```bash
python scripts/main.py analyze input.docx --work-dir work
```

无需人工复核时直接格式化：

```bash
python scripts/main.py format input.docx --output output.docx --work-dir work
```

需要复核时，只在 `classification_overrides.json` 写段落 ID 到类型的映射，然后：

```bash
python scripts/main.py render work/document.json --overrides work/classification_overrides.json --output output.docx --result-file work/result.json
python scripts/main.py validate work/document.json --overrides work/classification_overrides.json --output output.docx --result-file work/validation-result.json
```

## 测试与测试文档

测试代码会在项目 `.tmp/` 下自动生成格式故意混乱的虚构 DOCX，不使用真实文件：

```bash
python -m unittest discover -s tests -v
```

`tests/support.py` 的 `create_messy_docx()` 是测试文档生成入口。

## 打包

完成全部测试后，使用 Python 标准库 `zipfile` 将 `SKILL.md`、`agents/`、`config/`、`references/` 和 `scripts/` 直接放到 ZIP 根目录：

```text
dist/gongwen-format-skill.zip
```

部署包不包含测试、样例、Git、缓存和临时工作目录。

## 修改格式

只编辑 `config/format_rules.json`，然后运行完整测试。不要把具体字体、字号、对齐或行距散落到 Python 代码中，也不要加入未确认的公文规范。

## 当前限制

- 仅支持普通纯文字、单 Section DOCX。
- 表格、图片、文本框、嵌入对象、多 Section、非空页眉页脚会明确失败。
- 仅规范 TASK 明确给出的字体、字号、主标题居中、两处空行和固定行距。
- 模糊结构必须由智能体只针对 `needs_review` 段落分类。
