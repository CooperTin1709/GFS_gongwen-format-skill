from __future__ import annotations

import re
from typing import Any

from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Pt


DIGIT_RUN_RE = re.compile(r"[0-9０-９]+")
FONT_ATTRIBUTES = ("eastAsia", "ascii", "hAnsi", "cs")
INDENT_ATTRIBUTES = ("firstLine", "hanging", "hangingChars")


def split_text_by_digit_runs(text: str) -> list[tuple[str, bool]]:
    """Split text without changing any character; coalesce consecutive digits."""

    parts: list[tuple[str, bool]] = []
    start = 0
    for match in DIGIT_RUN_RE.finditer(text):
        if match.start() > start:
            parts.append((text[start : match.start()], False))
        parts.append((match.group(0), True))
        start = match.end()
    if start < len(text):
        parts.append((text[start:], False))
    return parts


def is_digit_run_text(text: str) -> bool:
    return bool(text) and DIGIT_RUN_RE.fullmatch(text) is not None


def set_run_format(
    run: Any,
    *,
    font_name: str,
    size_pt: float,
    bold: bool | None = None,
) -> None:
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    if bold is not None:
        run.font.bold = bold
    fonts = run._element.get_or_add_rPr().get_or_add_rFonts()
    for attribute in FONT_ATTRIBUTES:
        fonts.set(qn(f"w:{attribute}"), font_name)


def font_values(run: Any) -> dict[str, str | None]:
    r_pr = run._element.rPr
    fonts = r_pr.rFonts if r_pr is not None else None
    return {
        attribute: fonts.get(qn(f"w:{attribute}")) if fonts is not None else None
        for attribute in FONT_ATTRIBUTES
    }


def set_exact_line_spacing(paragraph: Any, line_spacing_pt: float) -> None:
    paragraph.paragraph_format.line_spacing = Pt(line_spacing_pt)
    spacing = paragraph._p.get_or_add_pPr().get_or_add_spacing()
    spacing.set(qn("w:line"), str(round(line_spacing_pt * 20)))
    spacing.set(qn("w:lineRule"), "exact")


def set_paragraph_spacing(
    paragraph: Any, *, space_before_pt: float, space_after_pt: float
) -> None:
    paragraph.paragraph_format.space_before = Pt(space_before_pt)
    paragraph.paragraph_format.space_after = Pt(space_after_pt)
    spacing = paragraph._p.get_or_add_pPr().get_or_add_spacing()
    spacing.set(qn("w:before"), str(round(space_before_pt * 20)))
    spacing.set(qn("w:after"), str(round(space_after_pt * 20)))


def paragraph_spacing(paragraph: Any) -> tuple[float | None, float | None]:
    p_pr = paragraph._p.pPr
    if p_pr is None or p_pr.spacing is None:
        return None, None
    spacing = p_pr.spacing

    def _points(attribute: str) -> float | None:
        value = spacing.get(qn(f"w:{attribute}"))
        try:
            return int(value) / 20 if value is not None else None
        except ValueError:
            return None

    return _points("before"), _points("after")


def set_default_paragraph_spacing(
    document: Any, *, space_before_pt: float, space_after_pt: float
) -> None:
    styles = document.styles.element
    doc_defaults = styles.find(qn("w:docDefaults"))
    if doc_defaults is None:
        doc_defaults = OxmlElement("w:docDefaults")
        styles.insert(0, doc_defaults)
    p_pr_default = doc_defaults.find(qn("w:pPrDefault"))
    if p_pr_default is None:
        p_pr_default = OxmlElement("w:pPrDefault")
        doc_defaults.append(p_pr_default)
    p_pr = p_pr_default.find(qn("w:pPr"))
    if p_pr is None:
        p_pr = OxmlElement("w:pPr")
        p_pr_default.append(p_pr)
    spacing = p_pr.find(qn("w:spacing"))
    if spacing is None:
        spacing = OxmlElement("w:spacing")
        p_pr.append(spacing)
    spacing.set(qn("w:before"), str(round(space_before_pt * 20)))
    spacing.set(qn("w:after"), str(round(space_after_pt * 20)))


def default_paragraph_spacing(document: Any) -> tuple[float | None, float | None]:
    styles = document.styles.element
    spacing = styles.find(
        f"{qn('w:docDefaults')}/{qn('w:pPrDefault')}/{qn('w:pPr')}/{qn('w:spacing')}"
    )
    if spacing is None:
        return None, None

    def _points(attribute: str) -> float | None:
        value = spacing.get(qn(f"w:{attribute}"))
        try:
            return int(value) / 20 if value is not None else None
        except ValueError:
            return None

    return _points("before"), _points("after")


def line_spacing(paragraph: Any) -> tuple[str | None, float | None]:
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


def set_first_line_indent_chars(paragraph: Any, chars: float) -> None:
    ind = paragraph._p.get_or_add_pPr().get_or_add_ind()
    for attribute in (*INDENT_ATTRIBUTES, "firstLineChars"):
        ind.attrib.pop(qn(f"w:{attribute}"), None)
    if chars:
        ind.set(qn("w:firstLineChars"), str(round(chars * 100)))


def indent_values(paragraph: Any) -> dict[str, str | None]:
    p_pr = paragraph._p.pPr
    ind = p_pr.ind if p_pr is not None else None
    attributes = ("firstLineChars", *INDENT_ATTRIBUTES)
    return {
        attribute: ind.get(qn(f"w:{attribute}")) if ind is not None else None
        for attribute in attributes
    }
