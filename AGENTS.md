# Maintenance rules

- Do not add external dependencies, network access, external APIs, Pandoc, LibreOffice, or Word COM.
- Treat `source_text` from Browser as the only content ground truth.
- Keep each retained original line in `text`; use `analysis_text` only for classification.
- Never strip, normalize, rewrite, correct, or otherwise change source paragraph `text`.
- Renderer output must use original `text`, never `analysis_text` or model-returned text.
- Keep all formatting values in `config/format_rules.json`.
- Use `unittest`; run the complete suite after every behavior change.
- Run the Browser Text E2E after changes to the pipeline.
- Reopen and validate every generated DOCX before reporting success.
- Never bypass Validator or downgrade a validation failure to a warning.
- Do not add public-document formatting rules that are not explicitly approved.
