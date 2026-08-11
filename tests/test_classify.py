from __future__ import annotations

import unittest

from scripts.classify import classify_paragraphs


def paragraph(text: str, index: int = 0) -> dict[str, object]:
    return {
        "id": f"p{index + 1:04d}",
        "index": index,
        "text": text,
        "is_blank": text == "",
        "classification": None,
        "confidence": None,
        "classification_source": None,
    }


class ClassifyTests(unittest.TestCase):
    def classify(self, text: str) -> dict[str, object]:
        return classify_paragraphs([paragraph(text)])[0]

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
        self.assertEqual(
            self.classify("这是普通正文内容，不允许发生任何修改。")["classification"],
            "body",
        )

    def test_attachment_and_continuation(self) -> None:
        items = [paragraph("附件：1.任务表", 0), paragraph("　　　2.说明", 1)]
        result = classify_paragraphs(items)
        self.assertEqual([item["classification"] for item in result], ["attachment", "attachment"])

    def test_attachment_block_does_not_consume_later_body(self) -> None:
        items = [
            paragraph("附件：1.任务表", 0),
            paragraph("", 1),
            paragraph("这是附件之后的普通正文。", 2),
        ]
        result = classify_paragraphs(items)
        self.assertEqual(
            [item["classification"] for item in result],
            ["attachment", "blank", "body"],
        )

    def test_blank(self) -> None:
        self.assertEqual(self.classify("")["classification"], "blank")

    def test_long_numbered_sentence_is_not_heading(self) -> None:
        text = "1. 这是一个以数字开头但具有完整语义且明显较长的正文句子，不应被盲目识别为标题。"
        self.assertEqual(self.classify(text)["classification"], "body")

    def test_ambiguous_numbered_paragraph_needs_review(self) -> None:
        text = "1. 这是长度处于灰区且没有明确句末标记的模糊编号段落内容"
        result = self.classify(text)
        self.assertEqual(result["classification"], "unknown")
        self.assertEqual(result["classification_source"], "needs_review")

    def test_decisive_title(self) -> None:
        self.assertEqual(self.classify("关于进一步加强管理工作的通知")["classification"], "title")

    def test_ambiguous_first_paragraph_needs_review(self) -> None:
        result = self.classify("工作安排")
        self.assertEqual(result["classification"], "unknown")
        self.assertEqual(result["candidate_type"], "title")


if __name__ == "__main__":
    unittest.main()
