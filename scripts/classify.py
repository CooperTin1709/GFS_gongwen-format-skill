from __future__ import annotations

import copy
import re
from collections import Counter
from typing import Any


CHINESE_NUMBER = "一二三四五六七八九十百"
HEADING_1_RE = re.compile(rf"^[{CHINESE_NUMBER}]+、")
HEADING_2_RE = re.compile(rf"^（[{CHINESE_NUMBER}]+）")
HEADING_3_RE = re.compile(r"^\d+[.．]\s*\S")
HEADING_4_RE = re.compile(r"^（\d+）\s*\S")
ATTACHMENT_RE = re.compile(r"^附件[:：]")
TITLE_END_RE = re.compile(r"(通知|通报|决定|意见|公告|报告|请示|批复|函|纪要|方案)$")
SENTENCE_END_RE = re.compile(r"[。！？；!?;]$")


def _decision(
    paragraph_type: str,
    confidence: float,
    source: str,
    *,
    candidate_types: list[str] | None = None,
    suggested_type: str | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "classification": paragraph_type,
        "confidence": confidence,
        "classification_source": source,
    }
    if candidate_types is not None:
        result["candidate_types"] = candidate_types
        result["suggested_type"] = suggested_type or candidate_types[0]
    return result


def _numbered_heading_decision(analysis_text: str, heading_type: str) -> dict[str, Any]:
    if len(analysis_text) > 45 or SENTENCE_END_RE.search(analysis_text):
        return _decision("body", 0.95, "numbered_complete_sentence")
    if len(analysis_text) <= 24:
        return _decision(heading_type, 0.99, "regex")
    return _decision(
        "unknown",
        0.50,
        "needs_review",
        candidate_types=[heading_type, "body"],
        suggested_type=heading_type,
    )


def classify_paragraphs(paragraphs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    classified = copy.deepcopy(paragraphs)
    first_heading_1 = next(
        (
            index
            for index, item in enumerate(classified)
            if HEADING_1_RE.match(str(item["analysis_text"]))
        ),
        float("inf"),
    )
    in_attachment_block = False

    for index, paragraph in enumerate(classified):
        analysis_text = str(paragraph["analysis_text"])
        if in_attachment_block:
            paragraph.update(_decision("attachment", 1.0, "attachment_block"))
            continue
        if ATTACHMENT_RE.match(analysis_text):
            in_attachment_block = True
            paragraph.update(_decision("attachment", 1.0, "attachment_block"))
            continue
        if HEADING_1_RE.match(analysis_text):
            paragraph.update(_decision("heading_1", 1.0, "regex"))
            continue
        if HEADING_2_RE.match(analysis_text):
            paragraph.update(_decision("heading_2", 1.0, "regex"))
            continue
        if HEADING_4_RE.match(analysis_text):
            paragraph.update(_numbered_heading_decision(analysis_text, "heading_4"))
            continue
        if HEADING_3_RE.match(analysis_text):
            paragraph.update(_numbered_heading_decision(analysis_text, "heading_3"))
            continue
        if index == 0 and index < first_heading_1:
            if len(analysis_text) <= 80 and TITLE_END_RE.search(analysis_text):
                paragraph.update(_decision("title", 1.0, "title_structure"))
                continue
            if len(analysis_text) <= 80 and not SENTENCE_END_RE.search(analysis_text):
                paragraph.update(
                    _decision(
                        "unknown",
                        0.50,
                        "needs_review",
                        candidate_types=["title", "body"],
                        suggested_type="title",
                    )
                )
                continue
        paragraph.update(_decision("body", 0.99, "body_fallback"))

    return classified


def _review_items(paragraphs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for index, paragraph in enumerate(paragraphs):
        if paragraph["classification"] != "unknown":
            continue
        items.append(
            {
                "id": paragraph["id"],
                "text": paragraph["text"],
                "previous_text": paragraphs[index - 1]["text"] if index > 0 else "",
                "next_text": paragraphs[index + 1]["text"] if index + 1 < len(paragraphs) else "",
                "candidate_types": paragraph["candidate_types"],
                "suggested_type": paragraph["suggested_type"],
            }
        )
    return items


def classify_document(document_data: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    result = copy.deepcopy(document_data)
    result["paragraphs"] = classify_paragraphs(result["paragraphs"])
    review_items = _review_items(result["paragraphs"])
    counts = Counter(item["classification"] for item in result["paragraphs"])
    analysis = {
        "status": "NEEDS_REVIEW" if review_items else "SUCCESS",
        "review_count": len(review_items),
        "review_items": review_items,
        "classification_counts": dict(sorted(counts.items())),
    }
    return result, analysis
