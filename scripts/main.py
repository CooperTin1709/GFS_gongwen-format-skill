from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from .classify import classify_document
    from .input_adapter import adapt_source_text
    from .render_docx import load_overrides, render_document
    from .utils import PipelineError, workspace_path, write_json
    from .validate import validate_document
except ImportError:  # direct execution: python scripts/main.py
    from classify import classify_document
    from input_adapter import adapt_source_text
    from render_docx import load_overrides, render_document
    from utils import PipelineError, workspace_path, write_json
    from validate import validate_document


EXIT_SUCCESS = 0
EXIT_FAILURE = 2
EXIT_NEEDS_REVIEW = 3
DEFAULT_OUTPUT_NAME = "formatted.docx"


def _error_result(error: PipelineError) -> dict[str, Any]:
    return {
        "status": error.code,
        "errors": [{"message": error.message, "details": error.details}],
    }


def _write_result(output_dir: Path, result: dict[str, Any]) -> None:
    write_json(output_dir / "result.json", result)


def process_text(
    source_text: str,
    output_dir: str | Path,
    overrides: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Run Browser text through adaptation, classification, rendering, and validation."""

    try:
        destination = workspace_path(output_dir)
        destination.mkdir(parents=True, exist_ok=True)
        canonical = adapt_source_text(source_text)
        classified, analysis = classify_document(canonical)

        if analysis["review_count"] and overrides is None:
            review_path = write_json(destination / "review.json", analysis["review_items"])
            result = {
                "status": "NEEDS_REVIEW",
                "review_file": str(review_path),
                "review_count": analysis["review_count"],
            }
            _write_result(destination, result)
            return result

        output_path = destination / DEFAULT_OUTPUT_NAME
        rendered_path, plan = render_document(
            classified,
            output_path,
            overrides=overrides,
        )
        result = validate_document(
            classified,
            rendered_path,
            overrides=overrides,
        )
        result["classification_counts"] = dict(
            sorted(
                Counter(
                    item["classification"]
                    for item in plan
                    if item["classification"] != "blank"
                ).items()
            )
        )
        _write_result(destination, result)
        return result
    except PipelineError as exc:
        result = _error_result(exc)
        try:
            destination = workspace_path(output_dir)
            destination.mkdir(parents=True, exist_ok=True)
            _write_result(destination, result)
        except (OSError, PipelineError):
            pass
        return result
    except Exception as exc:  # fail closed without printing source text
        result = {
            "status": "RENDER_FAILED",
            "errors": [
                {
                    "message": "Unexpected pipeline failure.",
                    "details": {"reason": type(exc).__name__},
                }
            ],
        }
        try:
            destination = workspace_path(output_dir)
            destination.mkdir(parents=True, exist_ok=True)
            _write_result(destination, result)
        except (OSError, PipelineError):
            pass
        return result


def _stdout_result(result: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "status",
        "source_type",
        "output_file",
        "validation_passed",
        "verified_against",
        "review_file",
        "review_count",
        "errors",
    )
    return {key: result[key] for key in fields if key in result}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate and validate a formatted DOCX from Browser-extracted text."
    )
    parser.add_argument("--text-file", required=True, help="UTF-8 Browser text file.")
    parser.add_argument("--output-dir", required=True, help="Directory for result files.")
    parser.add_argument(
        "--overrides",
        help="Optional JSON mapping of ambiguous paragraph IDs to candidate types.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        text_path = workspace_path(args.text_file, must_exist=True)
        source_text = text_path.read_text(encoding="utf-8")
        overrides = load_overrides(args.overrides) if args.overrides else None
        result = process_text(source_text, args.output_dir, overrides=overrides)
    except (OSError, UnicodeError) as exc:
        result = _error_result(
            PipelineError(
                "INVALID_INPUT",
                "Unable to read the Browser text as UTF-8.",
                details={"reason": type(exc).__name__},
            )
        )
    except PipelineError as exc:
        result = _error_result(exc)

    print(json.dumps(_stdout_result(result), ensure_ascii=False))
    status = result["status"]
    if status == "SUCCESS":
        return EXIT_SUCCESS
    if status == "NEEDS_REVIEW":
        return EXIT_NEEDS_REVIEW
    return EXIT_FAILURE


if __name__ == "__main__":
    sys.exit(main())
