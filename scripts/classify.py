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
SALUTATION_END_RE = re.compile(r"[:：]$")
SALUTATION_TARGET_RE = re.compile(
    r"^(?:各位|各|全体|尊敬的|行)?(?:领导|同事|部门|单位|人员|同志|员工|代表|委员|机构|支行|分行|处室|科室|中心|办公室|[A-Za-z0-9０-９一-龥]{1,12}部门)$"
)
ARABIC_DATE_RE = re.compile(r"^[0-9０-９]{4}年[0-9０-９]{1,2}月[0-9０-９]{1,2}日$")
CHINESE_DATE_RE = re.compile(
    r"^[〇零一二三四五六七八九十]{4}年[〇零一二三四五六七八九十]{1,3}月[〇零一二三四五六七八九十]{1,4}日$"
)
ORGANIZATION_RE = re.compile(
    r"(?:部门|单位|公司|银行|分行|支行|委员会|政府|局|处|科|中心|办公室|集团|机构)$"
)


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


def _is_date(text: str) -> bool:
    return bool(ARABIC_DATE_RE.fullmatch(text) or CHINESE_DATE_RE.fullmatch(text))


def _is_organization(text: str) -> bool:
    return (
        len(text) <= 40
        and bool(ORGANIZATION_RE.search(text))
        and not SENTENCE_END_RE.search(text)
    )


def _signature_decisions(paragraphs: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    if not paragraphs:
        return {}
    last = len(paragraphs) - 1
    last_text = str(paragraphs[last]["analysis_text"])
    if _is_date(last_text):
        decisions = {last: _decision("signature", 1.0, "signature_date")}
        for index in range(last - 1, max(-1, last - 3), -1):
            text = str(paragraphs[index]["analysis_text"])
            if not _is_organization(text):
                break
            decisions[index] = _decision("signature", 0.99, "signature_before_date")
        return decisions
    if last > 0 and _is_organization(last_text):
        return {
            last: _decision(
                "unknown",
                0.50,
                "needs_review",
                candidate_types=["signature", "body"],
                suggested_type="signature",
            )
        }
    return {}


def _salutation_decision(
    analysis_text: str, index: int, first_heading_1: int | float
) -> dict[str, Any] | None:
    if index > 3 or index >= first_heading_1 or len(analysis_text) > 30:
        return None
    if not SALUTATION_END_RE.search(analysis_text):
        return None
    target = analysis_text[:-1]
    if SALUTATION_TARGET_RE.fullmatch(target):
        return _decision("salutation", 0.99, "salutation_structure")
    return _decision(
        "unknown",
        0.50,
        "needs_review",
        candidate_types=["salutation", "body"],
        suggested_type="salutation",
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
    signature_decisions = _signature_decisions(classified)
    in_attachment_block = False

    for index, paragraph in enumerate(classified):
        analysis_text = str(paragraph["analysis_text"])
        if index in signature_decisions:
            paragraph.update(signature_decisions[index])
            continue
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
        salutation = _salutation_decision(analysis_text, index, first_heading_1)
        if salutation is not None:
            paragraph.update(salutation)
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
