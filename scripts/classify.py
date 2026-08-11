from __future__ import annotations

import copy
import re
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from .utils import write_json
except ImportError:  # pragma: no cover - direct script import fallback
    from utils import write_json


CHINESE_NUMBER = "一二三四五六七八九十百"
HEADING_1_RE = re.compile(rf"^[{CHINESE_NUMBER}]+、")
HEADING_2_RE = re.compile(rf"^（[{CHINESE_NUMBER}]+）")
HEADING_3_RE = re.compile(r"^\d+[.．]\s*\S")
HEADING_4_RE = re.compile(r"^（\d+）\s*\S")
ATTACHMENT_RE = re.compile(r"^附件[:：]")
ATTACHMENT_CONTINUATION_RE = re.compile(r"^[\s　]*\d+[.．、]")
TITLE_END_RE = re.compile(r"(通知|通报|决定|意见|公告|报告|请示|批复|函|纪要)$")
SENTENCE_END_RE = re.compile(r"[。！？；!?;]$")


def _decision(
    paragraph_type: str,
    confidence: float,
    source: str,
    *,
    candidate_type: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "classification": paragraph_type,
        "confidence": confidence,
        "classification_source": source,
    }
    if candidate_type:
        result["candidate_type"] = candidate_type
    if reason:
        result["review_reason"] = reason
    return result


def _numbered_heading_decision(text: str, heading_type: str) -> dict[str, Any]:
    if len(text) > 45 or SENTENCE_END_RE.search(text):
        return _decision("body", 0.90, "numbered_complete_sentence")
    if len(text) <= 24:
        return _decision(heading_type, 0.97, "regex")
    return _decision(
        "unknown",
        0.45,
        "needs_review",
        candidate_type=heading_type,
        reason="Numbered paragraph has ambiguous heading length.",
    )


def classify_paragraphs(paragraphs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    classified = copy.deepcopy(paragraphs)
    nonblank_indices = [i for i, item in enumerate(classified) if item["text"] != ""]
    first_nonblank = nonblank_indices[0] if nonblank_indices else None
    heading_1_indices = [
        i for i, item in enumerate(classified) if HEADING_1_RE.match(item["text"])
    ]
    first_heading_1 = heading_1_indices[0] if heading_1_indices else float("inf")
    in_attachment_block = False

    for index, paragraph in enumerate(classified):
        text = paragraph["text"]
        if text == "":
            in_attachment_block = False
            paragraph.update(_decision("blank", 1.0, "empty_text"))
            continue
        if ATTACHMENT_RE.match(text):
            in_attachment_block = True
            paragraph.update(_decision("attachment", 0.99, "attachment_block"))
            continue
        if in_attachment_block and ATTACHMENT_CONTINUATION_RE.match(text):
            paragraph.update(_decision("attachment", 0.99, "attachment_block"))
            continue
        in_attachment_block = False
        if HEADING_1_RE.match(text):
            paragraph.update(_decision("heading_1", 0.99, "regex"))
            continue
        if HEADING_2_RE.match(text):
            paragraph.update(_decision("heading_2", 0.99, "regex"))
            continue
        if HEADING_4_RE.match(text):
            paragraph.update(_numbered_heading_decision(text, "heading_4"))
            continue
        if HEADING_3_RE.match(text):
            paragraph.update(_numbered_heading_decision(text, "heading_3"))
            continue
        if index == first_nonblank and index < first_heading_1:
            if len(text) <= 80 and TITLE_END_RE.search(text):
                paragraph.update(_decision("title", 0.99, "title_structure"))
                continue
            if len(text) <= 60 and not SENTENCE_END_RE.search(text):
                paragraph.update(
                    _decision(
                        "unknown",
                        0.45,
                        "needs_review",
                        candidate_type="title",
                        reason="First structural paragraph lacks a decisive title marker.",
                    )
                )
                continue
        if len(text.strip()) <= 6 and not SENTENCE_END_RE.search(text):
            paragraph.update(
                _decision(
                    "unknown",
                    0.40,
                    "needs_review",
                    candidate_type="body",
                    reason="Short unnumbered paragraph is semantically ambiguous.",
                )
            )
            continue
        paragraph.update(_decision("body", 0.95, "body_fallback"))

    return classified


def classify_document(document_data: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    result = copy.deepcopy(document_data)
    result["paragraphs"] = classify_paragraphs(result["paragraphs"])
    needs_review = [
        {
            "id": item["id"],
            "index": item["index"],
            "candidate_type": item.get("candidate_type"),
            "reason": item.get("review_reason"),
        }
        for item in result["paragraphs"]
        if item["classification"] == "unknown"
    ]
    counts = Counter(item["classification"] for item in result["paragraphs"])
    analysis = {
        "success": not needs_review,
        "code": "NEEDS_REVIEW" if needs_review else "SUCCESS",
        "needs_review": needs_review,
        "classification_counts": dict(sorted(counts.items())),
    }
    result["analysis"] = analysis
    return result, analysis


def write_classification(
    document_data: dict[str, Any], work_dir: str | Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    classified, analysis = classify_document(document_data)
    destination = Path(work_dir)
    write_json(destination / "document.json", classified)
    write_json(destination / "analysis.json", analysis)
    return classified, analysis
