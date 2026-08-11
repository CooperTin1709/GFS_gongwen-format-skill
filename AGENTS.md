# Maintenance rules

- Do not add external dependencies or network access.
- Never rewrite, normalize, correct, or otherwise change source paragraph text.
- Keep all formatting values in `config/format_rules.json`.
- Use `unittest`; run the complete suite after every behavior change.
- Reopen and validate every rendered DOCX before reporting success.
- Never bypass validation or downgrade a validation failure to a warning.
- Reject unsupported complex content instead of silently dropping it.
- Do not add public-document formatting rules that are not explicitly approved.
