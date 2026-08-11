from __future__ import annotations

from typing import Any

try:
    from .utils import PipelineError
except ImportError:  # pragma: no cover - direct script import fallback
    from utils import PipelineError


def adapt_source_text(source_text: str) -> dict[str, Any]:
    """Convert Browser text to canonical non-blank paragraph records.

    Only newline encodings are unified. Each retained ``text`` value is the
    original line and is never replaced by its analysis-only copy.
    """

    if not isinstance(source_text, str):
        raise PipelineError("INVALID_INPUT", "source_text must be a string.")

    unified = source_text.replace("\r\n", "\n").replace("\r", "\n")
    paragraphs: list[dict[str, Any]] = []
    for line in unified.split("\n"):
        analysis_text = line.strip(" \t")
        if analysis_text == "":
            continue
        index = len(paragraphs)
        paragraphs.append(
            {
                "id": f"p{index + 1:04d}",
                "index": index,
                "text": line,
                "analysis_text": analysis_text,
                "classification": None,
                "confidence": None,
                "classification_source": None,
            }
        )

    if not paragraphs:
        raise PipelineError(
            "INVALID_INPUT",
            "source_text must contain at least one non-blank paragraph.",
        )

    return {
        "schema_version": 2,
        "source_type": "browser_text",
        "paragraphs": paragraphs,
    }
