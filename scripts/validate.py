from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

try:
    from .render_docx import build_render_plan, resolve_classifications
    from .utils import (
        PipelineError,
        load_json,
        load_rules,
        resolved_format_rule,
        workspace_path,
        write_json,
    )
except ImportError:  # pragma: no cover - direct script import fallback
    from render_docx import build_render_plan, resolve_classifications
    from utils import (
        PipelineError,
        load_json,
        load_rules,
        resolved_format_rule,
        workspace_path,
        write_json,
    )


def _line_spacing(paragraph: Any) -> tuple[str | None, float | None]:
    p_pr = paragraph._p.pPr
    if p_pr is None or p_pr.spacing is None:
        return None, None
    spacing = p_pr.spacing
    rule = spacing.get(qn("w:lineRule"))
    value = spacing.get(qn("w:line"))
    try:
        points = int(value) / 20 if value is not None else None
    except ValueError:
        points = None
    return rule, points


def _east_asia_font(run: Any) -> str | None:
    r_pr = run._element.rPr
    if r_pr is None or r_pr.rFonts is None:
        return None
    return r_pr.rFonts.get(qn("w:eastAsia"))


def _first_mismatch(expected: list[str], actual: list[str]) -> int | None:
    for index, (left, right) in enumerate(zip(expected, actual)):
        if left != right:
            return index
    return min(len(expected), len(actual)) if len(expected) != len(actual) else None


def _blank_count_after(paragraphs: list[Any], index: int) -> int:
    count = 0
    for paragraph in paragraphs[index + 1 :]:
        if paragraph.text != "":
            break
        count += 1
    return count


def _blank_count_before(paragraphs: list[Any], index: int) -> int:
    count = 0
    for paragraph in reversed(paragraphs[:index]):
        if paragraph.text != "":
            break
        count += 1
    return count


def validate_document(
    document_data: dict[str, Any],
    output: str | Path,
    *,
    overrides: dict[str, str] | None = None,
    rules_path: str | Path | None = None,
    workspace: str | Path | None = None,
) -> dict[str, Any]:
    output_path = workspace_path(output, must_exist=True, workspace=workspace)
    rules = load_rules(rules_path)
    resolved = resolve_classifications(document_data, overrides)
    blank_policy = rules["blank_policy"]
    plan = build_render_plan(resolved, blank_policy)
    try:
        rendered = Document(output_path)
    except Exception as exc:
        raise PipelineError(
            "VALIDATION_FAILED",
            "Rendered DOCX cannot be reopened.",
            details={"reason": type(exc).__name__},
        ) from exc

    errors: list[dict[str, Any]] = []
    expected_nonempty = [item["text"] for item in document_data["paragraphs"] if item["text"] != ""]
    actual_nonempty = [paragraph.text for paragraph in rendered.paragraphs if paragraph.text != ""]
    mismatch = _first_mismatch(expected_nonempty, actual_nonempty)
    if mismatch is not None:
        errors.append(
            {
                "check": "text_integrity",
                "message": "Non-empty paragraph text or order differs from the source.",
                "first_mismatch_index": mismatch,
                "expected_count": len(expected_nonempty),
                "actual_count": len(actual_nonempty),
            }
        )

    expected_all = [item["text"] for item in plan]
    actual_all = [paragraph.text for paragraph in rendered.paragraphs]
    sequence_mismatch = _first_mismatch(expected_all, actual_all)
    if sequence_mismatch is not None:
        errors.append(
            {
                "check": "paragraph_sequence",
                "message": "Rendered paragraph sequence does not match the normalized plan.",
                "first_mismatch_index": sequence_mismatch,
                "expected_count": len(expected_all),
                "actual_count": len(actual_all),
            }
        )

    observations: dict[str, dict[str, set[Any]]] = defaultdict(
        lambda: {"eastAsia": set(), "size_pt": set(), "line_spacing_pt": set()}
    )
    for index, item in enumerate(plan[: len(rendered.paragraphs)]):
        paragraph = rendered.paragraphs[index]
        paragraph_type = item["classification"]
        line_rule, line_points = _line_spacing(paragraph)
        observations[paragraph_type]["line_spacing_pt"].add(line_points)
        expected_line = float(rules["global"]["line_spacing_pt"])
        if line_rule != "exact" or line_points != expected_line:
            errors.append(
                {
                    "check": "line_spacing",
                    "paragraph_id": item["id"],
                    "expected_rule": "exact",
                    "expected_pt": expected_line,
                    "actual_rule": line_rule,
                    "actual_pt": line_points,
                }
            )
        if paragraph_type == "blank":
            continue
        rule = resolved_format_rule(rules, paragraph_type)
        text_runs = [run for run in paragraph.runs if run.text != ""]
        if not text_runs:
            errors.append(
                {
                    "check": "run_presence",
                    "paragraph_id": item["id"],
                    "message": "Non-empty paragraph has no text run.",
                }
            )
            continue
        for run in text_runs:
            east_asia = _east_asia_font(run)
            size_pt = run.font.size.pt if run.font.size is not None else None
            observations[paragraph_type]["eastAsia"].add(east_asia)
            observations[paragraph_type]["size_pt"].add(size_pt)
            if east_asia != rule["font"]:
                errors.append(
                    {
                        "check": "eastAsia_font",
                        "paragraph_id": item["id"],
                        "expected": rule["font"],
                        "actual": east_asia,
                    }
                )
            if size_pt != float(rule["size_pt"]):
                errors.append(
                    {
                        "check": "font_size",
                        "paragraph_id": item["id"],
                        "expected_pt": float(rule["size_pt"]),
                        "actual_pt": size_pt,
                    }
                )
        if rule.get("alignment") == "center" and paragraph.alignment != WD_ALIGN_PARAGRAPH.CENTER:
            errors.append(
                {
                    "check": "alignment",
                    "paragraph_id": item["id"],
                    "expected": "center",
                    "actual": getattr(paragraph.alignment, "name", None),
                }
            )

    title_indices = [i for i, item in enumerate(plan) if item["classification"] == "title"]
    title_blank_ok = True
    if title_indices:
        title_blank_ok = (
            _blank_count_after(rendered.paragraphs, title_indices[0])
            == int(blank_policy["after_title"])
        )
        if not title_blank_ok:
            errors.append(
                {"check": "blank_after_title", "message": "Title must be followed by exactly one blank paragraph."}
            )
    attachment_index = next(
        (i for i, item in enumerate(plan) if item["classification"] == "attachment"),
        None,
    )
    attachment_blank_ok = True
    if attachment_index is not None:
        attachment_blank_ok = (
            _blank_count_before(rendered.paragraphs, attachment_index)
            == int(blank_policy["before_attachment"])
        )
        if not attachment_blank_ok:
            errors.append(
                {"check": "blank_before_attachment", "message": "Attachment block must have exactly one preceding blank paragraph."}
            )

    observed_formats = {
        key: {
            field: sorted(value, key=lambda item: (item is None, str(item)))
            for field, value in fields.items()
        }
        for key, fields in sorted(observations.items())
    }
    success = not errors
    return {
        "success": success,
        "code": "SUCCESS" if success else "VALIDATION_FAILED",
        "source_file": document_data.get("source_file"),
        "output_file": str(output_path) if success else None,
        "errors": errors,
        "warnings": [],
        "needs_review": [],
        "validation": {
            "text_identical": mismatch is None,
            "paragraph_sequence_matches_plan": sequence_mismatch is None,
            "source_nonempty_count": len(expected_nonempty),
            "output_nonempty_count": len(actual_nonempty),
            "blank_after_title": title_blank_ok,
            "blank_before_attachment": attachment_blank_ok,
            "observed_formats": observed_formats,
        },
    }


def validate_from_files(
    document_json: str | Path,
    output: str | Path,
    *,
    overrides_path: str | Path | None = None,
    rules_path: str | Path | None = None,
    result_path: str | Path | None = None,
    workspace: str | Path | None = None,
) -> dict[str, Any]:
    try:
        from .render_docx import load_overrides
    except ImportError:  # pragma: no cover
        from render_docx import load_overrides

    data = load_json(document_json)
    overrides = load_overrides(overrides_path)
    result = validate_document(
        data,
        output,
        overrides=overrides,
        rules_path=rules_path,
        workspace=workspace,
    )
    if result_path:
        write_json(result_path, result)
    return result
