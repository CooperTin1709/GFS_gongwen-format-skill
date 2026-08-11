from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from .classify import classify_document
    from .extract import extract_document, write_extraction
    from .render_docx import load_overrides, render_document
    from .utils import PipelineError, load_json, workspace_path, write_json
    from .validate import validate_document
except ImportError:  # direct execution: python scripts/main.py
    from classify import classify_document
    from extract import extract_document, write_extraction
    from render_docx import load_overrides, render_document
    from utils import PipelineError, load_json, workspace_path, write_json
    from validate import validate_document


EXIT_SUCCESS = 0
EXIT_FAILURE = 2
EXIT_NEEDS_REVIEW = 3


def _print_summary(result: dict[str, Any]) -> None:
    summary = {
        key: result.get(key)
        for key in ("success", "code", "output_file", "document_json", "document_md", "result_file")
        if key in result
    }
    summary["needs_review_count"] = len(result.get("needs_review", []))
    summary["error_count"] = len(result.get("errors", []))
    print(json.dumps(summary, ensure_ascii=False))


def analyze_pipeline(source: str | Path, work_dir: str | Path) -> tuple[dict[str, Any], dict[str, Any]]:
    work_path = workspace_path(work_dir)
    work_path.mkdir(parents=True, exist_ok=True)
    extracted = extract_document(source)
    files = write_extraction(extracted, work_path)
    classified, analysis = classify_document(extracted)
    write_json(work_path / "document.json", classified)
    write_json(work_path / "analysis.json", analysis)
    result = {
        "success": not analysis["needs_review"],
        "code": analysis["code"],
        "source_file": classified["source_file"],
        "output_file": None,
        "document_json": files["document_json"],
        "document_md": files["document_md"],
        "analysis_file": str(work_path / "analysis.json"),
        "review_file": str(work_path / "classification_overrides.json"),
        "needs_review": analysis["needs_review"],
        "warnings": [],
        "errors": [],
    }
    result_path = write_json(work_path / "result.json", result)
    result["result_file"] = str(result_path)
    write_json(result_path, result)
    return classified, result


def _render_validate(
    data: dict[str, Any],
    output: str | Path,
    *,
    overrides: dict[str, str] | None,
    result_path: str | Path,
) -> dict[str, Any]:
    rendered_path, _ = render_document(data, output, overrides=overrides)
    result = validate_document(data, rendered_path, overrides=overrides)
    result["result_file"] = str(Path(result_path).resolve())
    write_json(result_path, result)
    return result


def command_analyze(args: argparse.Namespace) -> int:
    _, result = analyze_pipeline(args.input, args.work_dir)
    _print_summary(result)
    return EXIT_SUCCESS if result["success"] else EXIT_NEEDS_REVIEW


def command_format(args: argparse.Namespace) -> int:
    data, analysis_result = analyze_pipeline(args.input, args.work_dir)
    if analysis_result["needs_review"]:
        _print_summary(analysis_result)
        return EXIT_NEEDS_REVIEW
    result_path = Path(args.work_dir) / "result.json"
    result = _render_validate(data, args.output, overrides=None, result_path=result_path)
    result.update(
        {
            "document_json": analysis_result["document_json"],
            "document_md": analysis_result["document_md"],
        }
    )
    write_json(result_path, result)
    _print_summary(result)
    return EXIT_SUCCESS if result["success"] else EXIT_FAILURE


def command_render(args: argparse.Namespace) -> int:
    document_path = workspace_path(args.document_json, must_exist=True)
    data = load_json(document_path)
    overrides = load_overrides(args.overrides)
    result_path = workspace_path(args.result_file or (Path(args.output).parent / "result.json"))
    result = _render_validate(data, args.output, overrides=overrides, result_path=result_path)
    _print_summary(result)
    return EXIT_SUCCESS if result["success"] else EXIT_FAILURE


def command_validate(args: argparse.Namespace) -> int:
    document_path = workspace_path(args.document_json, must_exist=True)
    data = load_json(document_path)
    overrides = load_overrides(args.overrides)
    result = validate_document(data, args.output, overrides=overrides)
    result_path = workspace_path(args.result_file or (Path(args.output).parent / "validation-result.json"))
    result["result_file"] = str(result_path)
    write_json(result_path, result)
    _print_summary(result)
    return EXIT_SUCCESS if result["success"] else EXIT_FAILURE


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Deterministically format and validate plain-text Chinese DOCX files."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Preflight, extract, and classify a DOCX.")
    analyze.add_argument("input")
    analyze.add_argument("--work-dir", required=True)
    analyze.set_defaults(handler=command_analyze)

    format_command = subparsers.add_parser("format", help="Run the complete pipeline when no review is needed.")
    format_command.add_argument("input")
    format_command.add_argument("--output", required=True)
    format_command.add_argument("--work-dir", required=True)
    format_command.set_defaults(handler=command_format)

    render = subparsers.add_parser("render", help="Render classified JSON and validate the output.")
    render.add_argument("document_json")
    render.add_argument("--output", required=True)
    render.add_argument("--overrides")
    render.add_argument("--result-file")
    render.set_defaults(handler=command_render)

    validate = subparsers.add_parser("validate", help="Reopen and independently validate a rendered DOCX.")
    validate.add_argument("document_json")
    validate.add_argument("--output", required=True)
    validate.add_argument("--overrides")
    validate.add_argument("--result-file")
    validate.set_defaults(handler=command_validate)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except PipelineError as exc:
        result = exc.as_result()
        if getattr(args, "work_dir", None):
            try:
                work_dir = workspace_path(args.work_dir)
                work_dir.mkdir(parents=True, exist_ok=True)
                result_path = write_json(work_dir / "result.json", result)
                result["result_file"] = str(result_path)
                write_json(result_path, result)
            except PipelineError:
                pass
        _print_summary(result)
        return EXIT_NEEDS_REVIEW if exc.code == "NEEDS_REVIEW" else EXIT_FAILURE
    except Exception as exc:  # fail closed without printing document content
        result = {
            "success": False,
            "code": "RENDER_FAILED",
            "errors": [{"message": "Unexpected pipeline failure.", "reason": type(exc).__name__}],
            "warnings": [],
            "needs_review": [],
            "output_file": None,
        }
        _print_summary(result)
        return EXIT_FAILURE


if __name__ == "__main__":
    sys.exit(main())
