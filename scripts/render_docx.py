from __future__ import annotations

from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Emu, Pt

try:
    from .utils import (
        PipelineError,
        RESOLVED_TYPES,
        load_json,
        load_rules,
        resolved_format_rule,
        workspace_path,
    )
except ImportError:  # pragma: no cover - direct script import fallback
    from utils import (
        PipelineError,
        RESOLVED_TYPES,
        load_json,
        load_rules,
        resolved_format_rule,
        workspace_path,
    )


def load_overrides(path: str | Path | None) -> dict[str, str]:
    if path is None:
        return {}
    override_path = workspace_path(path, must_exist=True)
    data = load_json(override_path)
    if not isinstance(data, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in data.items()
    ):
        raise PipelineError(
            "INVALID_OVERRIDE",
            "Overrides must be a JSON object mapping paragraph id to type.",
        )
    return data


def resolve_classifications(
    document_data: dict[str, Any], overrides: dict[str, str] | None = None
) -> list[dict[str, Any]]:
    override_map = overrides or {}
    paragraphs = document_data.get("paragraphs")
    if not isinstance(paragraphs, list):
        raise PipelineError("INVALID_INPUT", "document.json has no paragraph list.")
    known_ids = {item.get("id") for item in paragraphs}
    unknown_override_ids = sorted(set(override_map) - known_ids)
    if unknown_override_ids:
        raise PipelineError(
            "INVALID_OVERRIDE",
            "Override contains unknown paragraph ids.",
            details={"ids": unknown_override_ids},
        )

    resolved: list[dict[str, Any]] = []
    unresolved: list[str] = []
    for item in paragraphs:
        paragraph = dict(item)
        paragraph_id = paragraph.get("id")
        original_type = paragraph.get("classification")
        if paragraph_id in override_map:
            if original_type != "unknown":
                raise PipelineError(
                    "INVALID_OVERRIDE",
                    "Only needs_review paragraphs may be overridden.",
                    details={"id": paragraph_id},
                )
            paragraph_type = override_map[paragraph_id]
            if paragraph_type not in RESOLVED_TYPES:
                raise PipelineError(
                    "INVALID_OVERRIDE",
                    "Override type is not allowed.",
                    details={"id": paragraph_id, "type": paragraph_type},
                )
            paragraph["classification"] = paragraph_type
            paragraph["classification_source"] = "override"
            paragraph["confidence"] = 1.0
        paragraph_type = paragraph.get("classification")
        if paragraph_type in (None, "unknown"):
            unresolved.append(str(paragraph_id))
            continue
        if paragraph_type not in RESOLVED_TYPES:
            raise PipelineError(
                "INVALID_INPUT",
                "document.json contains an invalid classification.",
                details={"id": paragraph_id, "type": paragraph_type},
            )
        if paragraph.get("text") == "" and paragraph_type != "blank":
            raise PipelineError(
                "INVALID_OVERRIDE",
                "An empty source paragraph must remain blank.",
                details={"id": paragraph_id},
            )
        if paragraph.get("text") != "" and paragraph_type == "blank":
            raise PipelineError(
                "INVALID_OVERRIDE",
                "A non-empty source paragraph cannot be classified as blank.",
                details={"id": paragraph_id},
            )
        resolved.append(paragraph)

    if unresolved:
        raise PipelineError(
            "NEEDS_REVIEW",
            "Rendering is blocked until all ambiguous paragraphs are classified.",
            details={"paragraph_ids": unresolved},
        )
    if sum(item["classification"] == "title" for item in resolved) > 1:
        raise PipelineError(
            "INVALID_OVERRIDE",
            "At most one paragraph may be classified as the main title.",
        )
    return resolved


def build_render_plan(
    paragraphs: list[dict[str, Any]], blank_policy: dict[str, Any]
) -> list[dict[str, Any]]:
    """Normalize only the two required blank boundaries."""

    plan: list[dict[str, Any]] = []
    first_attachment_index = next(
        (i for i, item in enumerate(paragraphs) if item["classification"] == "attachment"),
        None,
    )
    index = 0
    while index < len(paragraphs):
        item = dict(paragraphs[index])
        paragraph_type = item["classification"]
        if paragraph_type == "title":
            plan.append(item)
            index += 1
            while index < len(paragraphs) and paragraphs[index]["classification"] == "blank":
                index += 1
            for blank_number in range(int(blank_policy["after_title"])):
                plan.append(
                    {
                        "id": f"__blank_after_title_{blank_number + 1}",
                        "index": None,
                        "text": "",
                        "is_blank": True,
                        "classification": "blank",
                        "classification_source": "blank_policy",
                        "confidence": 1.0,
                    }
                )
            continue
        if index == first_attachment_index:
            while plan and plan[-1]["classification"] == "blank":
                plan.pop()
            for blank_number in range(int(blank_policy["before_attachment"])):
                plan.append(
                    {
                        "id": f"__blank_before_attachment_{blank_number + 1}",
                        "index": None,
                        "text": "",
                        "is_blank": True,
                        "classification": "blank",
                        "classification_source": "blank_policy",
                        "confidence": 1.0,
                    }
                )
        plan.append(item)
        index += 1
    return plan


def _remove_default_paragraph(document: Any) -> None:
    if document.paragraphs:
        paragraph = document.paragraphs[0]
        paragraph._element.getparent().remove(paragraph._element)


def _apply_section_metadata(document: Any, metadata: dict[str, Any]) -> None:
    values = metadata.get("section", {})
    section = document.sections[0]
    for attribute in (
        "page_width",
        "page_height",
        "top_margin",
        "bottom_margin",
        "left_margin",
        "right_margin",
        "header_distance",
        "footer_distance",
        "gutter",
    ):
        value = values.get(attribute)
        if value is not None:
            setattr(section, attribute, Emu(int(value)))
    orientation = values.get("orientation", "")
    if "landscape" in orientation:
        section.orientation = WD_ORIENT.LANDSCAPE
    elif "portrait" in orientation:
        section.orientation = WD_ORIENT.PORTRAIT


def _set_exact_line_spacing(paragraph: Any, line_spacing_pt: float) -> None:
    paragraph.paragraph_format.line_spacing = Pt(line_spacing_pt)
    spacing = paragraph._p.get_or_add_pPr().get_or_add_spacing()
    spacing.set(qn("w:line"), str(round(line_spacing_pt * 20)))
    spacing.set(qn("w:lineRule"), "exact")


def _set_run_format(run: Any, font_name: str, size_pt: float) -> None:
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    fonts = run._element.get_or_add_rPr().get_or_add_rFonts()
    fonts.set(qn("w:eastAsia"), font_name)


def render_document(
    document_data: dict[str, Any],
    output: str | Path,
    *,
    overrides: dict[str, str] | None = None,
    rules_path: str | Path | None = None,
    workspace: str | Path | None = None,
) -> tuple[Path, list[dict[str, Any]]]:
    output_path = workspace_path(output, workspace=workspace)
    if output_path.suffix.lower() != ".docx":
        raise PipelineError("RENDER_FAILED", "Output path must end with .docx.")
    source_path = Path(str(document_data.get("source_file", ""))).resolve()
    if source_path == output_path:
        raise PipelineError("RENDER_FAILED", "Output must not overwrite the source DOCX.")

    rules = load_rules(rules_path)
    resolved = resolve_classifications(document_data, overrides)
    plan = build_render_plan(resolved, rules["blank_policy"])
    document = Document()
    _remove_default_paragraph(document)
    _apply_section_metadata(document, document_data.get("metadata", {}))
    line_spacing_pt = float(rules["global"]["line_spacing_pt"])

    for item in plan:
        paragraph = document.add_paragraph()
        paragraph_type = item["classification"]
        if paragraph_type != "blank":
            rule = resolved_format_rule(rules, paragraph_type)
            run = paragraph.add_run(item["text"])
            _set_run_format(run, rule["font"], float(rule["size_pt"]))
            alignment = rule.get("alignment")
            if alignment == "center":
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _set_exact_line_spacing(paragraph, line_spacing_pt)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        document.save(output_path)
    except Exception as exc:
        raise PipelineError(
            "RENDER_FAILED",
            "Unable to save the rendered DOCX.",
            details={"path": str(output_path), "reason": type(exc).__name__},
        ) from exc
    return output_path, plan


def render_from_files(
    document_json: str | Path,
    output: str | Path,
    *,
    overrides_path: str | Path | None = None,
    rules_path: str | Path | None = None,
    workspace: str | Path | None = None,
) -> tuple[Path, list[dict[str, Any]], dict[str, Any], dict[str, str]]:
    data = load_json(document_json)
    overrides = load_overrides(overrides_path)
    path, plan = render_document(
        data,
        output,
        overrides=overrides,
        rules_path=rules_path,
        workspace=workspace,
    )
    return path, plan, data, overrides
