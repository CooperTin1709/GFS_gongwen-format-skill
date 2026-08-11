from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RULES_PATH = PROJECT_ROOT / "config" / "format_rules.json"

PARAGRAPH_TYPES = {
    "title",
    "heading_1",
    "heading_2",
    "heading_3",
    "heading_4",
    "body",
    "attachment",
}


class PipelineError(Exception):
    """Expected pipeline failure with a stable machine-readable code."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

    def as_result(self) -> dict[str, Any]:
        return {
            "status": self.code,
            "errors": [{"message": self.message, "details": self.details}],
        }


def workspace_path(
    value: str | Path,
    *,
    must_exist: bool = False,
    workspace: str | Path | None = None,
) -> Path:
    """Resolve a user data path and keep it inside the active workspace."""

    root = Path(workspace or Path.cwd()).resolve()
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise PipelineError(
            "INVALID_INPUT",
            "Path must stay inside the current working directory.",
            details={"path": str(candidate)},
        ) from exc
    if must_exist and not candidate.exists():
        raise PipelineError(
            "INVALID_INPUT",
            "Input path does not exist.",
            details={"path": str(candidate)},
        )
    return candidate


def load_json(path: str | Path) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PipelineError(
            "INVALID_INPUT",
            "Unable to read valid UTF-8 JSON.",
            details={"path": str(path), "reason": type(exc).__name__},
        ) from exc


def write_json(path: str | Path, data: Any) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(destination)
    return destination


def load_rules(path: str | Path | None = None) -> dict[str, Any]:
    rules_path = Path(path) if path else DEFAULT_RULES_PATH
    rules = load_json(rules_path)
    required = {
        "title",
        "heading_1",
        "heading_2",
        "heading_3",
        "heading_4",
        "body",
        "attachment",
        "global",
        "blank_policy",
    }
    missing = sorted(required - set(rules))
    if missing:
        raise PipelineError(
            "INVALID_INPUT",
            "Formatting rules are incomplete.",
            details={"missing": missing},
        )
    return rules


def resolved_format_rule(rules: dict[str, Any], paragraph_type: str) -> dict[str, Any]:
    if paragraph_type == "blank":
        return {}
    rule = rules[paragraph_type]
    if "inherit" in rule:
        return dict(rules[rule["inherit"]])
    return dict(rule)
