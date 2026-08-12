from __future__ import annotations

import unittest

from scripts.classify import classify_document, classify_paragraphs
from scripts.input_adapter import adapt_source_text


class ClassifyTests(unittest.TestCase):
    def classify(self, text: str) -> dict[str, object]:
        paragraph = adapt_source_text(text)["paragraphs"][0]
        return classify_paragraphs([paragraph])[0]

    def test_heading_1(self) -> None:
        self.assertEqual(self.classify("一、标题")["classification"], "heading_1")

    def test_heading_2(self) -> None:
        self.assertEqual(self.classify("（一）标题")["classification"], "heading_2")

    def test_heading_3_ascii_period(self) -> None:
        self.assertEqual(self.classify("1. 标题")["classification"], "heading_3")

    def test_heading_3_fullwidth_period(self) -> None:
        self.assertEqual(self.classify("1．标题")["classification"], "heading_3")

    def test_heading_4(self) -> None:
        self.assertEqual(self.classify("（1）标题")["classification"], "heading_4")

    def test_body(self) -> None:
        self.assertEqual(self.classify("普通正文。")["classification"], "body")

    def test_opening_salutation(self) -> None:
        self.assertEqual(self.classify("行领导：")["classification"], "salutation")

    def test_department_salutation(self) -> None:
        self.assertEqual(self.classify("XX部门：")["classification"], "salutation")

    def test_body_colon_in_middle_is_not_salutation(self) -> None:
        data = adapt_source_text(
            "关于测试工作的通知\n一、总体要求\n普通正文。\n具体要求如下："
        )
        result = classify_paragraphs(data["paragraphs"])
        self.assertEqual(result[-1]["classification"], "body")

    def test_signature_organization_and_arabic_date(self) -> None:
        data = adapt_source_text(
            "关于测试工作的通知\n一、总体要求\n正文。\nXX部门\n2026年8月11日"
        )
        result = classify_paragraphs(data["paragraphs"])
        self.assertEqual(
            [item["classification"] for item in result[-2:]],
            ["signature", "signature"],
        )

    def test_signature_chinese_date(self) -> None:
        data = adapt_source_text(
            "关于测试工作的通知\n一、总体要求\n正文。\nXX部门\n二〇二六年八月十一日"
        )
        result = classify_paragraphs(data["paragraphs"])
        self.assertEqual(result[-1]["classification"], "signature")

    def test_signature_after_attachment_block(self) -> None:
        data = adapt_source_text(
            "关于测试工作的通知\n附件：1.任务表\n　　　2.说明\nXX部门\n2026年8月11日"
        )
        result = classify_paragraphs(data["paragraphs"])
        self.assertEqual(
            [item["classification"] for item in result],
            ["title", "attachment", "attachment", "signature", "signature"],
        )

    def test_organization_without_date_needs_review(self) -> None:
        data = adapt_source_text("正文最后一句。\nXX部门")
        result, analysis = classify_document(data)
        self.assertEqual(result["paragraphs"][-1]["classification"], "unknown")
        self.assertEqual(
            result["paragraphs"][-1]["candidate_types"], ["signature", "body"]
        )
        self.assertEqual(analysis["status"], "NEEDS_REVIEW")

    def test_attachment_and_all_following_lines(self) -> None:
        data = adapt_source_text("附件：1.测试\n　　　2.说明")
        result = classify_paragraphs(data["paragraphs"])
        self.assertEqual(
            [item["classification"] for item in result],
            ["attachment", "attachment"],
        )

    def test_long_numbered_sentence_is_body(self) -> None:
        text = "1.2026年业务增长达到100%，该编号为AI-001且这是明显完整的正文句子。"
        self.assertEqual(self.classify(text)["classification"], "body")

    def test_ambiguous_numbered_paragraph_has_limited_candidates(self) -> None:
        result = self.classify("1. 这是长度处于灰区且没有明确句末标记的模糊编号段落内容")
        self.assertEqual(result["classification"], "unknown")
        self.assertEqual(result["candidate_types"], ["heading_3", "body"])

    def test_decisive_title(self) -> None:
        self.assertEqual(
            self.classify("关于进一步加强管理工作的通知")["classification"],
            "title",
        )

    def test_ambiguous_first_paragraph_has_title_or_body_candidates(self) -> None:
        result = self.classify("工作安排")
        self.assertEqual(result["classification"], "unknown")
        self.assertEqual(result["candidate_types"], ["title", "body"])

    def test_review_item_contains_only_local_context(self) -> None:
        data = adapt_source_text(
            "关于测试工作的通知\n一、要求\n1. 这是长度处于灰区且没有明确句末标记的模糊编号段落内容\n后续正文。"
        )
        _, analysis = classify_document(data)
        self.assertEqual(analysis["review_count"], 1)
        review = analysis["review_items"][0]
        self.assertEqual(
            set(review),
            {
                "id",
                "text",
                "previous_text",
                "next_text",
                "candidate_types",
                "suggested_type",
            },
        )
        self.assertEqual(review["previous_text"], "一、要求")
        self.assertEqual(review["next_text"], "后续正文。")


if __name__ == "__main__":
    unittest.main()
